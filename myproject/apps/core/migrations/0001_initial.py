# Generated by Django 3.2.5 on 2021-08-22 07:10

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Region',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tag', models.TextField(max_length=10, unique=True, verbose_name='Tag région')),
            ],
        ),
        migrations.CreateModel(
            name='Station',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('oaci', models.CharField(max_length=4, unique=True, verbose_name='Code OACI')),
                ('nom', models.CharField(max_length=124, verbose_name='Nom')),
                ('entete', models.CharField(max_length=11, verbose_name='Entete')),
                ('date_pivot', models.DateTimeField(verbose_name="Date changement d'heure")),
                ('ouverture', models.TimeField(verbose_name='H ouverture')),
                ('ouverture1', models.TimeField(verbose_name='H ouverture avant pivot')),
                ('ouverture2', models.TimeField(verbose_name='H ouverture après pivot')),
                ('fermeture', models.TimeField(verbose_name='H fermeture')),
                ('fermeture1', models.TimeField(verbose_name='H fermeture avant pivot')),
                ('fermeture2', models.TimeField(verbose_name='H fermeture après pivot')),
                ('retention', models.IntegerField()),
                ('reconduction', models.IntegerField()),
                ('repousse', models.IntegerField()),
                ('fuseau', models.CharField(max_length=124)),
                ('wind_unit', models.CharField(choices=[('kt', 'kt'), ('kmh', 'km/h')], max_length=3, verbose_name='Unité de vitesse')),
                ('temp_unit', models.CharField(choices=[('c', '°C'), ('f', 'F')], max_length=3, verbose_name='Unité de température')),
                ('region', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.region', verbose_name='Dir')),
            ],
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='core.region')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]