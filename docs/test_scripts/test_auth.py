from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase

class AuthTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpass123'
        )
        self.staff_user = get_user_model().objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='staffpass123',
            is_staff=True
        )
        self.superuser = get_user_model().objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='adminpass123'
        )

    def test_login_view_get(self):
        response = self.client.get(reverse('auth:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Email')

    def test_login_view_post_valid(self):
        response = self.client.post(reverse('auth:login'), {
            'username': 'testuser@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect on success

    def test_login_staff_user(self):
        response = self.client.post(reverse('auth:login'), {
            'username': 'staff@example.com',
            'password': 'staffpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_superuser(self):
        response = self.client.post(reverse('auth:login'), {
            'username': 'admin@example.com',
            'password': 'adminpass123',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_view_post_invalid(self):
        response = self.client.post(reverse('auth:login'), {
            'username': 'wrong@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'inválidos')
