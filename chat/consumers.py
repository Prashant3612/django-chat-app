import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Message, ChatRoom
from datetime import datetime

User = get_user_model()

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_username = self.scope['url_route']['kwargs']['username']
        self.current_user = self.scope['user']

        # Create unique private room name
        self.room_name = self.get_room_name(self.current_user.username, self.other_username)
        self.room_group_name = f"private_chat_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # Send old private messages
        old_messages = await self.get_saved_messages(self.current_user.username, self.other_username)
        await self.send(text_data=json.dumps({
            "type": "history",
            "messages": old_messages
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        """Handle new message from WebSocket."""
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return  # ignore invalid JSON

        message = data.get("message", "").strip()
        if not message:
            return

        # Save message
        await self.save_message(self.current_user.username, self.other_username, message)

        # Broadcast message with timestamp
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "sender": self.current_user.username,
                "message": message,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

    async def chat_message(self, event):
        """Send message to WebSocket."""
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"],
            "timestamp": event.get("timestamp")
        }))

    @database_sync_to_async
    def get_saved_messages(self, user1_username, user2_username):
        """Load chat history between 2 users."""
        try:
            user1 = User.objects.get(username=user1_username)
            user2 = User.objects.get(username=user2_username)
        except User.DoesNotExist:
            return []

        room = self.get_or_create_room(user1, user2)
        messages = Message.objects.filter(conversation=room).order_by("time_stamp")
        return [
            {
                "sender": m.sender.username,
                "content": m.message,
                "timestamp": m.time_stamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            for m in messages
        ]

    @database_sync_to_async
    def save_message(self, sender_username, recipient_username, content):
        sender = User.objects.get(username=sender_username)
        recipient = User.objects.get(username=recipient_username)
        room = self.get_or_create_room(sender, recipient)
        Message.objects.create(sender=sender, recipient=recipient, conversation=room, message=content)

    def get_room_name(self, u1, u2):
        """Deterministic name so both users join same room."""
        return "_".join(sorted([u1, u2]))

    def get_or_create_room(self, user1, user2):
        name = self.get_room_name(user1.username, user2.username)
        room, _ = ChatRoom.objects.get_or_create(name=name)
        return room
