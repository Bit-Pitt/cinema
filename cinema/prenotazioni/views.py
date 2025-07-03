from django.shortcuts import render
from .models import *
from datetime import datetime, timedelta
from django.utils.timezone import now
from django.views.generic import *
import json
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from cinema.mixin import *    #Per importare i miei mixin Staff/Moderatore
from django.contrib.auth.mixins import LoginRequiredMixin



# Create your views here.


# Applica uno scoto del 10% per utenti silver, 20% per gold, utilizzando "Decimal" per coerenza con il modello
# Anche se per come è il prezzo unitario e lo sconto, il risultato sarà sempre intero
from decimal import Decimal, ROUND_HALF_UP

def calcola_prezzo(utente, num_posti):
    base = Decimal('10.00') * num_posti
    profilo = getattr(utente, 'profiloutente', None)
    if not profilo:
        return base.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    sconto = Decimal('0.00')
    abbonamento = profilo.abbonamento.lower()
    if abbonamento == 'silver':
        sconto = Decimal('0.10')
    elif abbonamento == 'gold':
        sconto = Decimal('0.20')

    prezzo_finale = base * (Decimal('1.00') - sconto)
    return prezzo_finale.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)




# ListView per mostrare le proiezioni (pre prenotare), con potenziali filtri modellati grazie a 
# get_queryset, se esiste il filtro lo applica
class ProiezioneListView(LoginRequiredMixin,ListView):
    model = Proiezione
    template_name = 'proiezioni-list.html' 
    context_object_name = 'proiezioni'
    paginate_by = 9

    def get_queryset(self):
        oggi = now().date()
        fine_settimana = oggi + timedelta(days=7)

        #Queryset delle proiezioni di questa settimana da mostrare all'apertura della pagina
        # ordinati per data proiezione
        qs = (              
            super().get_queryset()
            .select_related('film', 'sala')
            .filter(data_ora__date__range=(oggi, fine_settimana))
            .order_by('data_ora')
        )
        #Se il form è stato riempito dall'utente allora ci sono filtri da applicare
        film = self.request.GET.get('film')
        data = self.request.GET.get('data')  # da input type="date"

        if film:
            qs = qs.filter(film_id=film)

        if data:
            try:
                # data è una stringa tipo "2025-07-02" da convertire in "datetime" 
                data_obj = datetime.strptime(data, "%Y-%m-%d").date()
                qs = qs.filter(data_ora__date=data_obj)
            except ValueError:
                pass  

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        oggi = now().date()
        fine_settimana = oggi + timedelta(days=7)

        # questi due per mostrare poi il menu a tendina nel form
        context['film_list'] = (
            Proiezione.objects
            .filter(data_ora__date__range=(oggi, fine_settimana))
            .values('film__id', 'film__titolo')
            .distinct()
            .order_by('film__titolo')
        )

        context['date_list'] = (
            Proiezione.objects
            .filter(data_ora__date__range=(oggi, fine_settimana))
            .dates('data_ora', 'day')
        )

        # Salva selezione attuale per mantenere i filtri attivi tra le pagine
        context['selected_film'] = self.request.GET.get('film', '')
        context['selected_data'] = self.request.GET.get('data', '')

        return context
    


# E' la view collegata alla proiezione, sarà renderata in modo dinamico tramite js
class ProiezioneDetailView(LoginRequiredMixin,DetailView):
    model = Proiezione
    template_name = 'proiezione_detail.html'
    context_object_name = 'proiezione'

    #Ci portiamo lato template (per js) i posti per fila per il render dinamico
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sala = self.object.sala
        context['posti_per_fila'] = json.loads(sala.posti_per_fila_lista)

        # computiamo i posti già prenotati
        prenotazioni = Prenotazione.objects.filter(proiezione=self.object)
        posti_occupati = set()
        for p in prenotazioni:
            posti = json.loads(p.posti)
            posti_occupati.update(posti)
        context['posti_occupati'] = sorted(posti_occupati)

        return context


# View che si occupa di creare la prenotazione (dopo che l'utente ha selezionato i posti)
# E' di fatto una CBV, questo per il semplice motivo di implementare la ricezione tramite
# metodo "post" con la funzione "post" 
class PrenotazioneCreateView(LoginRequiredMixin,View):
    def post(self, request, pk):
        proiezione = get_object_or_404(Proiezione, pk=pk)
        posti = json.loads(request.POST.get('posti', '[]'))
        utente = request.user

        prenotazione = Prenotazione(
            utente=utente,
            proiezione=proiezione,
            posti=json.dumps(posti),
            prezzo=calcola_prezzo(utente, len(posti))       #funzione definita sopra
        )

        try:        #Gestisco i controlli lato modello, ma passo il messaggio di errore all'utente
            prenotazione.full_clean()
            prenotazione.save()
            #Se qui va bene:
            messages.success(request,"Prenotazione avvenuta con successo, nel profilo trovi i dettagli.")
            return redirect('film:homepage')
            #return redirect('utenti:profilo')...

        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect('prenotazioni:proiezione-dettaglio', pk=pk)


# Lo staff potrà accedere alle prenotazioni e eliminarle tramite queste due CBV
class PrenotazioneListView(StaffRequiredMixin,ListView):
    model = Prenotazione
    template_name = 'prenotazione_list.html'
    context_object_name = 'prenotazioni'
    paginate_by = 20


    def get_queryset(self):
        qs = Prenotazione.objects.select_related('proiezione__film', 'utente')\
            .order_by('proiezione__film__titolo', 'proiezione__data_ora')
        
        #Se ci sono i parametri filtrerà
        film = self.request.GET.get('film')
        utente = self.request.GET.get('utente')

        if film:
            qs = qs.filter(proiezione__film__titolo__icontains=film)
        if utente:
            qs = qs.filter(utente__username__iexact=utente)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        #per non perdere l'informazione quando passi da una pagina all'altra
        context['film_query'] = self.request.GET.get('film', '')
        context['utente_query'] = self.request.GET.get('utente', '')
        return context

# basica deleteView per cancellare la prenotazione
class PrenotazioneDeleteView(DeleteView):
    model = Prenotazione
    template_name = 'prenotazione_confirm_delete.html'
    success_url = reverse_lazy('prenotazioni:prenotazione_list')
