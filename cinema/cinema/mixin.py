from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse



# In questo fil definisco i miei mixin per Moderatore e Staff (evitando di installare una libreria a parte)
class ModeratoreRequiredMixin(UserPassesTestMixin):
    def test_func(self):    #controllo se utente ha il gruppo "moderatori"
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='moderatori').exists()

    def handle_no_permission(self):         #Altrimenti riporta al login
        login_url = reverse('utenti:login') 
        return redirect_to_login(self.request.get_full_path(), login_url)
    

# Analogo per staff
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        # Controlla se l'utente è autenticato e appartiene al gruppo 'staff'
        return self.request.user.is_authenticated and self.request.user.groups.filter(name='staff').exists()

    def handle_no_permission(self):
        # Redirige al login personalizzato con namespace corretto
        login_url = reverse('utenti:login')
        return redirect_to_login(self.request.get_full_path(), login_url)
