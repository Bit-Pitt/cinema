from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def tmp(request):
    template = "base.html"
    l = [i for i in range(4)]
    ctx = { 'title' : "ESEMPIO!" , "list": l}
    return render(request,template_name=template,context=ctx)





