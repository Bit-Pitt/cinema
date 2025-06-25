
from django.urls import path
from .views import *

app_name = "film"

urlpatterns = [
    path("tmp/", tmp, name="t"),
    path("home/", home, name="homepage"),
    path("film/<pk>/", DetailFilmView.as_view(), name="film"),
]
