
from django.urls import path
from .views import *

app_name = "film"

urlpatterns = [
    path("tmp/", tmp, name="t"),
]
