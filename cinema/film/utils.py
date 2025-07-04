from prenotazioni.models import Prenotazione
from film.models import Film, Proiezione
from collections import defaultdict
from django.utils.timezone import now, timedelta
from utenti.models import Rating

# FUNZIONE CHE IMPLEMENTA IL SISTEMA DI RACCOMANDAZIONE User-based binario (film visto 1, 0 altrimenti)
# e utilizzo di cosine similarity  --> Con peso in caso di rating dell'utente!
# Nello specifico, lo score di ogni film non visto per l'utente "user_corrente":
# - somma delle sim(User_corrente,User_j)*peso_rating se user_j ha visto il film  /   tot_utenti_che hanno visto il film
# Se "ora_al_cinema" allora filtrerà solo per i film che hanno proiezioni future
# Se debug=False anche se tutti i film hanno score=0 verranno consigliati dei film
def get_raccomandazioni_utente(user_corrente, top_n=9,ora_al_cinema=False,debug=False):
    oggi = now()

    # Step 1: Costruisci {utente_id: set di film_id visti}
    user_film_map = defaultdict(set)        #dizionario {chiave: set()}
    prenotazioni = Prenotazione.objects.select_related('utente', 'proiezione__film').filter(
        proiezione__data_ora__lt=oggi
    )
    for p in prenotazioni:
        user_film_map[p.utente.id].add(p.proiezione.film.id)
    #Creato la tabella.

    # Film visti dall'utente corrente   [abbiamo quindi la lista dei suoi film visti]
    film_corrente = user_film_map[user_corrente.id]

    # Step 2: Calcola similarità tra gli altri utenti ==> quanti film hanno visto in comune
    # ovvero intersezione dei due insieme / tot film visti da loro
    similarita_utenti = {}
    for altro_id, film_visti in user_film_map.items():  #srotola il dizionario 
        if altro_id == user_corrente.id:
            continue
        intersezione = len(film_corrente & film_visti)
        unione = len(film_corrente | film_visti)
        if unione > 0:
            similarita_utenti[altro_id] = intersezione / unione

    # Step 3: Punteggio per ogni film NON visto
    punteggi_film = defaultdict(float)          #dizionario con chiave:float (punteggio)
    somma_sim = defaultdict(float)


    # Carica i rating in memoria: { (utente_id, film_id): voto }
    # Prima carico in forma di lista
    # Poi creo il dizionario per essere agevolmente acceduto dopo
    ratings = Rating.objects.all().values_list('utente_id', 'film_id', 'voto')
    rating_map = {(u, f): v for u, f, v in ratings}

    # Funzione per trasformare voto in peso
    def peso_voto(voto):
        return {
            1: 0.2,
            2: 0.5,
            3: 1,
            4: 1.5,
            5: 2
        }.get(voto, 1)  # Default a 1 se non trovato (non dovrebbe accadere)

    #Srotolo "similarità_utenti" che è fatto ad es:
    #  {  utente1: 0.34 , utente2: 0.52 ... }
    # Adesso per ogni film visto da utente_j (user_film_map[altro_id])
    #   Se il film non è stato già visto dall'utente corrente: sommo la similarità (*moltiplicatore) allo score di questo film non visto
    for altro_id, sim in similarita_utenti.items():
        for film_id in user_film_map[altro_id]:
            if film_id not in film_corrente:  # film non ancora visto da utente corrente
                voto = rating_map.get((altro_id, film_id), None)    #controllo se "altro_id" ha votato
                moltiplicatore = peso_voto(voto) if voto is not None else 1
                punteggi_film[film_id] += sim * moltiplicatore  # sim pesata per il voto
                somma_sim[film_id] += 1
                
    # somma_sim == > ci serve perchè lo score finale del film sarà:  somma_similarità_altri_utenti / num di utenti che hanno partecipato allo score
    # così che sarà vincente il film che ha avuto la somma di similarità medie più alte!


    # Step 4: CAlcola score come commentato sopra e ordina
    raccomandazioni = []
    for film_id in punteggi_film:
        score = punteggi_film[film_id] / somma_sim[film_id]
        if score > 0 or debug==False:
            raccomandazioni.append((film_id, score))

    #Faccio un sorting su queste tuple sulla base dello score (quindi il secondo argomento)
    raccomandazioni.sort(key=lambda x: x[1], reverse=True)

        # Step 5: Recupera oggetti Film (gli id)
    film_ids = [fid for fid, _ in raccomandazioni]

    # Se filtro attivo --> restringo ai film con proiezioni nelle prossime 2 settimane
    if ora_al_cinema:
        tra_due_settimane = oggi + timedelta(weeks=2)
        film_al_cinema = set(
            Proiezione.objects.filter(
                data_ora__range=(oggi, tra_due_settimane)
            ).values_list('film_id', flat=True)
        )
        film_ids = [fid for fid in film_ids if fid in film_al_cinema]   #applicato il filtro (senza perdere ordine)

    # Prendi i top N dopo eventuale filtro
    film_ids = film_ids[:top_n]
    film_raccomandati = list(Film.objects.filter(id__in=film_ids))

    # Potrei aver perso l'ordine dopo "list(....filter..)" quindi: ordina secondo la lista "film_ids" creata step 5
    film_raccomandati.sort(key=lambda f: film_ids.index(f.id))
        
    return film_raccomandati











#La funzione si aspetta la stringa "genere" del modello "Film"  Es:  "Thriller / Drama"
def collega_film_immagine(genere):
    generi_immagini = {
            "animazione": "animazione.jpg",
            "azione": "azione.jpg",
            "avventura":"azione.jpg",
            "crime": "crime.jpg",
            "drammatico": "drammatico.jpg",
            "fantasy": "fantasy.jpg",
            "fantascienza": "fantasy.jpg",
            "thriller": "thriller.jpg",
            "biografico": "biografia.jpg",
        }

    genere = genere.lower()
    # I generi possono essere due nella forma  "Thriller / drama" ==> voglio ['thriller','drama']
    generi_film = [g.strip() for g in genere.split("/")]

    # Vista la massiccia presenza di "drammatici" e quindi la relativa immagine, posiziono il genere
    # in seconda posizione così da ridurne l'occorrenza
    if len(generi_film) > 1 and generi_film[0] == "drammatico":
        generi_film[0], generi_film[1] = generi_film[1], generi_film[0]

    immagine = "default.jpg"
    for g in generi_film:
        if g in generi_immagini:
            immagine = generi_immagini[g]           #assegno la jpg specifica
            return immagine
    
    return "default.jpg"

