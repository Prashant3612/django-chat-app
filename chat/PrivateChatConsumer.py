# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, ChatRoom
from django.contrib.auth import get_user_model

User = get_user_model()

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.other_user_username = self.scope['url_route']['kwargs']['username']  # person you're chatting with
        self.current_user = self.scope['user']

        # Create a unique conversation identifier
        self.room_name = self.get_room_name(self.current_user.username, self.other_user_username)
        self.room_group_name = f"private_chat_{self.room_name}"

        # Join the group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send old messages
        old_messages = await self.get_saved_messages(self.current_user, self.other_user_username)
        await self.send(text_data=json.dumps({
            "type": "history",
            "messages": old_messages
        }))

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data["message"]

        # Save message
        await self.save_message(self.current_user, self.other_user_username, message)

        # Send to both users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "sender": self.current_user.username,
                "message": message
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "sender": event["sender"],
            "message": event["message"]
        }))

    @database_sync_to_async
    def get_saved_messages(self, user1, user2_username):
        try:
            user2 = User.objects.get(username=user2_username)
        except User.DoesNotExist:
            return []

        room = self.get_or_create_room(user1, user2)
        messages = Message.objects.filter(conversation=room).order_by("time_stamp")
        return [
            {"sender": msg.sender.username, "content": msg.message}
            for msg in messages
        ]

    @database_sync_to_async
    def save_message(self, sender, recipient_username, content):
        recipient = User.objects.get(username=recipient_username)
        room = self.get_or_create_room(sender, recipient)
        Message.objects.create(sender=sender, recipient=recipient, conversation=room, message=content)

    def get_room_name(self, user1, user2):
        """Generate unique name for private chat room"""
        return "_".join(sorted([user1, user2]))

    def get_or_create_room(self, user1, user2):
        """Fetch or create ChatRoom for the two users"""
        name = self.get_room_name(user1.username, user2.username)
        room, _ = ChatRoom.objects.get_or_create(name=name)
        return room
