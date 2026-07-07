from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch


class ForgotPasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', email='tester@example.com', password='secret123')

    @patch('ghr.views.send_email')
    def test_forgot_password_sends_reset_email_for_existing_user(self, mock_send_email):
        response = self.client.post(reverse('forgot_password'), {'email': 'tester@example.com'})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(mock_send_email.called)
        self.assertRedirects(response, reverse('home'))

    def test_forgot_password_redirects_for_unknown_email(self):
        response = self.client.post(reverse('forgot_password'), {'email': 'missing@example.com'})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))
