from django.contrib.auth.forms import UserCreationForm
from .models import *
from django import forms

#Form di creazione dell'utente dato a gratis da "UserCreationForm"
class CreaUtente(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit) 
        return user 
    
# Form per l'aggiunta dell'immagine (gestito da django che il campo sia un "Image" nel modello)
class ProfiloForm(forms.ModelForm):
    class Meta:
        model = ProfiloUtente
        fields = ['immagine_profilo']


# Form per creare una nuova discussione  (basterà ottenere il titolo --> utente e data automatici)
class DiscussioneForm(forms.ModelForm):
    class Meta:
        model = Discussione
        fields = ['titolo']         #definisci i campi editabili
        labels = {
            'titolo': 'Titolo della discussione',
        }


# Form per creare un messaggio di una discussione (basterà il contenuto --> utente e data automatici)
class MessaggioForm(forms.ModelForm):
    class Meta:
        model = Messaggio
        fields = ['contenuto']              #Il field contenuto sarà quello modificato
        widgets = {
            'contenuto': forms.Textarea(attrs={'rows': 3}),
        }


# Form per la creazione di un commento riguardo ad un film, necessiterà semplicemente del testo
class CommentoForm(forms.ModelForm):
    class Meta:
        model = Commento
        fields = ['testo']
        widgets = {
            'testo': forms.Textarea(attrs={'rows': 3, 'maxlength': 100, 'placeholder': 'Scrivi il tuo commento...'}),
        }


#Form per l'immissione di una valutazione, dando solo la scelta 1-5
class RatingForm(forms.ModelForm):
    class Meta:
        model = Rating
        fields = ['voto']
        widgets = {
            'voto': forms.Select(choices=[(i, f"{i} ★") for i in range(1, 6)], attrs={'class': 'form-select'}),
        }
        labels = {
            'voto': 'Valutazione',
        }
