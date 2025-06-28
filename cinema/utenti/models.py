from django.db import models
from django.db import models
from django.contrib.auth.models import User
from film.models import Film  
from django.core.validators import MinValueValidator, MaxValueValidator

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
    #campo charfield ma con un set di valori prestabiliti
    abbonamento = models.CharField(
        max_length=10, choices=SCELTE_ABBONAMENTO, default='basic'
    )
    is_moderatore = models.BooleanField(default=False)


#Questa classe (tabella nel db) rappresenta i commenti correlati a un film
class Commento(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name='commenti')
    testo = models.TextField(max_length=100)
    data_commento = models.DateTimeField()
    
    def __str__(self):
        return f"Commento di {self.utente.username} su {self.film.titolo}"
    

#La classe rappresenta il rating degli utenti dati a un film, impostiamo validatori già nel modello
class Rating(models.Model):
    film = models.ForeignKey(
        Film,
        on_delete=models.CASCADE,
        related_name='ratings'          #  per accedere da film.ratings.all() ... 
    )
    utente = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings'
    )
    voto = models.IntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    def __str__(self):
        return f"{self.utente.username} - {self.film.titolo}: {self.voto}"
    

# FORUM:  2 tabella
# Discussione: contiene i "metadata" di una discussione
# Messaggio: --> si collegano a una discussione
class Discussione(models.Model):
    titolo = models.CharField(max_length=200)
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    data_creazione = models.DateTimeField()        #aggiune in auto la data attuale
    ultimo_messaggio_data = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.titolo
    
class Messaggio(models.Model):
    discussione = models.ForeignKey(Discussione, on_delete=models.CASCADE, related_name='messaggi')
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    contenuto = models.TextField()          #lunghezza dinamica, conveniente quanto potenzialmente ha msg di dimensione molto diversa
    data_invio = models.DateTimeField()

    def __str__(self):
        return f"Messaggio di {self.utente.username} in '{self.discussione.titolo}'"

        #trigger in caso di nuovo messaggio
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # aggiorna solo se questo messaggio è il più recente (per robustezza non diamo per scontato sia il più recente <-- magari da admin aggiunta data non reale)
        if (not self.discussione.ultimo_messaggio_data) or (self.data_invio > self.discussione.ultimo_messaggio_data):
            self.discussione.ultimo_messaggio_data = self.data_invio
            self.discussione.save()



