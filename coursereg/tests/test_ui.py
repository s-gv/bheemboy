from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from django.core.urlresolvers import reverse
from coursereg.models import User, Course, Department, Term
from utils import is_error_msg_present
import unittest
import datetime
import logging

#@unittest.skip("skip UI tests in selenium")
class StudentUITests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super(StudentUITests, cls).setUpClass()
        cls.selenium = webdriver.Chrome()
        cls.selenium.implicitly_wait(3)

    @classmethod
    def tearDownClass(cls):
        cls.selenium.quit()
        super(StudentUITests, cls).tearDownClass()

    def setUp(self):
        dept = Department.objects.create(name='Electrical Communication Engineering (ECE)')
        charles = User.objects.create_user(email='charles@test.com', password='charles12345', user_type=User.USER_TYPE_FACULTY)
        ben = User.objects.create_user(email='ben@ece.iisc.ernet.in', password='test12345', user_type=User.USER_TYPE_STUDENT, adviser=charles)
        tomorrow = datetime.datetime.now() + datetime.timedelta(days=1)
        term = Term.objects.create(
            name='Aug-Dec',
            year='2016',
            last_reg_date=tomorrow,
            last_adviser_approval_date=tomorrow,
            last_instructor_approval_date=tomorrow,
            last_conversion_date=tomorrow,
            last_drop_date=tomorrow,
            last_drop_with_mention_date=tomorrow,
            last_grade_date=tomorrow
        )
        self.course = Course.objects.create(num='E0-232', title='Course Name', department=dept, term=term)
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_login_add_course(self):
        driver = self.selenium
        driver.get(self.live_server_url)
        driver.find_element_by_id("inputEmail").clear()
        driver.find_element_by_id("inputEmail").send_keys("ben@ece.iisc.ernet.in")
        driver.find_element_by_id("inputPassword").clear()
        driver.find_element_by_id("inputPassword").send_keys("test12345")
        driver.find_element_by_xpath("//button[@type='submit']").click()
        select = Select(driver.find_element_by_id('course_select_box'))
        select.select_by_visible_text(str(self.course))
        driver.find_element_by_xpath("//button[@type='submit']").click()
        self.assertEqual("E0-232 Course Name (Aug-Dec 2016)", driver.find_element_by_css_selector("div.col-md-5").text)
