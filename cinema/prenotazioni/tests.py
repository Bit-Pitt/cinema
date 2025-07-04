from django.test import TestCase,Client
from django.contrib.auth.models import User,Group
from django.utils.timezone import now
from datetime import timedelta
from film.models import *
from .models import Prenotazione
import json
from django.core.exceptions import ValidationError
from django.urls import reverse


# Suite di test sulle Prenotazioni
class PrenotazioniTest(TestCase):

    def setUp(self):        # Nel setUp utente1 prenota i posti 1-2
        # Crea due utenti 
        self.utente1 = User.objects.create_user(username='utente1', password='password1')
        self.utente2 = User.objects.create_user(username='utente2', password='password2')

        # Film da 90 minuti
        self.film = Film.objects.create(
            titolo="Il film test",
            durata=90,
            trama="Trama di prova",
            cast="Cast finto",
            genere="Fantascienza"
        )

        # Sala da 3 file da 4 posti = 12 posti totali
        self.sala = Sala.objects.create(
            nome="Sala Gold",
            numero_posti=12,
            posti_per_fila_lista=json.dumps([4, 4, 4])
        )

        # Proiezione tra 2 giorni (valida per i test di settimana)
        self.proiezione = Proiezione.objects.create(
            film=self.film,
            sala=self.sala,
            data_ora=now() + timedelta(days=2)
        )

        # Prenotazione iniziale valida di utente1 sui posti 1, 2
        self.prenotazione1 = Prenotazione.objects.create(
            utente=self.utente1,
            proiezione=self.proiezione,
            prezzo=20.00,
            posti=json.dumps([1, 2])
        )

    def test_prenotazione_senza_posti(self):
        pren = Prenotazione(
            utente=self.utente1,
            proiezione=self.proiezione,
            prezzo=8.00,
            posti=json.dumps([])
        )
        with self.assertRaises(ValidationError):
            pren.save()

    def test_prenotazione_con_posto_inesistente(self):
        pren = Prenotazione(
            utente=self.utente1,
            proiezione=self.proiezione,
            prezzo=8.00,
            posti=json.dumps([99])  # posto fuori range
        )
        with self.assertRaises(ValidationError):
            pren.save()

    def test_prenotazione_posti_non_contigui(self):
        pren = Prenotazione(
            utente=self.utente1,
            proiezione=self.proiezione,
            prezzo=8.00,
            posti=json.dumps([3, 5])  # non contigui
        )
        with self.assertRaises(ValidationError):
            pren.save()

    def test_prenotazione_posti_gold_senza_permesso(self):
        # Supponiamo che validate_posti_gold dia errore su posti 1-4 (prima fila)
        pren = Prenotazione(
            utente=self.utente1,
            proiezione=self.proiezione,
            prezzo=20.00,
            posti=json.dumps([5, 6])  # fila centrale --> posti [5,6,7,8]
        )
        with self.assertRaises(ValidationError):
            pren.save()

    def test_due_utenti_stesso_posto(self):
        # Posto 2 già prenotato da utente1
        pren = Prenotazione(
            utente=self.utente2,
            proiezione=self.proiezione,
            prezzo=10.00,
            posti=json.dumps([2])
        )
        with self.assertRaises(ValidationError):
            pren.save()

    #Controllo la possibilità di un utente loggato di prenotare (e che venga salvato correttamente)
    # e la impossibilità di un utente NON loggato di NON prenotare

    # UTENTE LOGGATO può creare una prenotazione
    def test_creazione_prenotazione_utente_loggato(self):
        self.client.login(username='utente1', password='password1')

        url = reverse('prenotazioni:crea-prenotazione', args=[self.proiezione.pk])
        data = {
            'posti': json.dumps([3, 4]),  
            'prezzo': 16.00
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # redirect dopo il successo
        self.assertEqual(Prenotazione.objects.filter(utente=self.utente1).count(), 2)  # incluso quello già presente
        self.assertTrue(Prenotazione.objects.filter(posti='[3, 4]').exists())

    # UTENTE NON LOGGATO viene reindirizzato al login
    def test_accesso_negato_prenotazione_utente_non_autenticato(self):
        url = reverse('prenotazioni:crea-prenotazione', args=[self.proiezione.pk])
        data = {
            'posti': json.dumps([9, 10]),
            'prezzo': 12.00
        }

        response = self.client.post(url, data)
        expected_login_url = f"/accounts/login/?next={url}"
        self.assertRedirects(response, expected_login_url)
        self.assertFalse(Prenotazione.objects.filter(posti='[9, 10]').exists())



#controlliamo le view per lo staff, e che sia correttamente protetta
class PrenotazioniStaffAccessTests(TestCase):
    
    def setUp(self):
        self.client = Client()

        # Creo un film, sala e proiezione per la prenotazione
        self.film = Film.objects.create(titolo="Test Film", durata=90, trama="...", cast="...", genere="Azione")
        self.sala = Sala.objects.create(nome="Test Sala", numero_posti=30, posti_per_fila_lista=json.dumps([10,10,10]))
        self.proiezione = Proiezione.objects.create(film=self.film, sala=self.sala, data_ora=now() + timedelta(days=1))

        # Utente staff
        self.staff_user = User.objects.create_user(username='staff', password='pass123', is_staff=True)
        staff_group, _ = Group.objects.get_or_create(name='staff')
        self.staff_user.groups.add(staff_group)

        # Utente normale
        self.normal_user = User.objects.create_user(username='user', password='pass123', is_staff=False)

        # Prenotazione per l’utente normale
        self.prenotazione = Prenotazione.objects.create(
            utente=self.normal_user,
            proiezione=self.proiezione,
            prezzo=10.0,
            posti=json.dumps([1, 2])
        )

    #Controllo sulla detailView
    def test_lista_prenotazioni_accesso_staff(self):
        self.client.login(username='staff', password='pass123')
        url = reverse('prenotazioni:prenotazione_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.prenotazione, response.context['prenotazioni'])

    #Controlla la detailView non sia accessibile
    def test_lista_prenotazioni_accesso_non_staff(self):
        self.client.login(username='user', password='pass123')
        url = reverse('prenotazioni:prenotazione_list')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    #CI si aspetta stesso comportamento rispetto a sopra
    def test_lista_prenotazioni_accesso_anonimo(self):
        self.client.logout()
        url = reverse('prenotazioni:prenotazione_list')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_elimina_prenotazione_staff(self):
        self.client.login(username='staff', password='pass123')
        url = reverse('prenotazioni:prenotazione_delete', args=[self.prenotazione.pk])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('prenotazioni:prenotazione_list'))
        self.assertFalse(Prenotazione.objects.filter(pk=self.prenotazione.pk).exists()) #Non deve più esistere

    def test_elimina_prenotazione_non_staff(self):
        self.client.login(username='user', password='pass123')
        url = reverse('prenotazioni:prenotazione_delete', args=[self.prenotazione.pk])
        response = self.client.post(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")  # Non dovrebbe permettere l'accesso
        self.assertTrue(Prenotazione.objects.filter(pk=self.prenotazione.pk).exists())

    def test_elimina_prenotazione_anonimo(self):
        self.client.logout()
        url = reverse('prenotazioni:prenotazione_delete', args=[self.prenotazione.pk])
        response = self.client.post(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
        self.assertTrue(Prenotazione.objects.filter(pk=self.prenotazione.pk).exists())




