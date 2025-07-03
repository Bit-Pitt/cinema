from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

app_name = "utenti"

urlpatterns = [
    #View riguande l'utente (login/logout/registrazione)
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", UserCreateView.as_view(), name="signup"), 

    #View per il forum (mostrare discussioni/discussione (msg) / creare discussione / creare msg di una discussione)
    path('forum', ListaDiscussioniView.as_view(), name='lista_discussioni'),
    path('forum/<int:pk>/', DettaglioDiscussioneView.as_view(), name='dettaglio_discussione'),
    path('forum/nuova/', CreaDiscussioneView.as_view(), name='crea_discussione'),
    path('forum/<int:pk>/aggiungi_messaggio/', aggiungi_messaggio, name='aggiungi_messaggio'),

    #View per commentare un film, votare (rate) un film
    path('<int:pk>/commenta/', CommentoCreateView.as_view(), name='commenta'),
    path('<int:pk>/vota/', RatingCreateView.as_view(), name='vota'),

    #View di abbonamento
    path('abbonati/', abbonati_view, name='abbonati'),
    path('attiva_abbonamento/', attiva_abbonamento, name='attiva_abbonamento'),

    #View per i moderatori
    path('commenti/', FilmModerazioneListView.as_view(), name='seleziona_film'),
    path('commenti/<int:film_id>/', CommentiPerFilmListView.as_view(), name='commenti_per_film'),
    path('commenti/delete/<int:pk>/', CommentoDeleteView.as_view(), name='commento_delete'),
    path('discussioni/', DiscussioneListView.as_view(), name='lista_discussioni_mod'),
    path('discussioni/<int:pk>/messaggi/', MessaggiPerDiscussioneView.as_view(), name='messaggi_per_discussione'),
    path('discussione/<int:pk>/elimina/', DiscussioneDeleteView.as_view(), name='discussione_delete'),
    path('messaggio/<int:pk>/elimina/', MessaggioDeleteView.as_view(), name='messaggio_delete'),


    # View per mostrare il profilo
    path('profilo/', ProfiloView.as_view(), name='profilo'),

]


