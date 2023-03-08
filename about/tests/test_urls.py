from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.URLS = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_urls_exist_at_desired_location(self):
        """Проверка доступности адресов в about."""
        for url in self.URLS:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_use_correct_template(self):
        """Проверка шаблонов для адресов в about."""
        for url, template in self.URLS.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
