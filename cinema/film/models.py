from django.db import models
from django.core.exceptions import ValidationError
from datetime import  timedelta
from django.utils.timezone import now
import json


# Create your models here.

class Film(models.Model):
    titolo = models.CharField(max_length=200)
    trama = models.TextField()
    cast = models.TextField()
    durata = models.PositiveIntegerField(help_text="Durata in minuti")
    genere = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.titolo} ({self.genere})"

    class Meta:
        verbose_name_plural = "Film"

# Validazione che numero_posti e posti_per_fila sia coerente, e che posti_per_fila rispetti formato JSON
# posti_per_fila è nel db un textField --> si usa Json per ottenere la lista di numeri
class Sala(models.Model):
    nome = models.CharField(max_length=20)
    numero_posti = models.PositiveIntegerField()
    # Campo JSON come stringa per salvare la lista dei posti per fila
    posti_per_fila_lista = models.TextField(help_text="Esempio: [10, 10, 10, 15, 15, 15]")

    def __str__(self):
        return f"Sala {self.nome} - {self.numero_posti} posti"

    class Meta:
        verbose_name_plural = "Sale"

    #Chiamato in automatico perchè fatto override di "save()"
    def clean(self):
        print("----Validazione sala")
        try:
            lista_posti = json.loads(self.posti_per_fila_lista)
        except json.JSONDecodeError:
            raise ValidationError("La lista dei posti per fila deve essere una lista valida in formato JSON, ad esempio: [10, 12, 14]")

        # controlloche tutti gli elementi siano numeri interi positivi
        if not all(isinstance(x, int) and x > 0 for x in lista_posti):
            raise ValidationError("Tutti gli elementi della lista devono essere numeri interi positivi.")

        somma_posti = sum(lista_posti)

        if somma_posti != self.numero_posti:
            raise ValidationError(f"Il numero totale dei posti ({self.numero_posti}) deve essere uguale alla somma della lista ({somma_posti}).")
        
    #Così da poter ottenere direttamente la lista
    def get_lista_posti(self):
        try:
            return json.loads(self.posti_per_fila_lista)
        except json.JSONDecodeError:
            return []
    
    def save(self, *args, **kwargs):
        self.clean()  # chiamata esplicita della validazione
        super().save(*args, **kwargs)




# Definizione del metodo clean per una validazione lato Model
class Proiezione(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name="proiezioni")
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="proiezioni")
    data_ora = models.DateTimeField()

    def __str__(self):
        return f"{self.film.titolo} in {self.sala.nome} il {self.data_ora}"

    class Meta:
        verbose_name_plural = "Proiezioni"
        ordering = ["data_ora"]

    #VALIDAZIONE:   (automatica perchè override di save())
    # Non posso aggiungere una proiezione nel passato / futuro > 2 settimane
    # - non posso aggiungere una proiezione in una sala occupata
    def clean(self):
        print("-----------------Validazione della proiezione")
        ora_attuale = now()
        # Blocco: impedisce date nel passato  (commentato per inizializzare il db con proiezioni passate)
        #if self.data_ora < ora_attuale:
        #    raise ValidationError("Non puoi creare o modificare una proiezione con una data/ora nel passato.")
        if self.data_ora > ora_attuale + timedelta(weeks=2):
            raise ValidationError("Non puoi creare una proiezione oltre due settimane nel futuro.")

        fine_proiezione = self.data_ora + timedelta(minutes=self.film.durata)

        # Prende tutte le proiezioni nella stessa sala, escludendo se stessa (in caso di update)
        proiezioni_sovrapposte = Proiezione.objects.filter(
            sala=self.sala
        ).exclude(id=self.id).select_related("film")

        for p in proiezioni_sovrapposte:
            inizio_esistente = p.data_ora
            fine_esistente = p.data_ora + timedelta(minutes=p.film.durata)

            #non c'è sovrapposizione solo se una proiezione finisce prima dell'inizio dell'altra o inizia dopo la fine dell'altra.
            if not (fine_proiezione <= inizio_esistente or self.data_ora >= fine_esistente):
                raise ValidationError(
                    f"Conflitto: esiste già una proiezione di '{p.film.titolo}' in sala {self.sala.nome} "
                    f"dalle {inizio_esistente.strftime('%H:%M')} alle {fine_esistente.strftime('%H:%M')}"
                    f" La proiezione che si voleva aggiungere:{self}"
                )
            
    def save(self, *args, **kwargs):
        self.full_clean()  # chiama clean() prima di salvare
        super().save(*args, **kwargs)

