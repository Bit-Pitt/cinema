from django.test import TestCase, Client
from django.contrib.auth.models import User,Group
from django.urls import reverse
from django.utils.timezone import now
from utenti.models import ProfiloUtente, Commento, Discussione, Messaggio
from film.models import Film

class ModerazioneViewTests(TestCase):
    def setUp(self):
        self.client = Client()

       # Crea utenti
        self.moderatore = User.objects.create_user(username='mod', password='pass123')
        self.utente_normale = User.objects.create_user(username='utente', password='pass123')

        # Ottieni i profili già creati e assegna il ruolo moderatore
        profilo_mod = ProfiloUtente.objects.get(user=self.moderatore)
        profilo_mod.is_moderatore = True
        profilo_mod.save()

        # Aggiungo l'utente al gruppo 'moderatori'
        staff_group, _ = Group.objects.get_or_create(name='moderatori')
        self.moderatore.groups.add(staff_group)

        # Crea film, commento, discussione, messaggio
        self.film = Film.objects.create(titolo='Film Test', durata=120, trama='Trama', cast='Cast', genere='Azione')
        self.commento = Commento.objects.create(
            utente=self.utente_normale, film=self.film,
            testo='Ottimo film!', data_commento=now()
        )
        self.discussione = Discussione.objects.create(
            titolo='Discussione test', utente=self.utente_normale,
            data_creazione=now(), ultimo_messaggio_data=now()
        )
        self.messaggio = Messaggio.objects.create(
            discussione=self.discussione, utente=self.utente_normale,
            contenuto='Messaggio di test', data_invio=now()
        )

    # -------------------------
    # TEST ACCESSO MODERATORE
    # -------------------------
    def test_accesso_lista_commenti_moderatore(self):
        self.client.login(username='mod', password='pass123')
        url = reverse('utenti:seleziona_film')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_accesso_commenti_per_film_moderatore(self):
        self.client.login(username='mod', password='pass123')
        url = reverse('utenti:commenti_per_film', args=[self.film.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.commento.testo)

    def test_accesso_lista_discussioni_moderatore(self):
        self.client.login(username='mod', password='pass123')
        url = reverse('utenti:lista_discussioni_mod')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.discussione.titolo)

    def test_accesso_messaggi_della_discussione_moderatore(self):
        self.client.login(username='mod', password='pass123')
        url = reverse('utenti:messaggi_per_discussione', args=[self.discussione.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.messaggio.contenuto)

    # -------------------------
    # TEST DELETE VIEW
    # -------------------------

    def test_elimina_discussione_moderatore(self):
        self.client.login(username='mod', password='pass123')
        url = reverse('utenti:discussione_delete', args=[self.discussione.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('utenti:lista_discussioni_mod'))
        self.assertFalse(Discussione.objects.filter(id=self.discussione.id).exists())

    def test_elimina_messaggio_moderatore(self):
        self.client.login(username='mod', password='pass123')
        url = reverse('utenti:messaggio_delete', args=[self.messaggio.id])
        response = self.client.post(url)
        self.assertRedirects(response, reverse('utenti:messaggi_per_discussione', args=[self.discussione.id]))
        self.assertFalse(Messaggio.objects.filter(id=self.messaggio.id).exists())

    # -------------------------
    # ACCESSO NEGATO (NON MODERATORI)
    # -------------------------
    def test_accesso_negato_non_moderatore(self):
        self.client.login(username='utente', password='pass123')
        url = reverse('utenti:seleziona_film')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_accesso_negato_anonimo(self):
        url = reverse('utenti:seleziona_film')
        response = self.client.get(url)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
