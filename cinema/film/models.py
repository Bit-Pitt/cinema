from django.db import models

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
        return f"{self.film.titolo} in {self.sala.nome} il {self.data_ora.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name_plural = "Proiezioni"
        ordering = ["data_ora"]

