from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from film.models import Proiezione
import json
from .validators import *


# La classe presenta il validatore sempre tramite "clean" e override di "save"
# I posti comperati sono modellati con Json tramite TextField in maniera analoga alle sale
class Prenotazione(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name="prenotazioni")
    proiezione = models.ForeignKey(Proiezione, on_delete=models.CASCADE, related_name="prenotazioni")
    data_acquisto = models.DateTimeField(auto_now_add=True)
    prezzo = models.DecimalField(max_digits=7, decimal_places=2)  # es: max 99999.99
    posti = models.TextField(help_text="Lista JSON di posti, es: [1, 2, 5]")

    def __str__(self):
        return f"Prenotazione di {self.utente.username} per {self.proiezione} acquistata il {self.data_acquisto}"

    def clean(self):
        print("------------Validazione prenotazione")

        # Prezzo > 0
        if self.prezzo <= 0:
            raise ValidationError("Il prezzo deve essere maggiore di zero.")

        # Validazione posti JSON
        try:
            lista_posti = json.loads(self.posti)
        except json.JSONDecodeError:
            raise ValidationError("I posti devono essere una lista JSON valida.")

        if len(lista_posti) < 1:
            raise ValidationError("Deve essere prenotato almeno un posto")
        
        if not isinstance(lista_posti, list):
            raise ValidationError("I posti devono essere una lista.")

        if not all(isinstance(p, int) and p > 0 for p in lista_posti):
            raise ValidationError("Tutti i posti devono essere numeri interi positivi.")
        validate_posti_contigui(lista_posti)
        validate_posti_sala_e_disponibilita(self)
        validate_posti_gold(self)

    def save(self, *args, **kwargs):
        self.full_clean()  # chiama clean() prima di salvare
        super().save(*args, **kwargs)

