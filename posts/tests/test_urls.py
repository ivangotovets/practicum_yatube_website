from http import HTTPStatus

from django.test import TestCase, Client

from ..models import Post, Group, User, Follow

INDEX_URL = '/'
FOLLOW_INDEX_URL = '/follow/'
GROUP_URL = '/group/test_slug/'
USER_PROFILE_URL = '/profile/test_user/'
CREATE_POST_URL = '/create/'
CREATE_REDIRECT_URL = '/auth/login/?next=/create/'
NOT_FOUND_URL = '/unexisting_page/'


class PostsURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='test_user')
        cls.user_no_posts = User.objects.create_user(
            username='login')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group,
        )
        Follow.objects.create(user=cls.user, author=cls.user_no_posts)

        cls.EDIT_POST_URL = f'/posts/{cls.post.id}/edit/'
        cls.POST_DETAIL_URL = f'/posts/{cls.post.id}/'
        cls.COMMENT_POST_URL = f'/posts/{cls.post.id}/comment/'
        cls.COMMENT_REDIRECT_URL = (f'/auth/login/?next=/posts/'
                                    f'{cls.post.id}/comment/')

        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client_no_posts = Client()
        cls.authorized_client.force_login(cls.user)
        cls.authorized_client_no_posts.force_login(cls.user_no_posts)

        cls.URLS = {
            cls.authorized_client: {
                CREATE_POST_URL: 'posts/create_post.html',
                cls.EDIT_POST_URL: 'posts/create_post.html',
                FOLLOW_INDEX_URL: 'posts/follow.html',
            },
            cls.guest_client: {
                INDEX_URL: 'posts/index.html',
                GROUP_URL: 'posts/group_list.html',
                USER_PROFILE_URL: 'posts/profile.html',
                cls.POST_DETAIL_URL: 'posts/post_detail.html',
            },
        }

        cls.URLS_REDIRECTS = {
            cls.guest_client: {
                CREATE_POST_URL: CREATE_REDIRECT_URL,
                cls.COMMENT_POST_URL: cls.COMMENT_REDIRECT_URL,
            },
            cls.authorized_client_no_posts: {
                cls.EDIT_POST_URL: cls.POST_DETAIL_URL,
            },
        }

    def test_all_urls_exist(self):
        """Доступны страницы по всем URL."""
        for client, urls in self.URLS.items():
            for url in urls:
                with self.subTest(url=url):
                    response = client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_rises_404(self):
        """Несуществующая страница вернет ошибку 404."""
        response = self.client.get(NOT_FOUND_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_all_urls_use_correct_template(self):
        """URL-адреса используют правильные шаблоны."""
        for client, urls in self.URLS.items():
            for url, template in urls.items():
                with self.subTest(url=url):
                    response = client.get(url)
                self.assertTemplateUsed(response, template)

    def test_redirects_working_correct(self):
        """CREATE_POST перенаправит гостя на страницу авторизации.
        COMMENT_POST_URL перенаправит гостя на страницу авторизации.
        EDIT_POST_URL перенаправит НАвтора поста на страницу
        POST_DETAIL_URL.
        """
        for client, urls in self.URLS_REDIRECTS.items():
            for url, redirect in urls.items():
                response = client.get(url, follow=True)
                self.assertRedirects(response, redirect)
