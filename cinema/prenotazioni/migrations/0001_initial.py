# Generated by Django 5.2.3 on 2025-07-01 15:56

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('film', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Prenotazione',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_acquisto', models.DateTimeField(auto_now_add=True)),
                ('prezzo', models.DecimalField(decimal_places=2, max_digits=7)),
                ('posti', models.TextField(help_text='Lista JSON di posti, es: [1, 2, 5]')),
                ('proiezione', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prenotazioni', to='film.proiezione')),
                ('utente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='prenotazioni', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
