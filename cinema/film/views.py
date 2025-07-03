from django.shortcuts import render
from django.utils import timezone
from random import sample
from datetime import  timedelta
from .models import *
from utenti.models import *
from itertools import islice
from django.views.generic import *
from .utils import *
import re
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from .forms import *
from django.db.models import Avg, Count
from itertools import zip_longest
from cinema.mixin import *  # mixin per staff e moderatore

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
    from .utils import collega_film_immagine  

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
        
        context['distribuzione_voti'] = distribuzione_voti
        context['totale_voti'] = totale_voti

        # --- Load dei COMMENTI dei film e relativa paginazione---
        commenti_list = film.commenti.order_by('-data_commento')  #  related_name="commenti"
        paginator = Paginator(commenti_list, 7)  # 7 commenti per pagina
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['commenti'] = page_obj
        return context


# Utilizza SISTEMA DI RACCOMANDAZIONE quando non ci sono filtri attivi (su tutti i film db)
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

        # Nessun filtro:  Mostro i 12 raccomandati
        if not titolo and not cast and not genere:
            film_raccomandati = get_raccomandazioni_utente(self.request.user,12)
            for f in film_raccomandati:
                f.immagine_genere = collega_film_immagine(f.genere)
            return film_raccomandati

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
class FilmCreateView(StaffRequiredMixin,CreateView):
    model = Film
    form_class = FilmForm
    template_name = 'CRUD/film_form.html'
    success_url = reverse_lazy('film:homepage')  

# CBV per la modifica di un film
# Il form è condiviso con la createView ecco perchè passo al contesto nome_view (per disambiguare i casi)
class FilmUpdateView(StaffRequiredMixin,UpdateView):
    model = Film
    form_class = FilmForm
    template_name = 'CRUD/film_form.html'
    success_url = reverse_lazy('film:homepage')
    #Perchè condivide il template con la ListView (modificaView)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context

# ListView per scegliere il film da modificare (mostrata quando lo staff clicca su "modifica film")
class FilmListModificaView(StaffRequiredMixin,ListView):
    model = Film
    template_name = 'CRUD/film_list_modifica.html'
    context_object_name = 'film_list'
    ordering = ['titolo']  # <-- Ordina alfabeticamente per titolo (A-Z)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context

class FilmDeleteView(StaffRequiredMixin,DeleteView):
    model = Film
    template_name = 'CRUD/confirm_delete.html'
    success_url = reverse_lazy('film:film_list_modifica')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context



#Procedo alla creazione delle 3 view analoghe ai Film per la Creazione/Modifica di Proiezioni
# Analogamente a prima: form personalizzato
class ProiezioneCreateView(StaffRequiredMixin,CreateView):
    model = Proiezione
    form_class = ProiezioneForm
    template_name = 'CRUD/proiezione_form.html'
    success_url = reverse_lazy('film:homepage')

    

# Il form è condiviso con la createView ecco perchè passo al contesto nome_view (per disambiguare i casi)
class ProiezioneUpdateView(StaffRequiredMixin,UpdateView):
    model = Proiezione
    form_class = ProiezioneForm
    template_name = 'CRUD/proiezione_form.html'
    success_url = reverse_lazy('film:homepage')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context


class ProiezioneListModificaView(StaffRequiredMixin,ListView):
    model = Proiezione
    template_name = 'CRUD/proiezione_list_modifica.html'
    context_object_name = 'proiezione_list'
    
    #Ordino per titolo del film
    def get_queryset(self):
        return Proiezione.objects.select_related('film').order_by('film__titolo')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context
    
class ProiezioneDeleteView(StaffRequiredMixin,DeleteView):
    model = Proiezione
    template_name = 'CRUD/confirm_delete.html'
    success_url = reverse_lazy('film:proiezione_list_modifica')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nome_view"] = self.__class__.__name__
        return context



#View per l'opzione "Dove siamo" della navigation bar
def dove_siamo(request):
    return render(request, 'dove_siamo.html')


# View per la sezione statistiche, ottiene:
# Lista di film popolari: [somma normalizzata di valori [0,1] per MediaRating + Rating/TotRating) + commenti/TotCommenti]
# Raggruppamento per 3 tramite IterTools (zipLongest)
def group_film_in_tre(lista):
    """Gruppi di 3 per carousel Bootstrap"""
    return [list(filter(None, gruppo)) for gruppo in zip_longest(*[iter(lista)]*3)]

def statistiche_film(request):
    # Annotazioni base  ,  "Avg,Count" offerti da django
    film_stats = Film.objects.annotate(
        media_rating=Avg('ratings__voto'),
        numero_rating=Count('ratings'),
        numero_commenti=Count('commenti')
    )

    # Totali globali per normalizzazione
    totale_rating = Rating.objects.count() or 1
    totale_commenti = Commento.objects.count() or 1

    # Calcolo film popolari (media ponderata con valori normalizzati [0,1])
    film_popolari = sorted(
        film_stats,
        key=lambda film: (
            ((film.media_rating or 0) / 5) +
            (film.numero_rating / totale_rating) +
            (film.numero_commenti / totale_commenti)
        ),
        reverse=True
    )[:12]              #Prendo i primi 12

    # Top rating medio
    film_rating_alto = film_stats.order_by('-media_rating')[:12]

    # Film con più commenti
    film_commentati = film_stats.order_by('-numero_commenti')[:12]

    # Devo sempre aggiungere il genere ad ogni film
    for film in film_popolari:
        film.immagine_genere = collega_film_immagine(film.genere)
    for film in film_rating_alto:
        film.immagine_genere = collega_film_immagine(film.genere)
    for film in film_commentati:
        film.immagine_genere = collega_film_immagine(film.genere)

    context = {
        'film_popolari': group_film_in_tre(film_popolari),
        'film_rating_alto': group_film_in_tre(film_rating_alto),
        'film_commentati': group_film_in_tre(film_commentati),
    }
    
    return render(request, 'statistiche.html', context)





