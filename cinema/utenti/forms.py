from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group

class CreaUtente(UserCreationForm):
    def save(self, commit=True):
        user = super().save(commit) #ottengo un riferimento all'utente
        #g = Group.objects.get(name="Lettori") #cerco il gruppo che mi interessa
        #g.user_set.add(user) #aggiungo l'utente al gruppo
        return user 
