from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from django.http import HttpResponse
from .models import ChatRoom, Message

User = get_user_model()


@login_required
def availableUsers(request):
    """Show all users. If logged in, exclude the current user."""
    if request.user.is_authenticated:
        users = User.objects.exclude(id=request.user.id)
    else:
        users = User.objects.all()

    return render(request, "chatRoomDashborad.html", {"users": users})


@login_required
def recent_chats(request):
    user = request.user
    conversations = (
        Message.objects.filter(Q(sender=user) | Q(recipient=user))
        .select_related("sender", "recipient")
        .order_by("-time_stamp")
    )

    chats = []
    seen_users = set()

    for msg in conversations:
        other_user = msg.recipient if msg.sender == user else msg.sender
        if other_user and other_user.id not in seen_users:
            seen_users.add(other_user.id)
            # build sorted room_name
            usernames = sorted([user.username, other_user.username])
            room_name = "_".join(usernames)
            chats.append({
                "message": msg,
                "other_user": other_user,
                "room_name": room_name
            })

    return render(request, "welcome.html", {"chats": chats})

@login_required


def chatRoomView(request, room_name):
    """
    Open a chat room between the logged-in user and another user.
    Room name is deterministic: alphabetically ordered "user1_user2".
    """
    usernames = sorted(room_name.split("_"))
    room_name = "_".join(usernames)

    if request.user.username not in usernames:
        return HttpResponse("You are not part of this conversation.", status=403)
    room, _ = ChatRoom.objects.get_or_create(name=room_name)

    
    try:
        other_username = next(u for u in usernames if u != request.user.username)
    except StopIteration:
        return HttpResponse("Invalid room.", status=400)

    other_user = get_object_or_404(User, username=other_username)

    return render(request, "chatRoom.html", {
        "room": room,
        "other_user": other_user,
    })

