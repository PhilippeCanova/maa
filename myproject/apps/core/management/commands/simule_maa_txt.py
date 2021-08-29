from pathlib import Path
import datetime
import json
import requests

from django.core.management.base import BaseCommand, CommandError
from django.urls import reverse

            

class Command(BaseCommand):
    help = "Simule l'envoi d'un fichier maa.txt"

    """def add_arguments(self, parser):
        parser.add_argument('poll_ids', nargs='+', type=int)
    """

    """
    def handle(self, *args, **options):
        for poll_id in options['poll_ids']:
            try:
                poll = Poll.objects.get(pk=poll_id)
            except Poll.DoesNotExist:
                raise CommandError('Poll "%s" does not exist' % poll_id)

            poll.opened = False
            poll.save()

            self.stdout.write(self.style.SUCCESS('Successfully closed poll "%s"' % poll_id))
            """
    
    def handle(self, *args, **options):
        payload = {'param1':1, 'param2':2}
        r = requests.post(reverse('incoming_maa_txt'), data=json.dumps(payload))
        print(r)
