from django.http import HttpResponse

def temp(request):
    return HttpResponse("TEMP!")