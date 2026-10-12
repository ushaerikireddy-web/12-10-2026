from django.test import TestCase
from django.urls import reverse


class PagesTests(TestCase):
    def test_contact_and_rate_limit(self):
        url = reverse('pages:contact')
        data = {'name': 'A', 'email': 'a@e.com', 'subject': 'Hi', 'message': 'Hello there, this is a test message.'}
        resp = self.client.post(url, data)
        self.assertEqual(resp.status_code, 302)
        # spam honeypot
        resp = self.client.post(url, dict(data, website='bot'))
        self.assertEqual(resp.status_code, 400)

    def test_about_page(self):
        resp = self.client.get(reverse('pages:about'))
        self.assertEqual(resp.status_code, 200)
