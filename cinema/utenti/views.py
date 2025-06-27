from django.shortcuts import render

# Create your views here.
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from .forms import * 

class UserCreateView(CreateView):
    form_class = CreaUtente
    template_name = "registration/signup.html"
    success_url = reverse_lazy("utenti:login")

