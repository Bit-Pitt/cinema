from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import ChatMessage
from django.contrib.auth.models import User

# Chat room per l'utente client
@login_required
def user_chat(request):
    return render(request, "chat_room.html", {
        "username": request.user.username,
        "room_name": request.user.username,
    })


# Lo staff da questa pagina visualizza le chat di assistenza live aperte
@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_dashboard(request):
    user_ids = ChatMessage.objects.values_list('sender', flat=True).distinct()
    users = User.objects.filter(id__in=user_ids,is_staff=False)
    return render(request, "staff_dashboard.html", {"users": users})

# Da qui accede alla chat di un utente
@login_required
@user_passes_test(lambda u: u.is_staff)
def staff_chat_with_user(request):
    room = request.GET.get("room")
    try:
        target_user = User.objects.get(username=room)
    except User.DoesNotExist:
        return render(request, "chat_room.html", {
            "room_name": "invalid",
            "username": request.user.username,
            "error": "Utente non trovato"
        })

    return render(request, "chat_room.html", {
        "room_name": room,  
        "username": request.user.username  
    })





