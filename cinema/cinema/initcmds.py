from film.models import *
import json
import os
from datetime import datetime, timedelta , time, date
import random
from django.utils import timezone
from django.contrib.auth.models import User
from utenti.models import *
from prenotazioni.models import Prenotazione
from django.utils.timezone import now
from prenotazioni.views import *
from django.contrib.auth.models import Group, User



def erase_db():
    print("Cancello il DB")         
    Film.objects.all().delete()
    Sala.objects.all().delete()
    Proiezione.objects.all().delete() 
    User.objects.all().delete() #cancella quelli di test
    Commento.objects.all().delete()
    Rating.objects.all().delete()
    Discussione.objects.all().delete()
    Messaggio.objects.all().delete()
    ProfiloUtente.objects.all().delete()
    Prenotazione.objects.all().delete()


def init_db():

    if len(Film.objects.all()) != 0:
        return
    load_film()  
    load_sale()    
    load_proiezioni()
    crea_utenti()         
    crea_commenti()
    crea_ratings()
    load_forum()
    crea_staff()
    crea_prenotazioni()
    crea_assegna_gruppi()




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
        posti_per_fila_lista_str = sala_dict['posti_per_fila_lista']
        # Converte la stringa  lista Python
        posti_per_fila = json.loads(posti_per_fila_lista_str)

        sala = Sala(
            nome=sala_dict['nome'],
            numero_posti=sum(posti_per_fila), 
            posti_per_fila_lista=posti_per_fila_lista_str
        )
        sala.save()



# Genero 30 date casuali tra le 16.00 e le 23.00 di questa settimana e la prossima 
# Assegno a 10 film le 30 date per questa settimana e altri 10 film le date della prossima
# assegno una sala
# salvo nel db
# Estensione per sistema di raccomandazione: aggiunta di proiezioni passate
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

                # --- PROIEZIONI PASSATE ---
    past_start_date = current_date - timedelta(days=90)  # fino a 3 mesi fa
    past_end_date = current_date - timedelta(days=1)     # fino a ieri

    proiezioni_passate = []
    for _ in range(90):
        random_date = generate_random_datetime(past_start_date, past_end_date)
        random_date = random_date.replace(hour=random.randint(start_time, end_time), minute=0, second=0, microsecond=0)
        random_date = timezone.make_aware(random_date)
        proiezioni_passate.append(random_date.isoformat())

    #Prendo i primi 30 film nel db
    film_misti = Film.objects.all()[:30]
    for film in film_misti:
        for _ in range(3):
            if not proiezioni_passate:      #Mi fermo quando ho terminato le proiezioni passate
                break
            proiezione = Proiezione()
            proiezione.film = film
            proiezione.data_ora = proiezioni_passate.pop(0)         #ottiene la proiezione e la toglie dalla lista
            proiezione.sala = random.choice(sale)
            try:
                proiezione.save()
                print(f"---------- Aggiunta proiezione nel passato ")
            except ValidationError as e:
                print(f"Errore: {e} salto proiezione passata per '{film.titolo}'")
                continue







# La funzione crea 30 utenti, 5 gold, 15 silver, 10 basic (default)
def crea_utenti():
    utenti_creati = []

    for i in range(1, 31):
        username = f'utente{i}'
        email = f'utente{i}@esempio.com'
        password = 'progetto123'
        user = User.objects.create_user(username=username, email=email, password=password)
        utenti_creati.append(user)

    # A questo punto i ProfiloUtente sono stati creati automaticamente grazie ai signals

    #  15 utenti a 'silver'
    for user in utenti_creati[0:15]:
        user.profiloutente.abbonamento = 'silver'
        user.profiloutente.scadenza_abbonamento = date.today()+timedelta(days=30)
        user.profiloutente.save()

    #  5 utenti a 'gold'
    for user in utenti_creati[15:20]:
        user.profiloutente.abbonamento = 'gold'
        user.profiloutente.scadenza_abbonamento = date.today()+timedelta(days=30)
        user.profiloutente.save()

# Popolo il db di commenti: 
# Nel file "commenti.json" ci sono 30 commenti generici
# Per ogni film do un numero di commenti casuali  da 3 a 10, e li prendo casualmente dai commenti nel json
def crea_commenti():
    path = os.path.join(os.path.dirname(__file__), "Jsons", "commenti.json")   

    with open(path, encoding='utf-8') as f:
        commenti_generici = json.load(f)

    films = Film.objects.all()

    for film in films:
        numero_commenti = random.randint(3, 10)
        commenti_casuali = random.sample(commenti_generici, numero_commenti)

        for c in commenti_casuali:
            try:
                utente = User.objects.get(username=c["utente"])
                    # qui generlo la data   casuale
                random_hour = random.randint(0, 23)
                random_minute = random.randint(0, 59)
                data_base = datetime.strptime(c["data"], "%Y-%m-%d")
                data_completa = datetime.combine(data_base.date(), time(random_hour, random_minute))
                data_completa = timezone.make_aware(data_completa)


                Commento.objects.create(
                    film=film,
                    utente=utente,
                    testo=c["testo"],
                    data_commento=data_completa
                )
            except User.DoesNotExist:
                print(f"Utente non trovato: {c['utente']} — commento ignorato")


# La funzione crea i ratings nel seguente modo:
# Ottiene i 20 utenti  "utenti{i}" carica in "load_utenti"  (i silver e gold)
# Per ogni film, assegna un numero randomico di rating, questi rating hanno un utente random e voto random
def crea_ratings():
    utenti_nomi = [f'utente{i}' for i in range(1, 21)]
    utenti = {u.username: u for u in User.objects.filter(username__in=utenti_nomi)}

    film_list = Film.objects.all()

    for film in film_list:
        num_ratings = random.randint(10, 20)
        utenti_usati = set()

        for _ in range(num_ratings):
            while True:
                username = random.choice(utenti_nomi)
                if username not in utenti_usati:
                    utenti_usati.add(username)
                    break

            utente = utenti.get(username)
            if not utente:
                continue 

            voto = random.randint(1, 5)
            Rating.objects.create(
                film=film,
                utente=utente,
                voto=voto
            )


# Crea una data random nel 2024 per popolare il forum
def random_data_2024():
    start = datetime(2024, 1, 1)
    end = datetime(2024, 12, 31)
    delta = end - start
    random_days = random.randint(0, delta.days)
    random_minutes = random.randint(0, 1440)    #24*60 (minuti in un giorno)
    return timezone.make_aware(start + timedelta(days=random_days, minutes=random_minutes))


# La funzione crea 10 discussioni (con titolo casuale)  e riguardo un film casuale
# Per ogni tipo di discussione ce allegato un dizionari di messaggi che verranno scelti a caso (anche il numero
# di messaggi  è casuale) e poi saranno collegati alla discussione

def load_forum():
    utenti = list(User.objects.filter(username__startswith="utente"))
    film_tutti = list(Film.objects.all())

    titoli_categorie = {
        "Pareri su": "generale",
        "Discussione su": "generale",
        "Opinioni su": "generale",
        "Cosa ne pensate di": "generale",
        "Analisi del film": "generale",
        "Recitazione in": "recitazione",
        "Genere e stile di": "genere",
        "Soundtrack di": "musica",
        "Scene memorabili in": "scene",
        "Regia in": "regia"
    }

    messaggi_per_categoria = {
        "generale": [
            "Bellissimo film!", "Non mi ha convinto.", "Film molto interessante.",
            "Lo consiglio a tutti.", "Potevano fare di meglio.",
            "Un film che rivedrei volentieri.", "Mi ha sorpreso in positivo.",
            "Non è il mio genere preferito, ma l'ho apprezzato.",
            "Trama coinvolgente e mai noiosa.", "Troppo sopravvalutato secondo me."
        ],
        "recitazione": [
            "L’attore protagonista è eccezionale.", "Recitazione mediocre.", "Ottima interpretazione del cast.",
            "Non mi è piaciuto il protagonista.", "Cast di altissimo livello.",
            "Gli attori secondari rubano la scena!", "Dialoghi ben recitati e naturali.",
            "Alcuni attori fuori ruolo.", "Recitazione molto intensa.", "Performance emozionante."
        ],
        "genere": [
            "Mi aspettavo più azione.", "Adoro questo stile narrativo.",
            "Il ritmo è lento ma coinvolgente.", "Un mix di generi ben riuscito.",
            "Troppo drammatico per i miei gusti.", "Perfetto per gli amanti del thriller.",
            "Un classico esempio di noir moderno.", "Genere trattato in modo originale.",
            "Poco innovativo rispetto ad altri film.", "Un horror che non fa paura."
        ],
        "musica": [
            "Colonna sonora fantastica!", "Le musiche sono da brividi.",
            "Soundtrack un po’ anonima.", "Adoro le musiche di questo film.",
            "Musiche che esaltano ogni scena.", "Compositore in gran forma.",
            "Tema musicale memorabile.", "Colonna sonora fuori contesto.",
            "Musiche troppo invasive.", "La musica accompagna perfettamente le emozioni."
        ],
        "scene": [
            "La scena finale è epica.", "Mi ha colpito molto una scena in particolare.",
            "Scene d’azione ben girate.", "Momenti molto toccanti.",
            "L’inseguimento è stato spettacolare.", "Sequenza iniziale da brividi.",
            "La scena romantica mi ha emozionato.", "Troppi rallenty inutili.",
            "Scene ben montate e fluide.", "Alcune scene sembravano fuori luogo."
        ],
        "regia": [
            "Regia spettacolare.", "Il regista ha fatto un gran lavoro.",
            "Scelte registiche discutibili.", "Inquadrature memorabili.",
            "Una regia che lascia il segno.", "Montaggio e ritmo gestiti benissimo.",
            "Troppo autoreferenziale.", "Stile registico elegante.",
            "Regia piatta e senza personalità.", "Uso intelligente della macchina da presa."
        ]
    }

    #Qui creo le 10 discussioni
    for _ in range(10):
        film = random.choice(film_tutti)
        utente_creatore = random.choice(utenti)

        titolo_base = random.choice(list(titoli_categorie.keys()))
        categoria = titoli_categorie[titolo_base]           #mi serve per poi trovare i messaggi coerenti
        titolo = f"{titolo_base} {film.titolo}"

        discussione = Discussione.objects.create(
            titolo=titolo,
            utente=utente_creatore,
            data_creazione=random_data_2024()
        )

        #Qui creo i messaggi correlati alle discussioni
        n_messaggi = random.randint(3, 15)
        ultimo_msg_data = None

        for _ in range(n_messaggi):
            autore = random.choice(utenti)
            contenuto = random.choice(messaggi_per_categoria[categoria])
            data = random_data_2024()

            if ultimo_msg_data:
                ultimo_msg_data = max(ultimo_msg_data, data)
            else:
                ultimo_msg_data = data

            Messaggio.objects.create(
                discussione=discussione,
                utente=autore,
                contenuto=contenuto,
                data_invio=data
            )

        discussione.ultimo_messaggio_data = ultimo_msg_data
        discussione.save()

#Crea 5 utenti staff:   staffi {i=0..5} psw: progetto123
#Crea 5 utenti moderatori  moderatorxi {x1..5}
def crea_staff():
    for i in range(1, 6):
        username = f"staff{i}"
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password="progetto123",
            )
            user.is_staff = True
            user.save()

    for i in range(1, 6):
        username = f"moderatori{i}"
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password="progetto123",
            )
            user.save()
            profilo = ProfiloUtente.objects.get(user=user)
            profilo.is_moderatore = True
            profilo.save()





# Crea prenotazioni
'''
prende tutte le proiezioni di questa settimana  <-- è tutte quelle passate per popolare il db per sistema di raccomandazioni
per ogni proiezione cicla sulle file della sala
per ogni fila calcola un numero casuale di posti da prenotare (tra 0 e la lunghezza della fila)
applica uno "shift" casuale (così che i posti non siano tutti a partire dal primo posto della fila) 
crea una prenotazione assegnando l'utente corrispondente (utente1, utente2, ..., utente16 per la fila centrale gold)
usa la lista di posti contigui generata
salva la prenotazione <-- calcolando il prezzo tramite la funzione apposita
'''
def crea_prenotazioni():
    oggi = now().date()
    settimana_fine = oggi + timedelta(days=7)

    # Filtra le proiezioni di questa settimana e le vecchie
    proiezioni = Proiezione.objects.filter(   
        data_ora__date__lte=settimana_fine,
    ).select_related('sala')

    for proiezione in proiezioni:
        sala = proiezione.sala
        lista_posti_per_fila = json.loads(sala.posti_per_fila_lista)

        # Calcolo fila centrale zero-based
        num_file = len(lista_posti_per_fila)
        if num_file % 2 == 0:
            fila_centrale = num_file // 2 - 1
        else:
            fila_centrale = num_file // 2

        posti_assegnati = set()

        # Ho quindi  se lista..=[10,10,15] -->  (0,10) (1,10) (2,15)
        for i, posti_fila in enumerate(lista_posti_per_fila):
            # Numero casuale di posti da prenotare in questa fila
            num_posti = random.randint(0, posti_fila)
            if num_posti == 0:
                continue

            # Calcolo shift per spostare la sequenza
            max_shift = posti_fila - num_posti
            shift = random.randint(0, max_shift)

            # Calcolo i posti (contigui) da prenotare, ricordando che i posti sono 1-based e cumulativi sulla sala
            # Quindi se posti  [10,10,15] e sono nella seconda fila con num_posti=2 e shift=1:
            # I posti saranno  10+1+1 ==> dal 12° al 13°   [CORRETTO]
            start_posto = sum(lista_posti_per_fila[:i]) + 1 + shift
            posti_prenotati = list(range(start_posto, start_posto + num_posti))

            # Salta se c'è sovrapposizione con posti già assegnati 
            # Nota che in realtà non possono esserci sovrapposizioni se il funzionamento è quello aspettato
            if any(p in posti_assegnati for p in posti_prenotati):
                print("------ ATTENZIONE: posto già prenotato")
                continue  # salta questa prenotazione, per semplicità
                
            posti_assegnati.update(posti_prenotati)

            # Se fila centrale usa utente gold "utente16" altrimenti utenti "utente1".."utenteN"
            if i == fila_centrale:
                username = 'utente16'  #  #sappiamo essere gold da load_utenti()
            else:
                idx_utente = random.randint(1, 30)  # Assegna casualmente un utente tra 1 e 30
                username = f'utente{idx_utente}'


            try:        #Non dovrebbero esserci problemi
                utente = User.objects.get(username=username)
            except User.DoesNotExist:
                print(f"Utente {username} non trovato, salto prenotazione fila {i}")
                continue

            # Creazione della prenotazione
            prenotazione = Prenotazione(
                utente=utente,
                proiezione=proiezione,
                prezzo= calcola_prezzo(utente,num_posti),
                posti=json.dumps(posti_prenotati),      #Perchè il modello ha un "TextField"
            )
            prenotazione.save()
            print(f"Prenotazione creata per {username} fila {i+1} posti {posti_prenotati} proiezione {proiezione}")


# la funzione Crea/Recupera i gruppi e inserisce nel gruppo i relativi utenti
def crea_assegna_gruppi():
    # Crea (o recupera) i gruppi
    staff_group, _ = Group.objects.get_or_create(name="staff")
    moderatori_group, _ = Group.objects.get_or_create(name="moderatori")

    # Assegna utenti staff1, staff2, ..., staff5 al gruppo staff
    for i in range(1, 6):
        username = f"staff{i}"
        try:
            utente = User.objects.get(username=username)
            utente.groups.add(staff_group)
            print(f"Aggiunto {username} al gruppo 'staff'")
        except User.DoesNotExist:
            print(f"Utente {username} non trovato, salto.")

    # Assegna utenti moderatore1, moderatore2, ..., moderatore5 al gruppo moderatori
    for i in range(1, 6):
        username = f"moderatori{i}"
        try:
            utente = User.objects.get(username=username)
            utente.groups.add(moderatori_group)
        except User.DoesNotExist:
            print(f"Utente {username} non trovato, salto.")

    
            

