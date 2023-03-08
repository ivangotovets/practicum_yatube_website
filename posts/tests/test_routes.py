from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User

INDEX_URL = reverse('posts:index')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
GROUP_URL = reverse('posts:group_list', args=['slug'])
USER_PROFILE_URL = reverse('posts:profile', args=['user'])
CREATE_POST_URL = reverse('posts:post_create')


class StaticViewsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='user')
        cls.another_user = User.objects.create_user(username='another_user')

        cls.group = Group.objects.create(
            title='Группа',
            slug='slug',
            description='Описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Текст',
            group=cls.group,
        )

        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.EDIT_POST_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.COMMENT_POST_URL = reverse('posts:add_comment', args=[cls.post.id])
        cls.FOLLOW_USER_URL = reverse(
            'posts:profile_follow',
            args=[cls.user]
        )
        cls.UNFOLLOW_USER_URL = reverse(
            'posts:profile_unfollow',
            args=[cls.user]
        )
        cls.GUEST_URLS = {
            INDEX_URL: '/',
            GROUP_URL: '/group/slug/',
            USER_PROFILE_URL: '/profile/user/',
            cls.POST_DETAIL_URL: f'/posts/{cls.post.id}/',
        }
        cls.AUTH_URLS = {
            CREATE_POST_URL: '/create/',
            cls.EDIT_POST_URL: f'/posts/{cls.post.id}/edit/',
            cls.COMMENT_POST_URL: f'/posts/{cls.post.id}/comment/',
            FOLLOW_INDEX_URL: '/follow/',
            cls.FOLLOW_USER_URL: f'/profile/{cls.user.username}/follow/',
            cls.UNFOLLOW_USER_URL: f'/profile/{cls.user.username}/unfollow/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_no_posts = Client()
        self.authorized_client_no_posts.force_login(self.another_user)

    def test_reverse_for_guest_exist(self):
        """Reverse для гостя работают."""
        for reverse_name, url in self.GUEST_URLS.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertURLEqual(reverse_name, url)

    def test_reverse_for_authorised_client_exist(self):
        """Reverse для авторизованного юзера работают."""
        for reverse_name, url in self.AUTH_URLS.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertURLEqual(reverse_name, url)

    def test_reverse_for_authorised_client_exist(self):
        """Reverse для авторизованного юзера работают."""
        for reverse_name, url in self.AUTH_URLS.items():
            with self.subTest(reverse_name=reverse_name):
                self.assertURLEqual(reverse_name, url)
