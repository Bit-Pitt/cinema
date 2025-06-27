from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import ProfiloUtente

#Dopo il salvataggio di un nuovo user ==> viene invocata questa funzione (crea la entry in ProfiloUtente correlata)
@receiver(post_save, sender=User)
def crea_profilo(sender, instance, created, **kwargs):
    if created:
        ProfiloUtente.objects.create(user=instance)
