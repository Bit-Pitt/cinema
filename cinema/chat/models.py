from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta


class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # destinatario
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Da {self.sender} a {self.user}: {self.message}"


# Questo metodo deve essere  chiamato ogni tot tempo per cancellare le chat vecchie, l'utente può essere sia "user" 
# che "sender" per cui si raggruppa per ogni utenti i messaggi che riguardano lui, si prende il più recente e 
# se più vecchio di 2h fa si cancella la chat ==> così per lo staff saranno visibili solo le chat rimanenti
def cleanup_old_chats():
    threshold = timezone.now() - timedelta(hours=2)
    non_staff_users = User.objects.filter(is_staff=False)

    for user in non_staff_users:
        # Trova l'ultimo messaggio inviato dallo user
        last_user_msg = ChatMessage.objects.filter(sender=user).order_by('-timestamp').first()

        if not last_user_msg or last_user_msg.timestamp < threshold:
            # Cancella tutti i messaggi collegati a questo utente (come sender o destinatario)
            ChatMessage.objects.filter(sender=user).delete()
            ChatMessage.objects.filter(user=user).delete()
            print(f"Chat cancellata per {user.username}")
