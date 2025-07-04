from django.test import TestCase,Client
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from datetime import timedelta
from film.models import Film, Sala, Proiezione
import json
from django.contrib.auth.models import User,Group
import json
from film.models import Film, Sala, Proiezione
from prenotazioni.models import Prenotazione
from utenti.models import Rating  
from film.utils import get_raccomandazioni_utente
from django.urls import reverse
from datetime import datetime
from django.utils import timezone





#Per ogni TestCase viene generato un DB temporaneo!
class ProiezioneCollisionTest(TestCase):

    #Creo un 1° film da 60m che avrà proiezione alle 7 e la rispettiva sala
    def setUp(self):
        # Film da 60 minuti
        self.film = Film.objects.create(
            titolo="Test Movie",
            trama="Una trama qualunque",
            cast="Attore A, Attrice B",
            durata=60,
            genere="Drammatico"
        )

        # Sala con 3 file da 10 posti (tot: 30)
        self.sala = Sala.objects.create(
            nome="Sala 1",
            numero_posti=30,
            posti_per_fila_lista=json.dumps([10, 10, 10])
        )

        # Orario base: oggi alle 17:00
        self.orario_base = now().replace(hour=17, minute=0, second=0, microsecond=0)

        # Proiezione originale dalle 17:00 alle 18:00
        self.proiezione1 = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=self.orario_base
        )

    #Testo che avvenga intercettato il conflitto
    def test_proiezione_conflitto_alle_17_01(self):
        nuova_ora = self.orario_base + timedelta(minutes=1)
        proiezione_conflict = Proiezione(
            film=self.film,
            sala=self.sala,
            data_ora=nuova_ora
        )
        with self.assertRaises(ValidationError):
            proiezione_conflict.save()

    # Qui deve ancora intercettare il conflitto
    def test_proiezione_conflitto_alle_17_30(self):
        nuova_ora = self.orario_base + timedelta(minutes=30)
        proiezione_conflict = Proiezione(
            film=self.film,
            sala=self.sala,
            data_ora=nuova_ora
        )
        with self.assertRaises(ValidationError):
            proiezione_conflict.save()

    def test_proiezione_valida_alle_18_05(self):
        nuova_ora = self.orario_base + timedelta(minutes=65)
        proiezione_valida = Proiezione(
            film=self.film,
            sala=self.sala,
            data_ora=nuova_ora
        )
        try:
            proiezione_valida.save()  # non deve lanciare eccezioni
        except ValidationError:
            self.fail("La proiezione NON dovrebbe causare conflitto.")

    # Film da 90 minuti alle 16:00 → conflitto con proiezione delle 17:00
    def test_film_lungo_alle_16_causa_conflitto(self):
        film_lungo = Film.objects.create(
            titolo="Film Lungo",
            trama="Lungo e noioso",
            cast="Attore X",
            durata=90,
            genere="Thriller"
        )
        nuova_ora = self.orario_base - timedelta(minutes=60)  # ore 16:00
        proiezione_conflict = Proiezione(
            film=film_lungo,
            sala=self.sala,
            data_ora=nuova_ora
        )
        with self.assertRaises(ValidationError):
            proiezione_conflict.save()

    # Film da 59 minuti alle 16:00 → NON causa conflitto con la proiezione delle 17:00
    def test_film_corto_alle_16_valido(self):
        film_corto = Film.objects.create(
            titolo="Film Corto",
            trama="Breve ma intenso",
            cast="Attrice Y",
            durata=59,
            genere="Commedia"
        )
        nuova_ora = self.orario_base - timedelta(minutes=60)  # ore 16:00
        proiezione_valida = Proiezione(
            film=film_corto,
            sala=self.sala,
            data_ora=nuova_ora
        )
        try:
            proiezione_valida.save()  # Non dovrebbe sollevare eccezioni
        except ValidationError:
            self.fail("La proiezione da 59 minuti alle 16:00 NON dovrebbe causare conflitto.")





# TestCase per il sistema di Raccomandazione
class RaccomandazioneTest(TestCase):

    # Utente1 e Utente guardano film_A
    # Utente2 guarda film_b
    def setUp(self):
        # Crea utenti
        self.utente1 = User.objects.create_user(username='utente1', password='test123')
        self.utente2 = User.objects.create_user(username='utente2', password='test456')

        # Film
        self.film_a = Film.objects.create(titolo="Film A", durata=100, trama="...", cast="...", genere="Drama")
        self.film_b = Film.objects.create(titolo="Film B", durata=120, trama="...", cast="...", genere="Action")

        # Sala
        self.sala = Sala.objects.create(nome="Sala 1", numero_posti=30, posti_per_fila_lista=json.dumps([10, 10,10]))

        # Proiezioni già avvenute (film visti)
        self.proiezione_a = Proiezione.objects.create(
            film=self.film_a,
            sala=self.sala,
            data_ora=now() - timedelta(days=5)
        )
        self.proiezione_b = Proiezione.objects.create(
            film=self.film_b,
            sala=self.sala,
            data_ora=now() - timedelta(days=3)
        )

        # Prenotazioni (film visti)
        Prenotazione.objects.create(
            utente=self.utente1,
            proiezione=self.proiezione_a,
            prezzo=8.00,
            posti=json.dumps([1])
        )

        Prenotazione.objects.create(
            utente=self.utente2,
            proiezione=self.proiezione_a,
            prezzo=8.00,
            posti=json.dumps([2])
        )

        Prenotazione.objects.create(
            utente=self.utente2,
            proiezione=self.proiezione_b,
            prezzo=8.00,
            posti=json.dumps([3])
        )

        # Rating (solo utente2 vota B con voto 3 => peso 1)
        Rating.objects.create(utente=self.utente2, film=self.film_b, voto=3)

    # Ci aspettiamo raccomando solo un film e sia film_b
    def test_raccomandazione_base(self):
        raccomandati = get_raccomandazioni_utente(self.utente1, top_n=5, ora_al_cinema=False)
        self.assertIn(self.film_b, raccomandati)
        self.assertEqual(len(raccomandati), 1)


    def test_raccomandazione_utente1_rafforzata_da_utente3(self):
        # utente3 guarda anche film_a, film_b, film_c --> dovrebbe raccomandare film_b per primo
        film_c = Film.objects.create(titolo="Film C", durata=90, trama="...", cast="...", genere="Sci-Fi")

        proiezione_c = Proiezione.objects.create(
            film=film_c,
            sala=self.sala,
            data_ora=now() - timedelta(days=2)
        )

        utente3 = User.objects.create_user(username='utente3', password='pass3')

        # Film A (già esistente)
        Prenotazione.objects.create(
            utente=utente3,
            proiezione=self.proiezione_a,
            prezzo=8.0,
            posti=json.dumps([4])
        )
        # Film B (già esistente)
        Prenotazione.objects.create(
            utente=utente3,
            proiezione=self.proiezione_b,
            prezzo=8.0,
            posti=json.dumps([5])
        )
        # Film C
        Prenotazione.objects.create(
            utente=utente3,
            proiezione=proiezione_c,
            prezzo=8.0,
            posti=json.dumps([6])
        )

        raccomandati = get_raccomandazioni_utente(self.utente1)

        self.assertIn(self.film_b, raccomandati)
        self.assertEqual(raccomandati[0], self.film_b)



    def test_nessuna_raccomandazione_senza_film_in_comune(self):
        # utente3 guarda solo film C --> mi aspetto non venga raccomandato nulla per lui (nessun film in comune con utente1/2)
        film_c = Film.objects.create(titolo="Film C", durata=90, trama="...", cast="...", genere="Sci-Fi")

        proiezione_c = Proiezione.objects.create(
            film=film_c,
            sala=self.sala,
            data_ora=now() - timedelta(days=1)
        )

        utente3 = User.objects.create_user(username='utente3_soloC', password='pass3')

        Prenotazione.objects.create(
            utente=utente3,
            proiezione=proiezione_c,
            prezzo=8.0,
            posti=json.dumps([1])
        )

        raccomandazioni = get_raccomandazioni_utente(utente3,debug=True)
        self.assertEqual(len(raccomandazioni), 0)



# Classe di test per i metodi CRUD sui Film
# I test sul CRUD tramite view devono simulare un Client (per altro con permessi!) e sfruttare il
# metodo post che utilizza la view
class FilmCRUDViewTests(TestCase):

    def setUp(self):        #Creo l'utente staff aggiungendolo al gruppo
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staff', password='pass123', is_staff=True)

        # Assicurati che esista il gruppo "staff"
        staff_group, _ = Group.objects.get_or_create(name='staff')
        self.staff_user.groups.add(staff_group)

        self.client.login(username='staff', password='pass123')

    #Test del funzionamento della view che crea un film
    def test_creazione_film(self):
        url = reverse('film:film_create')  
        data = {
            'titolo': 'Nuovo Film',
            'trama': 'Trama interessante',
            'cast': 'Attore1, Attrice2',
            'durata': 120,
            'genere': 'Azione'
        }
        response = self.client.post(url, data)
        print("RESPONSE STATUS:", response.status_code)
        print("REDIRECT TO:", response.url if response.status_code == 302 else "No redirect")

        self.assertEqual(response.status_code, 302)  # redirect dopo il successo
        self.assertEqual(Film.objects.count(), 1)          #Si aspetta che il db abbia questo film
        self.assertEqual(Film.objects.first().titolo, 'Nuovo Film')

    #Test della updateView
    def test_modifica_film(self):
        film = Film.objects.create(titolo='Vecchio Titolo', durata=100, trama='...', cast='...', genere='Commedia')
        url = reverse('film:film_update', args=[film.pk])  
        response = self.client.post(url, {
            'titolo': 'Titolo Modificato',
            'durata': 90,
            'trama': film.trama,
            'cast': film.cast,
            'genere': film.genere
        })
        self.assertEqual(response.status_code, 302)     #redirect
        film.refresh_from_db()
        self.assertEqual(film.titolo, 'Titolo Modificato')  #Si aspetta il nuovo titolo

    #Test della deleteView
    def test_cancellazione_film(self):
        film = Film.objects.create(titolo='Da Eliminare', durata=80, trama='...', cast='...', genere='Dramma')
        url = reverse('film:film_delete', args=[film.pk]) 
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Film.objects.filter(pk=film.pk).exists())  #Mi aspetto NON esisti più

    #Test della ListView
    def test_lista_film_modifica_view(self):
        Film.objects.create(titolo='A Film', durata=90, trama='...', cast='...', genere='Azione')
        Film.objects.create(titolo='B Film', durata=100, trama='...', cast='...', genere='Commedia')
        url = reverse('film:film_list_modifica')  
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A Film')         #Mi aspetto contenga i due film
        self.assertContains(response, 'B Film')
        
        # TEST: Accesso negato a film_create per utente NON staff
    def test_accesso_negato_create_film_utente_non_staff(self):
        self.client.logout()
        user = User.objects.create_user(username='user', password='pass123')
        self.client.login(username='user', password='pass123')

        url = reverse('film:film_create')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    # TEST: Accesso negato a film_update per utente NON staff
    def test_accesso_negato_update_film_utente_non_staff(self):
        film = Film.objects.create(titolo='Film Originale', durata=120, trama='Trama', cast='Cast', genere='Azione')

        self.client.logout()
        user = User.objects.create_user(username='user2', password='pass123')
        self.client.login(username='user2', password='pass123')

        url = reverse('film:film_update', args=[film.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    # TEST: Accesso negato a film_delete per utente NON staff
    def test_accesso_negato_delete_film_utente_non_staff(self):
        film = Film.objects.create(titolo='Film da Eliminare', durata=100, trama='Trama', cast='Cast', genere='Dramma')

        self.client.logout()
        user = User.objects.create_user(username='user3', password='pass123')
        self.client.login(username='user3', password='pass123')

        url = reverse('film:film_delete', args=[film.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    # TEST: Accesso negato a film_list_modifica per utente NON staff
    def test_accesso_negato_lista_film_modifica_view_utente_non_staff(self):
        self.client.logout()
        user = User.objects.create_user(username='user4', password='pass123')
        self.client.login(username='user4', password='pass123')

        url = reverse('film:film_list_modifica')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")




# Analogamente la classe di test per le Proiezioni

class ProiezioneCRUDViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.staff_user = User.objects.create_user(username='staff', password='pass123', is_staff=True)

        # Aggiungo l'utente al gruppo 'staff'
        staff_group, _ = Group.objects.get_or_create(name='staff')
        self.staff_user.groups.add(staff_group)

        self.client.login(username='staff', password='pass123')

        # Creo un film e una sala per i test
        self.film = Film.objects.create(
            titolo='Film di Test',
            trama='Una trama interessante',
            cast='Attore Uno, Attrice Due',
            durata=100,
            genere='Azione'
        )
        self.sala = Sala.objects.create(
            nome='Sala Test',
            numero_posti=50,
            posti_per_fila_lista='[10, 10, 10, 10, 10]'
        )

    def test_creazione_proiezione(self):
        url = reverse('film:proiezione_create')
        data = {
            'film': self.film.id,
            'sala': self.sala.id,
            'data_ora': timezone.make_aware(datetime.now() + timedelta(days=1))
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Proiezione.objects.count(), 1)     #controllo che sia stata creata e che sia lei
        self.assertEqual(Proiezione.objects.first().film, self.film)

    def test_modifica_proiezione(self):
        proiezione = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.make_aware(datetime.now() + timedelta(days=2))
        )
        url = reverse('film:proiezione_update', args=[proiezione.pk])
        nuova_data = timezone.make_aware(datetime.now() + timedelta(days=3))
        response = self.client.post(url, {
            'film': self.film.id,
            'sala': self.sala.id,
            'data_ora': nuova_data
        })
        self.assertEqual(response.status_code, 302)
        proiezione.refresh_from_db()            #controllo sia stata aggiornata la data
        self.assertEqual(
            proiezione.data_ora.replace(microsecond=0),
            nuova_data.replace(microsecond=0)
        )

    def test_cancellazione_proiezione(self):
        proiezione = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.make_aware(datetime.now() + timedelta(days=4))
        )
        url = reverse('film:proiezione_delete', args=[proiezione.pk])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)                 #controllo non esista più
        self.assertFalse(Proiezione.objects.filter(pk=proiezione.pk).exists())

    #Controllo funzionamento della listView
    def test_lista_proiezioni_modifica_view(self):
        Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.make_aware(datetime.now() + timedelta(days=1))
        )
        url = reverse('film:proiezione_list_modifica')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.film.titolo)


        # Verifico che un utente NON staff venga rediretto al login quando tenta di accedere alle view CRUD
    def test_accesso_negato_create_view_per_utente_non_staff(self):
        self.client.logout()
        user = User.objects.create_user(username='user', password='pass123')
        self.client.login(username='user', password='pass123')

        url = reverse('film:proiezione_create')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")  #Rediretto al login

    def test_accesso_negato_update_view_per_utente_non_staff(self):
        proiezione = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.make_aware(datetime.now() + timedelta(days=1))
        )

        self.client.logout()
        user = User.objects.create_user(username='user2', password='pass123')
        self.client.login(username='user2', password='pass123')

        url = reverse('film:proiezione_update', args=[proiezione.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")  #Rediretto al login

    def test_accesso_negato_delete_view_per_utente_non_staff(self):
        proiezione = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=timezone.make_aware(datetime.now() + timedelta(days=1))
        )

        self.client.logout()
        user = User.objects.create_user(username='user3', password='pass123')
        self.client.login(username='user3', password='pass123')

        url = reverse('film:proiezione_delete', args=[proiezione.pk])
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")  #Rediretto al login

    def test_accesso_negato_lista_view_per_utente_non_staff(self):
        self.client.logout()
        user = User.objects.create_user(username='user4', password='pass123')
        self.client.login(username='user4', password='pass123')

        url = reverse('film:proiezione_list_modifica')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")  #Rediretto al login
