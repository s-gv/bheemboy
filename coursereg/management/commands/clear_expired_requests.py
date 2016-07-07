from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from datetime import date
from coursereg.models import Participant, User, Notification
from coursereg import maillib

class Command(BaseCommand):
    help = '''Delete enrolment requests past the last registration date that are not approved by adviser/instructor.
    Also sends a notification upon deletion.'''

    def handle(self, *args, **options):
        superuser = User.objects.get(is_superuser=True)
        assert superuser, "No superuser found!"

        expired_participants = Participant.objects.filter(
            Q(is_adviser_approved=False) | Q(is_instructor_approved=False),
            course__last_reg_date__lt=date.today(), participant_type=Participant.PARTICIPANT_STUDENT)

        count = 0
        should_send_mail = True
        for participant in expired_participants:
            msg = 'Cancelled application for %s because the last registration date has passed.' % participant.course
            Notification.objects.create(
                user=participant.user,
                origin=Notification.ORIGIN_OTHER,
                message=msg,
            )
            if should_send_mail:
                should_send_mail = maillib.send_email(superuser.email, [participant.user.email], 'Coursereg notification', msg)
            participant.delete()
            count += 1

        self.stdout.write(self.style.SUCCESS(
            'Cleared %s expired enrolment applications.' % count
        )) 
