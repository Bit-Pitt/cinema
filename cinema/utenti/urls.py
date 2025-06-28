from django.urls import path
from django.contrib.auth import views as auth_views
from .views import *

app_name = "utenti"

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", UserCreateView.as_view(), name="signup"), 
    path('forum', ListaDiscussioniView.as_view(), name='lista_discussioni'),
    path('forum/<int:pk>/', DettaglioDiscussioneView.as_view(), name='dettaglio_discussione'),
    path('forum/nuova/', CreaDiscussioneView.as_view(), name='crea_discussione'),
    path('forum/<int:pk>/aggiungi_messaggio/', aggiungi_messaggio, name='aggiungi_messaggio'),
    path('<int:pk>/commenta/', CommentoCreateView.as_view(), name='commenta'),
    path('<int:pk>/vota/', RatingCreateView.as_view(), name='vota'),

]


