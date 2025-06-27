
from django.urls import path
from .views import *

app_name = "film"

urlpatterns = [
    path("home/", home, name="homepage"),
    path("film/<pk>/", DetailFilmView.as_view(), name="film"),
    path("cercafilm/", CercaFilmView.as_view(), name="cerca_film"),
    path("autocomplete/", autocomplete, name="autocomplete"),
]
