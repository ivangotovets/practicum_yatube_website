import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, Group, User, Comment, Follow

INDEX_URL = reverse('posts:index')
FOLLOW_INDEX_URL = reverse('posts:follow_index')
GROUP_URL = reverse('posts:group_list', args=['test_slug'])
USER_PROFILE_URL = reverse('posts:profile', args=['test_user'])
CREATE_POST_URL = reverse('posts:post_create')

POST_PAGES_URLS = (
    INDEX_URL,
    GROUP_URL,
    USER_PROFILE_URL,
)
LAST_POST = 'Post 12'

PICT_WHITE = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
    b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
    b'\x02\x4c\x01\x00\x3b'
)
PICT_BLACK = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x05\x04\x04'
    b'\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44'
    b'\x01\x00\x3b'
)
UPLOAD_PICT_WHITE = SimpleUploadedFile(
    name='white.gif',
    content=PICT_WHITE,
    content_type='image/gif'
)
UPLOAD_PICT_BLACK = SimpleUploadedFile(
    name='black.gif',
    content=PICT_BLACK,
    content_type='image/gif'
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsViewTests(TestCase):
    """Создаем 1‑го пользователя с 1 записью без группы и 2‑го пользователя
    с 11 постами в тестовой группе. Пост без группы является предпоследним."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='test_user')
        cls.another_user = User.objects.create_user(username='another_user')

        cls.group = Group.objects.create(
            title='Тестовая группа', slug='test_slug', description='Описание'
        )

        post_list = [
            Post(author=cls.user, text=f'Post {n}', group=cls.group)
            for n in range(1, settings.POSTS_PER_PAGE + 1)
        ]
        Post.objects.bulk_create(post_list)
        cls.post_11 = cls.another_post = Post.objects.create(
            author=cls.another_user, text='Post 11', group=None,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=LAST_POST,
            group=cls.group,
            image=UPLOAD_PICT_WHITE,
        )

        cls.comment = Comment.objects.create(
            text='Коммент 1',
            author=cls.user,
            post=cls.post,
        )

        cls.post_form = PostForm(instance=cls.post)

        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.EDIT_POST_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.COMMENT_POST_URL = reverse('posts:add_comment', args=[cls.post.id])
        cls.FOLLOW_USER_URL = reverse(
            'posts:profile_follow',
            args=[cls.user.username],
        )
        cls.UNFOLLOW_USER_URL = reverse(
            'posts:profile_unfollow',
            args=[cls.user.username]
        )
        cls.ALL_URLS = {
            INDEX_URL: 'posts/index.html',
            GROUP_URL: 'posts/group_list.html',
            USER_PROFILE_URL: 'posts/profile.html',
            CREATE_POST_URL: 'posts/create_post.html',
            cls.POST_DETAIL_URL: 'posts/post_detail.html',
            cls.EDIT_POST_URL: 'posts/create_post.html',
            FOLLOW_INDEX_URL: 'posts/follow.html',
        }

        cls.POST_DATA = {
            'text': 'Новый текст',
            'group': cls.group.id,
            'image': UPLOAD_PICT_WHITE,
        }

        cls.auth_client = Client()
        cls.another_auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.another_auth_client.force_login(cls.another_user)

        cls.CONTEXT_EXPECTED_URLS = {
            ('group', cls.group): GROUP_URL,
            ('author', cls.user): USER_PROFILE_URL,
            ('post', cls.post): cls.POST_DETAIL_URL,
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @staticmethod
    def context_eq_fixture(context, fixture):
        flag = True
        for field in fixture._meta.fields:
            if getattr(context, field.name) != getattr(fixture, field.name):
                flag = False
        return flag

    @staticmethod
    def form_data_eq_fixture(form, fixture):
        flag = True
        for field in form.fields:
            if form[field].initial != fixture[field].initial:
                flag = False
        return flag

    def test_group_author_post_receive_correct_context(self):
        """Страницы GROUP, USER_PROFILE, POST_DETAIL получают в контексте
        правильные объекты."""
        for (context, fixture), url in self.CONTEXT_EXPECTED_URLS.items():
            with self.subTest(url=url):
                context_obj = self.auth_client.get(url).context[context]
                self.assertTrue(self.context_eq_fixture(context_obj, fixture))

    def test_pages_receive_post_lists_desc(self):
        """Страницы с постами получают в контексте списки постов с
        сортировкой по убыванию."""
        for url in POST_PAGES_URLS:
            with self.subTest(url=url):
                post_obj = self.auth_client.get(url).context['page_obj'][0]
                self.assertTrue(self.context_eq_fixture(post_obj, self.post))

    def test_post_detail_shows_comments_thread(self):
        """В POST_DETAIL выводятся комментарии."""
        response = self.auth_client.get(self.POST_DETAIL_URL)
        comment = response.context['comments'][0]
        self.assertTrue(self.context_eq_fixture(comment, self.comment))

    def test_post_lists_contain_pages(self):
        """На страницах со списком постов записи выводятся страницы.
        На главной больше на 1 запись."""
        for num_url, page in enumerate(POST_PAGES_URLS, start=1):
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']),
                    settings.POSTS_PER_PAGE,
                )
                response = self.auth_client.get(page + '?page=2')
                if num_url == 1:
                    self.assertEqual(len(response.context['page_obj']), 2)
                else:
                    self.assertEqual(len(response.context['page_obj']), 1)

    def test_group_profile_doesnt_contain_post_from_another_user(self):
        """В GROUP_LIST работает фильтрация по группе и пользователю.
        Пост от 2‑го пользователя выводится только в index."""
        for page in POST_PAGES_URLS:
            with self.subTest(page=page):
                response = self.auth_client.get(page)
                posts_list = response.context['page_obj']
                if page == INDEX_URL:
                    self.assertIn(self.another_post, posts_list)
                else:
                    self.assertNotIn(self.another_post, posts_list)

    def test_post_create_passes_empty_post_form(self):
        """В CREATE_POST в шаблон передается пустой объект PostForm."""
        context = self.auth_client.get(CREATE_POST_URL).context['form']
        self.assertIsInstance(context, PostForm)
        self.assertTrue(self.form_data_eq_fixture(context, PostForm()))

    def test_post_edit_passes_existing_post_form(self):
        """В EDIT_POST в шаблон передается объект PostForm c данными."""
        context = self.auth_client.get(self.EDIT_POST_URL).context['form']
        self.assertIsInstance(context, PostForm)
        self.assertTrue(self.form_data_eq_fixture(context, self.post_form))

    def test_index_page_is_cached(self):
        """Страница INDEX кэшируется."""
        page_before = self.auth_client.get(INDEX_URL)
        Post.objects.all().delete()
        page_cached = self.auth_client.get(INDEX_URL)
        self.assertEqual(page_before.content, page_cached.content)
        cache.clear()
        page_empty = self.auth_client.get(INDEX_URL)
        self.assertNotEqual(page_empty.content, page_cached.content)

    def test_follow(self):
        """Another_user может подписаться на user."""
        followings = set(Follow.objects.all())
        self.assertEqual(len(followings), 0)
        self.another_auth_client.get(self.FOLLOW_USER_URL)
        followings = set(Follow.objects.all())
        self.assertEqual(len(followings), 1)
        follow = followings.pop()
        self.assertEqual(follow.user, self.another_user)
        self.assertEqual(follow.author, self.user)

    def test_unfollow(self):
        """Another_user может отписаться от user."""
        self.another_auth_client.get(self.FOLLOW_USER_URL)
        followings = set(Follow.objects.all())
        self.assertEqual(len(followings), 1)
        self.another_auth_client.get(self.UNFOLLOW_USER_URL)
        followings = set(Follow.objects.all())
        self.assertEqual(len(followings), 0)

    def test_subscription_feed(self):
        """Запись another_user появляется в ленте user, но отсутствует в
        его собственной."""
        Follow.objects.create(user=self.user, author=self.another_user)
        response = self.auth_client.get(FOLLOW_INDEX_URL)
        another_post = response.context['page_obj'][0]
        self.assertTrue(self.context_eq_fixture(another_post, self.post_11))

    def test_cannot_self_follow(self):
        """Нельзя подписаться на себя и работает ограничение в модели."""
        followings = set(Follow.objects.all())
        self.assertEqual(len(followings), 0)
        self.auth_client.get(self.FOLLOW_USER_URL)
        followings = set(Follow.objects.all())
        self.assertEqual(len(followings), 0)
