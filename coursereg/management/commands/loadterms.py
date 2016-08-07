from django.core.management.base import BaseCommand, CommandError
from coursereg.models import Term
import json
from django.utils import timezone
from datetime import timedelta, datetime

def parse_datetime_str(date_str):
    naive_date_str = ' '.join(date_str.split(' ')[:4])
    offset_str = date_str.split(' ')[4][-5:]
    offset_name = str(date_str.split(' ')[4][:-5])
    naive_dt = datetime.strptime(naive_date_str, '%b %d %Y %H:%M:%S')
    offset = int(offset_str[-4:-2])*60 + int(offset_str[-2:])
    if offset_str[0] == "-":
        offset = -offset
    return naive_dt.replace(tzinfo=timezone.FixedOffset(offset, offset_name))

class Command(BaseCommand):
    help = 'Bulk load term to the database from a JSON file.'

    def add_arguments(self, parser):
        parser.add_argument('--datafile',
            default='coursereg/data/terms.json',
            help='File to load data from (default: coursereg/data/terms.json)')

    def handle(self, *args, **options):
        with open(options['datafile']) as f:
            terms = json.loads(f.read())
            counter = 0
            for term in terms:
                name = term['name']
                if not Term.objects.filter(name=name):
                    Term.objects.create(
                        name=name,
                        is_active=term['is_active'],
                        default_last_reg_date=parse_datetime_str(term['default_last_reg_date']),
                        default_last_adviser_approval_date=parse_datetime_str(term['default_last_adviser_approval_date']),
                        default_last_instructor_approval_date=parse_datetime_str(term['default_last_instructor_approval_date']),
                        default_last_conversion_date=parse_datetime_str(term['default_last_conversion_date']),
                        default_last_drop_date=parse_datetime_str(term['default_last_drop_date']),
                        default_last_drop_with_mention_date=parse_datetime_str(term['default_last_drop_with_mention_date']),
                        default_last_grade_date=parse_datetime_str(term['default_last_grade_date']),
                    )
                    counter += 1
            self.stdout.write(self.style.SUCCESS(
                'Successfully added %s terms to the databse.' % (counter, )
            ))                                                                                
