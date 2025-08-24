# from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Add custom fields if needed
  #It will inherit all the feilds like name,email, etc. from the parent class user
    # avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    status_message = models.CharField(max_length=255, default="Hey there! I’m using ChatApp")

    def __str__(self):
        return self.username

