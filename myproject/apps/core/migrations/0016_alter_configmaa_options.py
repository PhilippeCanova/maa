# Generated by Django 3.2.5 on 2021-09-05 13:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_client_configmaas'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='configmaa',
            options={'ordering': ['station', 'type_maa', 'seuil']},
        ),
    ]
