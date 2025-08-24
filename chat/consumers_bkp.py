import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from chat.models import Message, ChatRoom

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send saved messages after accepting connection
        saved_messages = await self.get_saved_messages(self.room_name)
        await self.send(text_data=json.dumps({
            'type': 'history',
            'messages': saved_messages
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data.get('message', '')
            recipient_username = data.get('recipient', None)

            sender_user = self.scope['user']

            if not message:
                return  # Ignore empty messages

            # Save message to DB (async-safe)
            recipient_user = None
            if recipient_username:
                recipient_user = await self.get_user(recipient_username)

            await self.save_message(sender_user, recipient_user, message)

            # Group message
            if not recipient_username:
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender': sender_user.username,
                        'recipient': None
                    }
                )
            else:
                # Direct/private message
                if recipient_user:
                    recipient_channel = f'user_{recipient_user.username}'

                    # Send to recipient's personal group
                    await self.channel_layer.group_send(
                        recipient_channel,
                        {
                            'type': 'chat_message',
                            'message': message,
                            'sender': sender_user.username,
                            'recipient': recipient_user.username
                        }
                    )
                    # Echo to sender too
                    await self.send(text_data=json.dumps({
                        'message': message,
                        'sender': sender_user.username,
                        'recipient': recipient_user.username
                    }))

        except Exception as e:
            print("WebSocket receive error:", str(e))
            await self.close()

    async def chat_message(self, event):
        message = event['message']
        sender = event['sender']
        recipient = event.get('recipient', None)

        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'recipient': recipient
        }))

    @database_sync_to_async
    def get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @database_sync_to_async
    def get_conversation(self, room_name):
        return Conversation.objects.get(id=room_name)  # assuming room_name is ID

    @database_sync_to_async
    def get_saved_messages(self, room_name):
        try:
            conversation = ChatRoom.objects.get(name=room_name)
            messages = Message.objects.filter(conversation=conversation).order_by('time_stamp')
            return [
                    {'sender': msg.sender.username, 'content': msg.message, 'timestamp': msg.time_stamp.strftime('%Y-%m-%d %H:%M:%S')}
                for msg in messages
                ]
        except ChatRoom.DoesNotExist:
                return []

    @database_sync_to_async
    def save_message(self, sender, recipient, message):
        Message.objects.create(
            sender=sender,
            recipient=recipient,
            message=message
        )

    
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
