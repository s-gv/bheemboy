import datetime
from django.test import TestCase
from django.test import Client
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Participant, Grade, Term, RegistrationType
from utils import is_error_msg_present
import logging

class AdviserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        cls.charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        cls.ben = User.objects.create_user(email='ben@test.com', password='ben12345', user_type=User.USER_TYPE_STUDENT, adviser=cls.charles)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        aug_term = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=tomorrow,
            last_adviser_approval_date=tomorrow,
            last_instructor_approval_date=tomorrow,
            last_conversion_date=tomorrow,
            last_drop_date=tomorrow,
            last_grade_date=tomorrow
        )
        aug_term_expired = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=yesterday,
            last_cancellation_date=yesterday,
            last_adviser_approval_date=yesterday,
            last_instructor_approval_date=yesterday,
            last_conversion_date=yesterday,
            last_drop_date=yesterday,
            last_grade_date=yesterday
        )
        cls.s_grade = Grade.objects.create(name="S grade", points=7.5, should_count_towards_cgpa=True)
        cls.course = Course.objects.create(num='E0-111', title='Course Name1', department=dept, term=aug_term)
        cls.course_yesterday = Course.objects.create(num='E0-123', title='Course Name A', department=dept, term=aug_term_expired)
        cls.course2 = Course.objects.create(num='E1-222', title='Course Name2', department=dept, term=aug_term)
        cls.course3 = Course.objects.create(num='E2-333', title='Course Name3', department=dept, term=aug_term)
	cls.credit = RegistrationType.objects.create(name='Credit',should_count_towards_cgpa=True,is_active=True)
	cls.audit = RegistrationType.objects.create(name='Audit',should_count_towards_cgpa=False,is_active=True)
	cls.nonrtp = RegistrationType.objects.create(name='NonRTP',should_count_towards_cgpa=False,is_active=True)
	
    def setUp(self):
        self.client = Client()
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_1_adviser_review(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'review', 'origin': 'adviser'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course,is_adviser_reviewed = True))
		
    def test_2_adviser_new_badge_alert_for_new_request(self):
        self.client.login(email='ben@test.com', password='ben12345')
        self.client.post(reverse('coursereg:participants_create'),
                {'course_id': self.course.id, 'reg_type': 1, 'user_id': self.ben.id, 'origin': 'student'}, follow=True)
        self.client.login(email='charles@test.com', password='charles12345')
        self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, is_adviser_reviewed=False))
		
    def test_3_adviser_switch_audit(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'reg_type_change', 'origin': 'adviser', 'reg_type':'2'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, registration_type = '2'))
		
    def test_4_adviser_switch_credit(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'reg_type_change', 'origin': 'adviser', 'reg_type':'1'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, registration_type = '1'))
		
    def test_6_adviser_switch_nonrtp(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'reg_type_change', 'origin': 'adviser', 'reg_type':'3'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, registration_type = '3'))
		
    def test_7_adviser_drop(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'drop', 'origin': 'adviser'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, is_drop = True))
		
    def test_8_adviser_can_adviser_drop_after_dropdate(self):
		participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade,is_drop = False)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'drop', 'origin': 'adviser'}, follow=True)
		self.assertEqual(response.status_code, 403)        
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday, is_drop = False))
		
    def test_9_adviser_undrop(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade, is_drop = True)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'undrop', 'origin': 'adviser'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, is_drop = False))
		
    def test_10_adviser_can_adviser_undrop_after_dropdate(self):
		participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade, is_drop = True)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'undrop', 'origin': 'adviser'}, follow=True)
		self.assertEqual(response.status_code, 403)        
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday, is_drop = True))
		
    def test_11_adviser_disable_student_edit(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade,lock_from_student=False)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'disable_student_edits', 'origin': 'adviser'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, lock_from_student= True))
		
    def test_12_adviser_enable_student_edit(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.audit, grade=self.s_grade,lock_from_student=True)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'enable_student_edits', 'origin': 'adviser'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, lock_from_student= False))

    def test_13_adviser_delete_course(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_delete',args=[participant.id]),
			{'origin': 'adviser'}, follow=True)
		self.assertFalse(Participant.objects.filter(user=self.ben, course=self.course))

    def test_14_adviser_can_adviser_delete_after_adviserApprovalDate(self):
		participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_delete',args=[participant.id]),
                {'origin': 'adviser'}, follow=True)
		self.assertEqual(response.status_code, 403)        
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday))
		
    def test_15_adviser_can_adviser_switch_regtype_afterAdviserApproveDate(self):
		participant = Participant.objects.create(user=self.ben, course=self.course_yesterday,
            participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update',args=[participant.id]),
                {'action': 'reg_type_change', 'origin': 'adviser', 'reg_type':'3'}, follow=True)
		self.assertEqual(response.status_code, 403)        
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course_yesterday, registration_type = '1'))
		
    def test_14_adviser_mark_all(self):
		participant = Participant.objects.create(user=self.ben, course=self.course,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,is_adviser_reviewed=False)
		participant = Participant.objects.create(user=self.ben, course=self.course2,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.credit, grade=self.s_grade,is_adviser_reviewed=False)
		participant = Participant.objects.create(user=self.ben, course=self.course3,
			participant_type=Participant.PARTICIPANT_STUDENT, registration_type=self.nonrtp, grade=self.s_grade,is_adviser_reviewed=False)
		self.client.login(email='charles@test.com', password='charles12345')
		response = self.client.post(reverse('coursereg:participants_update_all'),
			{'student_id': self.ben.id,'action': 'review', 'origin': 'adviser'}, follow=True)
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course, is_adviser_reviewed = True))
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course2, is_adviser_reviewed = True))
		self.assertTrue(Participant.objects.filter(user=self.ben, course=self.course3, is_adviser_reviewed = True))
