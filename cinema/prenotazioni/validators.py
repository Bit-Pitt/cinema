from django.core.exceptions import ValidationError
from film.models import *
from utenti.models import *
import json

# Verifica che i posti siano contigui
def validate_posti_contigui(lista_posti):
    lista_posti_sorted = sorted(lista_posti)
    for i in range(len(lista_posti_sorted) - 1):
        if lista_posti_sorted[i+1] != lista_posti_sorted[i] + 1:
            raise ValidationError("I posti devono essere contigui.")

# 1) Valida che i posti esistano      
# 2) Valida che i posti non siano occupati, prende tutti i posti occupati dalle altre prenotazioni
# di questa proiezione
def validate_posti_sala_e_disponibilita(prenotazione):
    sala = prenotazione.proiezione.sala
    # Ottieni lista posti per fila come lista di interi
    lista_posti_per_fila = json.loads(sala.posti_per_fila_lista)
    totale_posti = sum(lista_posti_per_fila)

    lista_posti_prenotazione = json.loads(prenotazione.posti)

    # Controllo validità posti nella sala
    for posto in lista_posti_prenotazione:
        if posto < 1 or posto > totale_posti:
            raise ValidationError(f"Il posto {posto} non è valido nella sala {sala.nome}.")

    # Controlla sovrapposizione con altre prenotazioni, prende in primis tutte le altre prenotazioni
    prenotazioni_occupate = prenotazione.__class__.objects.filter(
        proiezione=prenotazione.proiezione
    ).exclude(id=prenotazione.id)

    posti_occupati = set()          #salviamo tutti i posti occupati come set() che aggiorniamo
    for pren in prenotazioni_occupate:
        try:
            posti_pren = json.loads(pren.posti)
            posti_occupati.update(posti_pren)
        except json.JSONDecodeError:
            continue

    #any: ritorna True se è True per almeno uno nell'iterabile
    if any(posto in posti_occupati for posto in lista_posti_prenotazione):
        raise ValidationError("Uno o più posti sono già prenotati.")
    
# Valida che se sono stati scelti dei posti gold all'ora l'utente sia Gold
# I posti gold sono tutti quella della fila centrale (se dispari le file) altrimenti la fila data da file//2
def validate_posti_gold(prenotazione):
    sala = prenotazione.proiezione.sala
    lista_posti_per_fila = json.loads(sala.posti_per_fila_lista)
    num_file = len(lista_posti_per_fila)

    # Calcolo fila centrale (index zero-based), es se sala 9 file: 9//2=4 (ovvero la 5° fila giusto)
    if num_file % 2 == 0:
        fila_centrale = num_file // 2 - 1  
    else:
        fila_centrale = num_file // 2

    # Calcolo intervallo posti fila centrale
    # I posti sono contati consecutivamente da 1 a totale_posti
    posti_prima = sum(lista_posti_per_fila[:fila_centrale])
    posti_fila_centrale = lista_posti_per_fila[fila_centrale]
    inizio_gold = posti_prima + 1
    fine_gold = posti_prima + posti_fila_centrale
    #ES:   [ 10 10 15 15 15]
    # posti_prima = (10+10), posti_fila_centrale=l[3]=15 ,  inizio_gold=21 , fine_gold=20+15=35 CORRETTO

    lista_posti_prenotazione = json.loads(prenotazione.posti)

    # Controlla se ci sono posti gold nella prenotazione e nel caso controlla che l'utente sia gold
    prenota_posto_gold = any(inizio_gold <= posto <= fine_gold for posto in lista_posti_prenotazione)

    if prenota_posto_gold:
        profilo = ProfiloUtente.objects.get(user=prenotazione.utente)
        if profilo.abbonamento.lower() != 'gold':
            raise ValidationError("Solo utenti Gold possono prenotare posti nella fila centrale.")


