from django.contrib import admin
from django.urls import path, re_path,include
from django.shortcuts import redirect
from .initcmds import *
from utenti.views import disattiva_abbonamenti
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path("films/", include("film.urls")),
    path("accounts/", include("utenti.urls")),
    path("prenotazioni/",include("prenotazioni.urls")),
    re_path(r'$^|$/^', lambda request: redirect('film:homepage')), 
]

#In caso di debug aggiungo i "Media" --> foto caricate dagli utenti
if settings.DEBUG:  
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


#erase_db()
init_db()
disattiva_abbonamenti()


