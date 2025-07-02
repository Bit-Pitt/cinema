from django.urls import path
from .views import *

app_name="prenotazioni"

urlpatterns = [
    path('', ProiezioneListView.as_view(), name='proiezioni-list'),
    path('proiezione/<int:pk>/', ProiezioneDetailView.as_view(), name='proiezione-dettaglio'),
    path('proiezione/<int:pk>/prenota/', PrenotazioneCreateView.as_view(), name='crea-prenotazione'),

]
