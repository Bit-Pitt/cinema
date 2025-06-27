from django.db import models
from django.db import models
from django.contrib.auth.models import User
from film.models import Film  

#E' la tabella collegata ad "user" quella di default di django per ottenere le informazioni
#riguardanti l'utente (se basic/silver/gold) ==> silver al momento della creazione, e un booleano per
# il moderatore  (is_staff è già in User)
class ProfiloUtente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    SCELTE_ABBONAMENTO = [
        ('basic', 'Basic'),
        ('silver', 'Silver'),
        ('gold', 'Gold'),
    ]
    
    abbonamento = models.CharField(
        max_length=10, choices=SCELTE_ABBONAMENTO, default='basic'
    )
    is_moderatore = models.BooleanField(default=False)


#Questa classe (tabella nel db) rappresenta i commenti correlati a un film
class Commento(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='commenti')
    testo = models.TextField(max_length=1000)
    data_commento = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commento di {self.utente.username} su {self.film.titolo}"
