
from django.urls import path
from .views import *

app_name = "film"

urlpatterns = [
    path("home/", home, name="homepage"),
    path("cercafilm/", CercaFilmView.as_view(), name="cerca_film"),
    path("autocomplete/", autocomplete, name="autocomplete"),       #codice js

    #Aggiungi/modifica per film (da utente Staff)
    path('film/aggiungi/', FilmCreateView.as_view(), name='film_create'),
    path('film/modifica/', FilmListModificaView.as_view(), name='film_list_modifica'),
    path('film/<int:pk>/modifica/', FilmUpdateView.as_view(), name='film_update'),
    path('film/<int:pk>/elimina/', FilmDeleteView.as_view(), name='film_delete'),

    #Aggiungi/modifica per proiezioni(utente staff)
    path('proiezione/aggiungi/', ProiezioneCreateView.as_view(), name='proiezione_create'),
    path('proiezione/modifica/', ProiezioneListModificaView.as_view(), name='proiezione_list_modifica'),
    path('proiezione/<int:pk>/modifica/', ProiezioneUpdateView.as_view(), name='proiezione_update'),
    path('proiezione/<int:pk>/elimina/', ProiezioneDeleteView.as_view(), name='proiezione_delete'),


    #Detail di un film
    path("film/<int:pk>/", DetailFilmView.as_view(), name="film"),

    #Opzione della navBar
    path('dove-siamo/', dove_siamo, name='dove_siamo'),

    #Statistiche
    path('statistiche/', statistiche_film, name='statistiche_film'),


]

