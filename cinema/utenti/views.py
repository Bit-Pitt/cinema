from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import *
from .forms import * 
from django.db.models import Count
from .models import *
from django.core.paginator import Paginator
from django.contrib import messages
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from datetime import timedelta , date


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
class CreaDiscussioneView(CreateView):
    model = Discussione
    form_class = DiscussioneForm
    template_name = 'forum/crea_discussione.html'
    success_url = reverse_lazy('utenti:lista_discussioni')

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
class CommentoCreateView(CreateView):
    model = Commento
    form_class = CommentoForm
    template_name = 'commenta.html'

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
class RatingCreateView(CreateView):
    model = Rating
    form_class = RatingForm
    template_name = 'rating.html'

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

# Lista dei commenti (per moderatori)
class CommentoListView(ListView):
    model = Commento
    template_name = 'moderazione/commento_list.html'
    context_object_name = 'commenti'
    ordering = ['film__titolo', 'utente__username']  # ordinamento alfabetico per film e utente

# DeleteView per commento
class CommentoDeleteView(DeleteView):
    model = Commento
    template_name = 'moderazione/commento_confirm_delete.html'
    success_url = reverse_lazy('moderazione:lista_commenti')






