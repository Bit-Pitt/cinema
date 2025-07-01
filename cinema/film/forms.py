from django import forms
from .models import Film,Proiezione

#In realtà se lo lascio così non era necessario, è in sostanza la versione base della createView
class FilmForm(forms.ModelForm):
    class Meta:
        model = Film
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Imposta il valore iniziale solo se il form è in modalità "creazione"
        if not self.instance.pk:
            self.fields['durata'].initial = 100

# Form per la creazione / modifica di una sala
class ProiezioneForm(forms.ModelForm):
    class Meta:
        model = Proiezione
        fields = ['film', 'sala', 'data_ora']
        widgets = {     #Specifico il widget per avere il campo di input adatto alle date
            'data_ora': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        }
    #Per ordinare per titolo
    def __init__(self, *args, **kwargs):
        super(ProiezioneForm, self).__init__(*args, **kwargs)
        self.fields['film'].queryset = Film.objects.order_by('titolo')

