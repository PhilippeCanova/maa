# Generated by Django 3.2.5 on 2021-12-08 07:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('configurateur', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvoiMAA',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_envoi', models.DateTimeField()),
                ('date_debut', models.DateTimeField()),
                ('date_fin', models.DateTimeField()),
                ('numero', models.IntegerField()),
                ('message', models.TextField()),
                ('entete_transmet', models.TextField(null=True)),
                ('fcst', models.CharField(default='FCST', max_length=20)),
                ('at', models.DateTimeField(blank=True, null=True)),
                ('status', models.CharField(choices=[('to_create', 'A créer'), ('to_send', 'A envoyer'), ('ok', 'Envoyé')], default='new', max_length=10)),
                ('context_TAF', models.TextField(blank=True, null=True)),
                ('context_CDPH', models.TextField(blank=True, null=True)),
                ('context_CDPQ', models.TextField(blank=True, null=True)),
                ('description_maa', models.TextField(blank=True, null=True)),
                ('log', models.TextField(blank=True, null=True)),
                ('message_mail', models.TextField(blank=True, null=True)),
                ('message_pdf', models.FileField(blank=True, null=True, upload_to='uploads/%Y/%m/%d/')),
                ('message_sms', models.TextField(blank=True, null=True)),
                ('num_groupe', models.IntegerField(default=1)),
                ('total_groupe', models.IntegerField(default=1)),
                ('cancel', models.BooleanField(default=False)),
                ('data_vent', models.TextField(blank=True, null=True)),
                ('data_tempe', models.TextField(blank=True, null=True)),
                ('configmaa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maa_emis', to='configurateur.configmaa')),
            ],
        ),
    ]
