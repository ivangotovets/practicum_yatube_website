from django.db import models
from django.test import TestCase

from ..models import Group, Post, User, Comment

MODELS_FIELD_TYPES = {
    Post: {
        'text': models.TextField,
        'pub_date': models.DateTimeField,
        'author': models.ForeignKey,
        'group': models.ForeignKey,
        'image': models.ImageField,
    },
    Group: {
        'title': models.CharField,
        'slug': models.SlugField,
        'description': models.TextField,
    },
    Comment: {
        'text': models.TextField,
        'created': models.DateTimeField,
        'author': models.ForeignKey,
        'post': models.ForeignKey,
    },
}

MODELS_FIELD_VERBOSE = {
    Group: {
        'title': 'Название группы',
        'description': 'Описание группы',
        'slug': 'Адрес группы',
    },
    Post: {
        'text': 'Текст поста',
        'pub_date': 'Дата поста',
        'image': 'Картинка',
        'author': 'Автор',
        'group': 'Группа',
    },
    Comment: {
        'text': 'Текст комментария',
        'created': 'Дата комментария',
        'author': 'Автор',
        'post': 'Пост',
    },
}


class PostsModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create_user(username='auth')

        cls.group = Group.objects.create(
            title='Группа',
            slug='test_slug',
            description='Описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Пост',
        )

        cls.comment = Comment.objects.create(
            text='Коммент',
            author=cls.user,
            post=cls.post,
        )

        cls.MODEL_NAMES = {
            cls.post: cls.post.text[:cls.post.MAX_POST_LENGTH],
            cls.group: cls.group.title,
            cls.comment: cls.comment.text[:cls.comment.MAX_COMMENT_LENGTH],
        }

    def test_models_have_correct_fields(self):
        """В моделях созданы поля верного типа."""
        for model, mapping in MODELS_FIELD_TYPES.items():
            for field, field_type in mapping.items():
                with self.subTest(field=field):
                    self.assertIsInstance(
                        model._meta.get_field(field),
                        field_type
                    )

    def test_models_have_correct_object_names(self):
        """У моделей правильно работает __str__."""
        for model, expected_name in self.MODEL_NAMES.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), expected_name)

    def test_post_verbose_name(self):
        """У полей моделей правильные названия."""
        for model, mapping in MODELS_FIELD_VERBOSE.items():
            for field, verbose in mapping.items():
                with self.subTest(field=field):
                    self.assertEqual(
                        model._meta.get_field(field).verbose_name,
                        verbose
                    )
