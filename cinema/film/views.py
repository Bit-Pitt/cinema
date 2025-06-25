from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
from random import sample
from datetime import datetime, timedelta
from .models import Film
from itertools import islice
from django.views.generic.detail import *
from .utils import *


#Divide a gruppi di 3 i film, per poterli renderare a gruppi nel DTL
def chunked(iterable, n):
    iterable = iter(iterable)
    return iter(lambda: list(islice(iterable, n)), [])

def tmp(request):
    template = "tmp.html"
    l = [i for i in range(4)]
    ctx = { 'title' : "ESEMPIO!" , "list": l}
    return HttpResponse("Ciao")
    return render(request,template_name=template,context=ctx)

''' Aggiungi link dinamici ai film / Attori di un film!! (questo nel template )
<a href="https://it.wikipedia.org/w/index.php?search={{ film.titolo|urlencode }}" target="_blank" rel="noopener noreferrer">
    Cerca su Wikipedia
</a>
'''


def home(request):
    template = "home.html"    
    oggi = timezone.now()
    settimana_prossima = oggi + timedelta(days=7)

    # ----------------------- ESTENDI ------------------  
    # i top 3 film in evidenza saranno quelli che hanno più commenti e rating >>>
    film_con_proiezioni = Film.objects.filter(
        proiezioni__isnull=False                #grazie a related_name è semplicemente così
    ).distinct()

    film_in_evidenza = sample(list(film_con_proiezioni), min(3, len(film_con_proiezioni)))

    # Film in uscita (con proiezioni nella settimana prossima)
    film_settimana_prossima = Film.objects.filter(
        proiezioni__data_ora__range=(settimana_prossima, settimana_prossima + timedelta(days=7))
    ).distinct()

    #film_in_uscita = sample(list(film_settimana_prossima), min(3, len(film_settimana_prossima)))
    #crei una lista di oggetti "film"
    film_in_uscita = list(film_settimana_prossima)  
    film_in_uscita = list(chunked(film_in_uscita, 3))  

      # Importa la funzione
    from .utils import collega_film_immagine  # supponendo che la funzione sia in utils.py

    # Aggiungi l'attributo immagine_genere (dinamico non persistente) per ogni film
    for film in film_in_evidenza:
        film.immagine_genere = collega_film_immagine(film.genere)

    for chunk in film_in_uscita:        #bisogna iterare per ogni tripla (chunk)
        for film in chunk:
            film.immagine_genere = collega_film_immagine(film.genere)

    return render(request, template_name=template, context={
        "film_in_evidenza": film_in_evidenza,
        "film_in_uscita": film_in_uscita,
    })



class DetailFilmView(DetailView):
    model = Film
    template_name = "detail_film.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        immagine = collega_film_immagine(self.object.genere.lower())    
        context["immagine_genere"] = immagine
        return context



