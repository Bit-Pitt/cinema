from film.models import *
import json
import os
from datetime import datetime, timedelta
import random
from django.utils import timezone


def erase_db():
    print("Cancello il DB")          
    Film.objects.all().delete()
    Sala.objects.all().delete()
    Proiezione.objects.all().delete() 


def init_db():
    
    if len(Film.objects.all()) != 0:
        return
    
    load_film()  
    load_sale()    
    load_proiezioni()       


def load_film():
    path = os.path.join(os.path.dirname(__file__), "Jsons", "film.json")   
    
    with open(path, 'r', encoding='utf-8') as file:
        films_data = json.load(file)

    for film_dict in films_data:
        film = Film()
        film.titolo = film_dict.get('titolo', '')       #se non trova il campo lo inizializza a vuoto
        film.trama = film_dict.get('trama', '')
        film.cast = film_dict.get('cast', '')
        film.durata = film_dict.get('durata', 0)
        film.genere = film_dict.get('genere', '')
        film.save()
    


def load_sale():
    path = os.path.join(os.path.dirname(__file__), "Jsons", "sale.json")   
    
    with open(path, 'r', encoding='utf-8') as file:
        sale = json.load(file)

    for sala_dict in sale:
        sala = Sala()
        sala.nome = sala_dict['nome']
        sala.numero_posti = sala_dict['numero_posti']
        sala.file = sala_dict['file']
        sala.posti_per_fila = sala_dict['posti_per_fila']
        sala.save() 


# Genero 30 date casuali tra le 4 e le 11 di questa settimana e la prossima 
# Assegno a 10 film le 30 date per questa settimana e altri 10 film le date della prossima
# assegno una sala
# salvo nel db
def load_proiezioni():
    #genera una data casuale tra [start_date,end_date]
    def generate_random_datetime(start_date, end_date):
        delta = end_date - start_date
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start_date + timedelta(seconds=random_seconds)

    # Tempo di inizio e fine proiezioni (4 PM to 11 PM)
    start_time = 16  
    end_time = 23   

    current_date = datetime.now()
    next_week_date = current_date + timedelta(weeks=1)

    proiezioni_current_week = []
    for i in range(30):
        random_date = generate_random_datetime(current_date, current_date + timedelta(days=7))
        random_date = random_date.replace(hour=random.randint(start_time, end_time), minute=0, second=0, microsecond=0)
        random_date = timezone.make_aware(random_date)
        proiezioni_current_week.append(random_date.isoformat())    #formato std

    proiezioni_next_week = []
    for i in range(30):
        random_date = generate_random_datetime(next_week_date, next_week_date + timedelta(days=7))
        random_date = random_date.replace(hour=random.randint(start_time, end_time), minute=0, second=0, microsecond=0)
        random_date = timezone.make_aware(random_date)
        proiezioni_next_week.append(random_date.isoformat())

    sale_nomi = sale_nomi = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    sale = [Sala.objects.get(nome=nome) for nome in sale_nomi]

    primi_10_film = Film.objects.all()[:10]
    ultimi_10_film = Film.objects.all().order_by('-id')[:10]
    
    for film in primi_10_film:
        for _ in range(3):
            proiezione = Proiezione()
            proiezione.film = film
            proiezione.data_ora = proiezioni_current_week[0]
            proiezioni_current_week.pop(0)
            proiezione.sala = random.choice(sale)
            try:
                proiezione.save()
            except ValidationError as e:
                print(f"Errore: {e} salto questa proiezione per il film '{film.titolo}'")
                continue  

    
    for film in ultimi_10_film:
        for _ in range(3):
            proiezione = Proiezione()
            proiezione.film = film
            proiezione.data_ora = proiezioni_next_week[0]
            proiezioni_next_week.pop(0)
            proiezione.sala = random.choice(sale)
            try:
                proiezione.save()
            except ValidationError as e:
                print(f"Errore: {e} salto questa proiezione per il film '{film.titolo}'")
                continue  



