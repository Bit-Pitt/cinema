from django import forms
from .models import Film

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
