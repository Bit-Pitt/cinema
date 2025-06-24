from film.models import *
import json
import os
from datetime import datetime, timedelta
import random

def erase_db():
    print("Cancello il DB")
    Film.objects.all().delete()
    Sala.objects.all().delete()
    Proiezione.objects.all().delete()           #in teoria non necessario per "onCascade"

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

def load_proiezioni():

    def generate_random_datetime(start_date, end_date):
        delta = end_date - start_date
        random_seconds = random.randint(0, int(delta.total_seconds()))
        return start_date + timedelta(seconds=random_seconds)

    # Define the start and end times for the proiezioni (4 PM to 11 PM)
    start_time = 16  # 4 PM
    end_time = 23   # 11 PM

    # Define the current date and the next week date
    current_date = datetime.now()
    next_week_date = current_date + timedelta(weeks=1)

    # Generate 10 proiezioni for the current week
    proiezioni_current_week = []
    for i in range(10):
        random_date = generate_random_datetime(current_date, current_date + timedelta(days=7))
        random_date = random_date.replace(hour=random.randint(start_time, end_time), minute=0, second=0, microsecond=0)
        proiezioni_current_week.append({
            "film_id": random.randint(1, 10),  # Assuming film IDs are between 1 and 10
            "sala_id": random.randint(1, 10),  # Assuming sala IDs are between 1 and 10
            "data_ora": random_date.isoformat()
        })

    # Generate 10 proiezioni for the next week
    proiezioni_next_week = []
    for i in range(10):
        random_date = generate_random_datetime(next_week_date, next_week_date + timedelta(days=7))
        random_date = random_date.replace(hour=random.randint(start_time, end_time), minute=0, second=0, microsecond=0)
        proiezioni_next_week.append({
            "film_id": random.randint(1, 10),  # Assuming film IDs are between 1 and 10
            "sala_id": random.randint(1, 10),  # Assuming sala IDs are between 1 and 10
            "data_ora": random_date.isoformat()
        })

    # Combine the proiezioni
    proiezioni = proiezioni_current_week + proiezioni_next_week

    # Print the proiezioni as a JSON string
    print(json.dumps(proiezioni, indent=4))

