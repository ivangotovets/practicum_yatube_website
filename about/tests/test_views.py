from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.REVERSES = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def setUp(self):
        self.guest_client = Client()

    def test_about_page_accessible_by_name(self):
        """Доступны reverse в пространстве about."""
        for path in self.REVERSES:
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_about_page_uses_correct_template(self):
        """Относительные reverse из about ведут к правильным шаблонам."""
        for path, template in self.REVERSES.items():
            with self.subTest(path=path):
                response = self.guest_client.get(path)
                self.assertTemplateUsed(response, template)
