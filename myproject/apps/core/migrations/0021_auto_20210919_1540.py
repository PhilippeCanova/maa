# Generated by Django 3.2.5 on 2021-09-19 15:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0020_auto_20210919_1526'),
    ]

    operations = [
        migrations.AlterField(
            model_name='logs',
            name='code',
            field=models.CharField(default='0000', max_length=8),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='logs',
            name='heure',
            field=models.DateTimeField(auto_now=True),
        ),
    ]