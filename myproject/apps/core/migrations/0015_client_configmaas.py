# Generated by Django 3.2.5 on 2021-09-05 13:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_auto_20210905_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='configmaas',
            field=models.ManyToManyField(to='core.ConfigMAA'),
        ),
    ]