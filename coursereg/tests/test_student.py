import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Participant
from utils import is_error_msg_present

class StudentTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        cls.course_tomorrow = Course.objects.create(num='E0-232', title='Course Name', department=dept, last_reg_date=tomorrow)
        cls.course_yesterday = Course.objects.create(num='E0-211', title='Noname', department=dept, last_reg_date=yesterday)

    def setUp(self):
        self.client = Client()

    def test_was_course_with_last_reg_date_in_future_shown(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:index'), follow=True)
        self.assertTrue(self.course_tomorrow in response.context['courses'])

    def test_was_course_with_last_reg_date_in_past_not_shown(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.get(reverse('coursereg:index'), follow=True)
        self.assertFalse(self.course_yesterday in response.context['courses'])

    def test_was_course_added(self):
        self.client.login(email='ben@test.com', password='ben12345')
        response = self.client.post(reverse('coursereg:participants_create'),
            {'course_id': self.course_tomorrow.id, 'reg_type': 'credit', 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.assertTrue(any([p[4] == self.course_tomorrow for p in response.context['participants']]))

    def test_was_course_removed(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_tomorrow,
            participant_type=Participant.PARTICIPANT_STUDENT, state=Participant.STATE_CREDIT, grade=Participant.GRADE_NA,
            is_adviser_approved=False, is_instructor_approved=False)
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertFalse(Participant.objects.filter(user=self.ben, course=self.course_tomorrow))

    def test_was_student_not_able_to_delete_course_after_adviser_approval(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_tomorrow,
            participant_type=Participant.PARTICIPANT_STUDENT, state=Participant.STATE_CREDIT, grade=Participant.GRADE_NA,
            is_adviser_approved=True, is_instructor_approved=True)
        self.client.login(email='ben@test.com', password='ben12345')
        with self.assertRaises(AssertionError) as context:
            self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_tomorrow))

    def test_was_student_not_able_to_delete_approved_course_after_last_reg_date(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, state=Participant.STATE_CREDIT, grade=Participant.GRADE_NA,
            is_adviser_approved=True, is_instructor_approved=True)
        self.client.login(email='ben@test.com', password='ben12345')
        with self.assertRaises(AssertionError) as context:
            self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday))

    def test_could_student_delete_graded_course(self):
        participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, state=Participant.STATE_CREDIT, grade=Participant.GRADE_S,
            is_adviser_approved=True, is_instructor_approved=True)
        self.client.login(email='ben@test.com', password='ben12345')
        with self.assertRaises(AssertionError) as context:
            self.client.post(reverse('coursereg:participants_delete', args=[participant.id]), follow=True)
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday))