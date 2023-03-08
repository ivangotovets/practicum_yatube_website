import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import fields
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm, CommentForm
from ..models import Post, Group, User, Comment

USER_PROFILE_URL = reverse('posts:profile', args=['test_user'])
CREATE_POST_URL = reverse('posts:post_create')

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
class PostsFormsTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(
            username='test_user'
        )
        cls.another_user = User.objects.create_user(
            username='another_user'
        )

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='1 Группа',
        )
        cls.new_group = Group.objects.create(
            title='Новая группа',
            slug='new_slug',
            description='2 Группа',
        )
        cls.post_form = PostForm()
        cls.comment_form = CommentForm()
        cls.FORMS_FIELD_TYPES = {
            cls.post_form: {
                'text': fields.CharField,
                'group': fields.ChoiceField,
                'image': fields.ImageField,
            },
            cls.comment_form: {
                'text': fields.CharField,
            },
        }

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=cls.group
        )

        cls.comment = Comment.objects.create(
            text='Коммент 1',
            author=cls.user,
            post=cls.post,
        )

        cls.EDIT_POST_URL = reverse('posts:post_edit', args=[cls.post.id])
        cls.POST_DETAIL_URL = reverse('posts:post_detail', args=[cls.post.id])
        cls.COMMENT_POST_URL = reverse('posts:add_comment', args=[cls.post.id])

        cls.POST_DATA = {
            'text': 'Новый текст',
            'group': cls.group.id,
            'image': UPLOAD_PICT_WHITE,
        }
        cls.NEW_POST_DATA = {
            'text': 'Новый текст',
            'group': cls.new_group.id,
            'image': UPLOAD_PICT_BLACK,
        }
        cls.COMMENT_DATA = {
            'text': 'Коммент 2',
            'author': cls.another_user,
            'post': cls.post,
        }

        cls.authorized_client = Client()
        cls.another_authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.another_authorized_client.force_login(cls.another_user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_forms_have_correct_fields(self):
        """В формах созданы поля верного типа."""
        for form, mapping in self.FORMS_FIELD_TYPES.items():
            for field, field_type in mapping.items():
                with self.subTest(field=field):
                    self.assertIsInstance(
                        form.fields[field],
                        field_type
                    )

    def test_post_detail_shows_comment_form(self):
        """В POST_DETAIL выводится форма комментария."""
        response = self.authorized_client.get(self.POST_DETAIL_URL)
        form = response.context['form']
        self.assertIsInstance(form, CommentForm)

    def test_post_create_saves_new_post(self):
        """Валидная форма в CREATE_POST_URL создает новую запись в БД и
        переадресует на USER_PROFILE_URL."""
        posts_before = set(Post.objects.all())
        response = self.authorized_client.post(
            CREATE_POST_URL,
            data=self.POST_DATA,
            follow=True
        )
        self.assertRedirects(response, USER_PROFILE_URL)
        new_posts = set(Post.objects.all()) - posts_before
        post = new_posts.pop()
        self.assertEqual(post.text, self.POST_DATA['text'])
        self.assertEqual(post.group.id, self.POST_DATA['group'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.image.read(), PICT_WHITE)

    def test_post_edit_updates_existing_post(self):
        """Валидная форма в EDIT_POST_URL изменяет запись в БД и переадресует
        на POST_DETAIL_URL."""
        posts_before = set(Post.objects.all())
        response = self.authorized_client.post(
            self.EDIT_POST_URL,
            data=self.NEW_POST_DATA,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        updated_posts = set(Post.objects.all())
        self.assertEqual(len(updated_posts), len(posts_before))
        updated_post = updated_posts.pop()
        self.assertEqual(updated_post.text, self.NEW_POST_DATA['text'])
        self.assertEqual(updated_post.group.id, self.NEW_POST_DATA['group'])
        self.assertEqual(updated_post.author, self.user)
        self.assertEqual(updated_post.image.read(), PICT_BLACK)

    def test_comment_post_saves_new_comment(self):
        """Валидная форма в COMMENT_POST_URL добавляет запись в БД и
        переадресует на POST_DETAIL_URL."""
        comments_before = set(Comment.objects.all())
        response = self.another_authorized_client.post(
            self.COMMENT_POST_URL,
            data=self.COMMENT_DATA,
            follow=True
        )
        self.assertRedirects(response, self.POST_DETAIL_URL)
        new_comments = set(Comment.objects.all()) - comments_before
        comment = new_comments.pop()
        self.assertEqual(comment.text, self.COMMENT_DATA['text'])
        self.assertEqual(comment.post, self.COMMENT_DATA['post'])
        self.assertEqual(comment.author, self.another_user)
