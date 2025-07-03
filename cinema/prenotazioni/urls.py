from django.urls import path
from .views import *

app_name="prenotazioni"

urlpatterns = [
    path('', ProiezioneListView.as_view(), name='proiezioni-list'),
    path('proiezione/<int:pk>/', ProiezioneDetailView.as_view(), name='proiezione-dettaglio'),
    path('proiezione/<int:pk>/prenota/', PrenotazioneCreateView.as_view(), name='crea-prenotazione'),
    path('lista/', PrenotazioneListView.as_view(), name='prenotazione_list'),
    path('elimina/<int:pk>/', PrenotazioneDeleteView.as_view(), name='prenotazione_delete'),

]


