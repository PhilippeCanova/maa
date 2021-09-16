# Generated by Django 3.2.5 on 2021-08-29 06:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_alter_configmaa_type_maa'),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nom', models.CharField(max_length=250)),
                ('prenom', models.CharField(blank=True, max_length=250, null=True)),
                ('telephone', models.CharField(max_length=15)),
                ('email', models.EmailField(blank=True, max_length=15, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='context_CDPH',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='context_CDPQ',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='context_TAF',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='log',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='message_mail',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='message_pdf',
            field=models.FileField(blank=True, null=True, upload_to='uploads/%Y/%m/%d/'),
        ),
        migrations.AlterField(
            model_name='envoimaa',
            name='message_sms',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='MediumSMS',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sms', models.CharField(max_length=15)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.client')),
            ],
        ),
        migrations.CreateModel(
            name='MediumMail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.client')),
            ],
        ),
        migrations.CreateModel(
            name='MediumFTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('remote', models.CharField(max_length=254)),
                ('login', models.CharField(max_length=254)),
                ('pwd', models.CharField(max_length=254)),
                ('dir', models.CharField(blank=True, max_length=254, null=True)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.client')),
            ],
        ),
    ]
