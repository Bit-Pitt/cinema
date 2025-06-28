
from django.urls import path
from .views import *

app_name = "film"

urlpatterns = [
    path("home/", home, name="homepage"),
    path("cercafilm/", CercaFilmView.as_view(), name="cerca_film"),
    path("autocomplete/", autocomplete, name="autocomplete"),

    path('film/aggiungi/', FilmCreateView.as_view(), name='film_create'),
    path('film/modifica/', FilmListModificaView.as_view(), name='film_list_modifica'),
    path('film/<int:pk>/modifica/', FilmUpdateView.as_view(), name='film_update'),

    path("film/<int:pk>/", DetailFilmView.as_view(), name="film"),
]

