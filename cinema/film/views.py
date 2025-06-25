from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

def tmp(request):
    template = "base.html"
    l = [i for i in range(4)]
    ctx = { 'title' : "ESEMPIO!" , "list": l}
    
    return render(request,template_name=template,context=ctx)

''' Aggiungi link dinamici ai film / Attori di un film!! (questo nel template )
<a href="https://it.wikipedia.org/w/index.php?search={{ film.titolo|urlencode }}" target="_blank" rel="noopener noreferrer">
    Cerca su Wikipedia
</a>

'''




