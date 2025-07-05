from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import *
from .forms import * 
from django.db.models import Count
from .models import *
from prenotazioni.models import Prenotazione
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import timedelta , date
from django.utils.timezone import now
import json
from film.utils import collega_film_immagine  
from film.utils import get_raccomandazioni_utente
from django.contrib.auth.mixins import LoginRequiredMixin
from cinema.mixin import *      #Miei mixin




# La classe sfrutta la "createView" cbv a cui associa il form in automatico, così come il template grazie a Django users
class UserCreateView(CreateView):
    form_class = CreaUtente
    template_name = "registration/signup.html"
    success_url = reverse_lazy("utenti:login")


#List view di entrata al "Forum" mostra le discussioni, potenzialmente con ordinamenti scelti da utente
#Di default l'ordinamento sarà data creazione
class ListaDiscussioniView(ListView):
    model = Discussione
    template_name = 'forum/lista_discussioni.html'
    context_object_name = 'discussioni'
    paginate_by = 8                 #offerto dalla CBV

    def get_queryset(self):
        queryset = Discussione.objects.all()
                                        #di deafault prende "data_creazione" e ordina per quello
        ordina = self.request.GET.get('ordina', 'data_creazione')
        if ordina == 'num_messaggi':
            queryset = queryset.annotate(num=Count('messaggi')).order_by('-num')        #sfruttando "related_name=messaggi"
        else:
            queryset = queryset.order_by(f'-{ordina}')                      #"-"per i più recenti in alto

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ordinamento'] = self.request.GET.get('ordina', 'data_creazione')
        return context

# Detail view per una singola discussione
#overridando get_context_data serve un paginator manuale
# La detailView aggiunge al contesto il form per la creazione di un messaggio, se utente autenticato!
class DettaglioDiscussioneView(DetailView):
    model = Discussione
    template_name = 'forum/dettaglio_discussione.html'
    context_object_name = 'discussione'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        messaggi_list = self.object.messaggi.order_by('-data_invio')
        
        paginator = Paginator(messaggi_list, self.paginate_by)
        page_number = self.request.GET.get('page')
        messaggi_paginati = paginator.get_page(page_number)

        context['messaggi'] = messaggi_paginati

        # Aggiungo il form solo se l'utente è autenticato
        if self.request.user.is_authenticated:
            context['form'] = MessaggioForm()

        return context

    
# CBV per la creazione di una discussione, il form verrà creato in automatico e crispizzato nel template
class CreaDiscussioneView(LoginRequiredMixin,CreateView):
    model = Discussione
    form_class = DiscussioneForm
    template_name = 'forum/crea_discussione.html'
    success_url = reverse_lazy('utenti:lista_discussioni')
    login_url = 'utenti:login'  # URL a cui redirezionare se non loggato


     #inserisco oltre al field catturato dal form l'utente e la data_creazione
    def form_valid(self, form):
        form.instance.utente = self.request.user  # assegna l'utente loggato come autore
        form.instance.data_creazione = timezone.now()      
        messages.success(self.request, "Discussione creata con successo!")      #per gestire il messaggio di successo
        return super().form_valid(form)

#La view si occupa di gestire l'inserimento di un nuovo messaggio,tramite form definito in forms.py  
# La view è pensata per essere contattata tramite post dal form che si trova in "dettaglio_discussione.html"
@login_required
def aggiungi_messaggio(request, pk):
    discussione = get_object_or_404(Discussione, pk=pk)
    if request.method == 'POST':
        form = MessaggioForm(request.POST)
        if form.is_valid():
            messaggio = form.save(commit=False)
            messaggio.discussione = discussione
            messaggio.utente = request.user
            messaggio.data_invio = timezone.now()
            messaggio.save()

            messages.success(request, "Messaggio inviato con successo.")
            return redirect('utenti:dettaglio_discussione', pk=pk)
    else:
        form = MessaggioForm()
    return redirect('utenti:dettaglio_discussione', pk=pk)


# La view permette di craeare un commento ad un film, aggiunge in automatico film,utente,ora
class CommentoCreateView(LoginRequiredMixin,CreateView):
    model = Commento
    form_class = CommentoForm
    template_name = 'commenta.html'
    login_url = 'utenti:login'  # URL a cui redirezionare se non loggato
    

    def form_valid(self, form):
        form.instance.utente = self.request.user
        film_pk = self.kwargs.get('pk')
        form.instance.film = Film.objects.get(pk=film_pk)
        form.instance.data_commento = timezone.now()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        film_pk = self.kwargs.get('pk')
        context['film'] = Film.objects.get(pk=film_pk)
        return context

    def get_success_url(self):
        return reverse_lazy('film:film', kwargs={'pk': self.kwargs.get('pk')})
    

# CBV per la creazione di un rate, evitando che un utente dia due rate allo stesso film 
class RatingCreateView(LoginRequiredMixin,CreateView):
    model = Rating
    form_class = RatingForm
    template_name = 'rating.html'
    login_url = 'utenti:login'  # URL a cui redirezionare se non loggato

    # Se utente già valutato il film non permette una rivalutazione
    def dispatch(self, request, *args, **kwargs):
        film = Film.objects.get(pk=self.kwargs['pk'])
        utente = request.user
        if Rating.objects.filter(film=film, utente=utente).exists():
            messages.warning(request, "Hai già valutato questo film.")
            return redirect('film:film', pk=film.pk)
        return super().dispatch(request, *args, **kwargs)

    #Aggiungo in automatico utente e film al rating
    def form_valid(self, form):
        form.instance.utente = self.request.user
        form.instance.film = Film.objects.get(pk=self.kwargs['pk'])
        messages.success(self.request, "Valutazione salvata con successo!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['film'] = Film.objects.get(pk=self.kwargs['pk'])
        return context

    def get_success_url(self):
        return reverse_lazy('film:film', kwargs={'pk': self.kwargs['pk']})



# Adesso la logica per gestire l'abbonamento
CODICI_SILVER = {"codsilver1", "silver2025"}
CODICI_GOLD = {"codgold1", "goldaccess2025"}

@login_required
def abbonati_view(request):
    profilo, _ = ProfiloUtente.objects.get_or_create(user=request.user)
    return render(request, 'abbonati.html', {"profilo": profilo})

# La view gestisce la logica di abbonamento
# Un utente loggato può abbonarsi silver o gold tramite codice
# Un utente silver solo gold tramite codice
@login_required
def attiva_abbonamento(request):
    if request.method == "POST":
        codice = request.POST.get("codice", "").strip().lower()
        tipo = request.POST.get("tipo")  # 'silver' o 'gold'
        profilo, _ = ProfiloUtente.objects.get_or_create(user=request.user)

        oggi = date.today()

        # Blocca se già Gold attivo
        if profilo.abbonamento == "gold":
            return redirect("utenti:abbonati")

        # Blocca se vuole riattivare Silver quando già attivo
        if tipo == "silver" and profilo.abbonamento == "silver":
            return redirect("utenti:abbonati")

        # Controlla codice valido
        if (tipo == "silver" and codice in CODICI_SILVER) or (tipo == "gold" and codice in CODICI_GOLD):
            profilo.abbonamento = tipo
            profilo.scadenza_abbonamento = oggi + timedelta(days=30)
            profilo.save()

        return redirect("utenti:abbonati")


#Per creare utente con abbonamento scaduto
'''
py -m  manage shell
from django.contrib.auth.models import User
from film.models import ProfiloUtente
from datetime import date, timedelta
user = User.objects.get(username='utente1')
profilo = ProfiloUtente.objects.get(user=user)
profilo.abbonamento = 'silver'
profilo.scadenza_abbonamento = date.today() - timedelta(days=5)  # 5 giorni fa
profilo.save()
'''
#La funzione andrebbe lanciata 1 volta ogni giorno  (attualmente lanciata ogni volta che runserver)
def disattiva_abbonamenti():
    oggi = date.today()
    utenti_scaduti = ProfiloUtente.objects.filter(
            scadenza_abbonamento__lt=oggi
        ).exclude(abbonamento='basic')

    for profilo in utenti_scaduti:
        profilo.abbonamento = 'basic'
        profilo.scadenza_abbonamento = None
        profilo.save()
        print(f"Abbonamento scaduto per: {profilo.user.username}")


# Adesso funzioni per i Moderatori  


#Per moderare commenti sui film:        [Uso il mixin creato in cinema/mixin.py]
# ListView per scegliere i film
# ListView per scegliere il commento da eliminare e deleteview per eliminarlo

# View per selezionare un film
class FilmModerazioneListView(ModeratoreRequiredMixin,ListView):
    model = Film
    template_name = 'moderazione/seleziona_film.html'
    context_object_name = 'film_list'
    ordering = ['titolo']


# Lista dei commenti per un film
class CommentiPerFilmListView(ModeratoreRequiredMixin,ListView):
    model = Commento
    template_name = 'moderazione/commenti_per_film.html'
    context_object_name = 'commenti'

    def get_queryset(self):
        self.film = get_object_or_404(Film, pk=self.kwargs['film_id'])
        return Commento.objects.filter(film=self.film).order_by('utente__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['film'] = self.film
        return context

# DeleteView per commento
class CommentoDeleteView(ModeratoreRequiredMixin,DeleteView):
    model = Commento
    template_name = 'moderazione/commento_confirm_delete.html'
    def get_success_url(self):
        film_id = self.object.film.id
        return reverse_lazy('utenti:commenti_per_film', kwargs={'film_id': film_id})


# Altre opzioni per il moderatore
# Ora le view per Eliminare una discussione (ListView+DeleteView)
# e per eliminare un msg (ListView+Deleteview) <-- listView dei msg ci si arriva dalla listView delle discussioni

# Lista discussioni (moderazione)
class DiscussioneListView(ModeratoreRequiredMixin,ListView):
    model = Discussione
    template_name = 'moderazione/discussione_list_mod.html'
    context_object_name = 'discussioni'
    ordering = ['titolo']

# Visualizza messaggi per una discussione
class MessaggiPerDiscussioneView(ModeratoreRequiredMixin,ListView):
    model = Messaggio
    template_name = 'moderazione/messaggi_per_discussione.html'
    context_object_name = 'messaggi'

    def get_queryset(self):
        return Messaggio.objects.filter(discussione_id=self.kwargs['pk']).order_by('data_invio')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['discussione'] = Discussione.objects.get(pk=self.kwargs['pk'])
        return context

# DeleteView discussione
class DiscussioneDeleteView(ModeratoreRequiredMixin,DeleteView):
    model = Discussione
    template_name = 'moderazione/discussione_confirm_delete.html'
    success_url = reverse_lazy('utenti:lista_discussioni_mod')

# DeleteView messaggio
class MessaggioDeleteView(ModeratoreRequiredMixin,DeleteView):
    model = Messaggio
    template_name = 'moderazione/messaggio_confirm_delete.html'

    def get_success_url(self):
        return reverse_lazy('utenti:messaggi_per_discussione', kwargs={'pk': self.object.discussione.pk})

#trasforma i posti da numeri 1-nPosti in "human readable" ovvero  tipo "C2" posto 2 fila 3.
# Per questo serve il layout della sala
def posti_human_readable(posti_list, sala):
    """
    posti_list: lista di interi, es [12, 13, 14]
    sala: oggetto Sala che ha il metodo get_lista_posti() che ritorna [10,10,15]
    ritorna lista di stringhe tipo ['B2', 'B3', 'B4']
    """
    layout = sala.get_lista_posti()  # es [10, 10, 15]

    lettere_fila = "ABCDEFGHIJ"

    risultati = []

    for posto in posti_list:
        # cerco in quale fila si trova il posto
        somma = 0
        fila_idx = -1
        for i, num_posti in enumerate(layout):
            somma += num_posti
            if posto <= somma:
                fila_idx = i
                break
        
        # calcolo indice posto nella fila (da 1)
        # somma contiene numero massimo posto in quella fila
        # posizione_in_fila = posto - (somma - num_posti_fila)
        #se layout [10,10,15] e posto è il 12 :   12 - (20-10) = 2
        pos_in_fila = posto - (somma - layout[fila_idx])
        
        # etichetta fila (A, B, C ...)
        fila_lettera = lettere_fila[fila_idx]
        risultati.append(f"{fila_lettera}{pos_in_fila}")
    
    return risultati



# View che mostra il profilo, TemplateView è una semplice CBV
# passa al contesto:    prenotazioni future dell'utente
#                       film raccomandati
#                       film visti dall'utente
#                       film ora al cinema
class ProfiloView(LoginRequiredMixin,TemplateView):
    template_name = 'profilo.html'
    #Divide la lista di oggetti in pezzi "chunck" così che il carosello li mostri 3 alla volta
    def chunk_list(self, lst, n):
        return [lst[i:i + n] for i in range(0, len(lst), n)]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        utente = self.request.user
        oggi = now()

        # 1. Prenotazioni future ordinate dalla più vicina
        fine_settimana = oggi + timedelta(days=8)
        prenotazioni_settimana = Prenotazione.objects.filter(
            utente=utente,
            proiezione__data_ora__range=(oggi, fine_settimana)
        ).select_related('proiezione__film').order_by('proiezione__data_ora')

        for p in prenotazioni_settimana:
            try:
                lista_posti = json.loads(p.posti)
                p.posti_presi = posti_human_readable(lista_posti, p.proiezione.sala)
            except Exception:
                p.posti_presi = []      #Non dovrebbe mai accadere (db corrotto)

        # 2. La funzione in Utils (app film) rappresenta il sistema di raccomandazione
        film_raccomandati = get_raccomandazioni_utente(self.request.user,ora_al_cinema=True)
        for film in film_raccomandati:
            film.immagine_genere = collega_film_immagine(film.genere)

        # 3. Film visti dall'utente
        film_visti = list(Film.objects.filter(
            proiezioni__prenotazioni__utente=utente,
            proiezioni__data_ora__lt=oggi
        ).distinct())
        for film in film_visti:
            film.immagine_genere = collega_film_immagine(film.genere)

        # 4. Film ora al cinema (proiezioni nella settimana successiva)
        inizio_settimana = oggi
        fine_settimana = oggi + timedelta(days=7)
        film_al_cinema = list(Film.objects.filter(
            proiezioni__data_ora__range=(inizio_settimana, fine_settimana)
        ).distinct())
        for film in film_al_cinema:
            film.immagine_genere = collega_film_immagine(film.genere)

        # Ora suddividiamo le liste film in gruppi da 3 per il carosello
        film_raccomandati_gruppi = self.chunk_list(film_raccomandati, 3)
        film_visti_gruppi = self.chunk_list(film_visti, 3)
        film_al_cinema_gruppi = self.chunk_list(film_al_cinema, 3)

        context.update({
            'prenotazioni_settimana': prenotazioni_settimana,
            'film_raccomandati': film_raccomandati_gruppi,
            'film_visti': film_visti_gruppi,
            'film_al_cinema': film_al_cinema_gruppi,
        })
        return context
    

# in sostanza view per aggiungere l'immagine del profilo
class ModificaProfiloView(LoginRequiredMixin, UpdateView):
    model = ProfiloUtente
    form_class = ProfiloForm
    template_name = 'modifica_profilo.html'
    success_url = reverse_lazy('utenti:profilo')

    def get_object(self):
        return self.request.user.profiloutente


