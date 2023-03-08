from http import HTTPStatus

from django.test import TestCase, Client

NOT_FOUND_URL = '/unexciting_page/'
NOT_FOUND_TEMP = 'core/404.html'


class PostsURLTests(TestCase):

    def setUp(self):
        self.client = Client()

    def test_non_existing_page_shows_404(self):
        """Страница NOT_FOUND выдаст ошибку 404 и показывает кастомный
        шаблон."""
        response = self.client.get(NOT_FOUND_URL)
        self.assertTemplateUsed(response, NOT_FOUND_TEMP)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
