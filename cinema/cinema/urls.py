from django.contrib import admin
from django.urls import path, re_path,include
from django.shortcuts import redirect
from .initcmds import *
from utenti.views import disattiva_abbonamenti

urlpatterns = [
    path('admin/', admin.site.urls),
    path("films/", include("film.urls")),
    path("accounts/", include("utenti.urls")),
    re_path(r'$^|$/^', lambda request: redirect('film:homepage')), 
]


#erase_db()
init_db()
disattiva_abbonamenti()


