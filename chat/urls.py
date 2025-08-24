from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.availableUsers, name='show_users'),
    path('room/<str:room_name>/', views.chatRoomView, name='chat_room'),
    path('home/', views.recent_chats, name='home'),
]
