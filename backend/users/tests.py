from django.contrib.auth import SESSION_KEY, get_user_model
from django.test import TestCase, override_settings


@override_settings(FRONTEND_SITE_URL='http://localhost:5173')
class AdminMainSiteLogoutTests(TestCase):
    def test_admin_main_site_logs_out_and_redirects_to_frontend(self):
        user = get_user_model().objects.create_user(
            username='staff',
            email='staff@example.com',
            password='password',
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get('/admin/main-site/')

        self.assertRedirects(
            response,
            'http://localhost:5173',
            fetch_redirect_response=False,
        )
        self.assertNotIn(SESSION_KEY, self.client.session)
        self.assertIn('no-store', response['Cache-Control'])
        self.assertEqual(response['Pragma'], 'no-cache')
