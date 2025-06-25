from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


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

class Sala(models.Model):
    nome = models.CharField(max_length=20)
    numero_posti = models.PositiveIntegerField()
    file = models.PositiveIntegerField(help_text="Numero di file")
    posti_per_fila = models.PositiveIntegerField()

    def __str__(self):
        return f"Sala {self.nome} - {self.numero_posti} posti"

    class Meta:
        verbose_name_plural = "Sale"

class Proiezione(models.Model):
    film = models.ForeignKey(Film, on_delete=models.CASCADE, related_name="proiezioni")
    sala = models.ForeignKey(Sala, on_delete=models.CASCADE, related_name="proiezioni")
    data_ora = models.DateTimeField()

    def __str__(self):
        return f"{self.film.titolo} in {self.sala.nome} il {self.data_ora}"

    class Meta:
        verbose_name_plural = "Proiezioni"
        ordering = ["data_ora"]

    #VALIDAZIONE: non posso aggiungere una proiezione in una sala occupata
    def clean(self):
        print("-----------------Validazione")
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
                    f"La proiezione che si voleva aggiungere:{self}"
                )
            
    def save(self, *args, **kwargs):
        self.full_clean()  # chiama clean() prima di salvare
        super().save(*args, **kwargs)

