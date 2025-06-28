from django.shortcuts import render
from django.utils import timezone
from random import sample
from datetime import  timedelta
from .models import *
from utenti.models import Rating
from itertools import islice
from django.views.generic import *
from .utils import *
import re
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from .forms import *

# rimuove spazi multipli che non porterebbero a dei match
def normalizza_spazi(s):
    return re.sub(r'\s+', ' ', s).strip()


#Divide a gruppi di 3 i film, per poterli renderare a gruppi nel DTL
def chunked(iterable, n):
    iterable = iter(iterable)
    return iter(lambda: list(islice(iterable, n)), [])


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


# Questa DetailView mostra le informazioni riguardanti un determinato film
# "collega_film_immagine" per inserire dinamicamente lo static file associato al film
# La view ottiene inoltre i film di questa settimana per mostrare solo per loro il btn "prenota"
# Calcola anche la media dei rating (1-5) per mostrare il grafico
class DetailFilmView(DetailView):
    model = Film
    template_name = "detail_film.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        film = self.object

        # Immagine per il genere
        context["immagine_genere"] = collega_film_immagine(film.genere.lower())

        # Verifica proiezioni nella settimana corrente
        oggi = timezone.now().date()
        fine_settimana = oggi + timedelta(days=7)
        context['proiezione_questa_settimana'] = Proiezione.objects.filter(
            film=film,
            data_ora__date__gte=oggi,
            data_ora__date__lte=fine_settimana
        ).exists()

        # === Calcolo distribuzione voti (da 1 a 5) === (per mostrare i rating)
        voti_raw = film.ratings.values_list('voto', flat=True)  # related_name usato qui
        conteggio_voti = {i: 0 for i in range(1, 6)}
        for voto in voti_raw:
            if voto in conteggio_voti:
                conteggio_voti[voto] += 1

        totale_voti = sum(conteggio_voti.values())
        distribuzione_voti = []
        for voto, count in conteggio_voti.items():
            percentuale = (count / totale_voti * 100) if totale_voti > 0 else 0
            distribuzione_voti.append({
                'voto': voto,
                'conteggio': count,
                'percentuale': round(percentuale, 1)
            })
        print(distribuzione_voti)
        context['distribuzione_voti'] = distribuzione_voti
        context['totale_voti'] = totale_voti

        # --- Load dei COMMENTI dei film e relativa paginazione---
        commenti_list = film.commenti.order_by('-data_commento')  #  related_name="commenti"
        paginator = Paginator(commenti_list, 7)  # 7 commenti per pagina
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['commenti'] = page_obj
        return context


    
# Implementa la funzione "Cerca Film" nella home page
# Se ci si arriva per la prima volta mostra i raccomandati, altrimenti esegue le query
class CercaFilmView(ListView):
    model = Film
    template_name = "cerca_film.html"
    context_object_name = "film_list"
    paginate_by = 6            #mi da la possibilità di implementare facilmente l'impaginazione

    def get_queryset(self):
        titolo = normalizza_spazi(self.request.GET.get("titolo", "").strip())
        cast = normalizza_spazi(self.request.GET.get("cast", "").strip())
        genere = normalizza_spazi(self.request.GET.get("genere", "").strip())

        # Nessun filtro:  (per ora 10 casuali)
        if not titolo and not cast and not genere:
            all_ids = list(Film.objects.values_list("id", flat=True))
            random_ids = sample(all_ids, min(10, len(all_ids)))
            film_casuali = Film.objects.filter(id__in=random_ids)
            for f in film_casuali:
                f.immagine_genere = collega_film_immagine(f.genere)
            return film_casuali

        # Se qui allora ci sono dei parametri di ricerca
        queryset = Film.objects.all()

        if titolo:
            queryset = queryset.filter(titolo__icontains=titolo)
        if cast:
            queryset = queryset.filter(cast__icontains=cast)
        if genere:
            queryset = queryset.filter(genere__icontains=genere)


        risultati = queryset.distinct()

        for f in risultati:
            f.immagine_genere = collega_film_immagine(f.genere)

        return risultati
    
from django.http import JsonResponse

#Uso jsons response al posto di "HttpResponse" per agevolare operazioni più complesse
def autocomplete(request):
    w = request.GET.get("w")  # Primo parametro per:titolo, cast, genere
    q = request.GET.get("q")  # stringa di ricerca

    if w not in ["titolo", "genere"] or not q or len(q) < 3:
        return JsonResponse({"results": []})        #vuoto se non rispetta i requisiti

    #filtro così per i__contains sul campo "w", prendo al max 5
    results = list(Film.objects
        .filter(**{f"{w}__icontains": q})       #**per espandere il dizionario es: filter(titolo__icontains=Inception)
        .values_list(w, flat=True)              #lista solamente il titolo/cast/genere
        .distinct()[:5]
    )
    return JsonResponse({"results": results})


# View per creare un film
class FilmCreateView(CreateView):
    model = Film
    form_class = FilmForm
    template_name = 'film_form.html'
    success_url = reverse_lazy('film:homepage')  

# CBV per la modifica di un film
class FilmUpdateView(UpdateView):
    model = Film
    form_class = FilmForm
    template_name = 'film_form.html'
    success_url = reverse_lazy('film:homepage')

    #Perchè condivide il template con la ListView (modificaView)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context

# ListView per scegliere il film da modificare
class FilmListModificaView(ListView):
    model = Film
    template_name = 'film_list_modifica.html'
    context_object_name = 'film_list'
    ordering = ['titolo']  # <-- Ordina alfabeticamente per titolo (A-Z)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context





