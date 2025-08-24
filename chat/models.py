from django.db import models
from django.conf import settings  
from django.contrib.auth.models import User


# Create your models here.

class ChatRoom(models.Model):
  name=models.CharField(max_length=200)
  participants=models.ManyToManyField(settings.AUTH_USER_MODEL)
  created=models.DateTimeField(auto_now_add=True)
  last_active=models.DateTimeField(auto_now=True)

class Message(models.Model):
  sender=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE, related_name='sent_messages')
  recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages', null=True, blank=True)
  conversation=models.ForeignKey(ChatRoom, on_delete=models.CASCADE,null=True,blank=True)
  message=models.TextField()
  time_stamp=models.DateTimeField(auto_now_add=True)
  is_read=models.BooleanField(default=False)


# class ChatUser(model.Model):

