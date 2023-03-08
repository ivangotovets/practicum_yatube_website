from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import CheckConstraint, F, Q


User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название группы')
    slug = models.SlugField(unique=True, verbose_name='Адрес группы')
    description = models.TextField(
        null=True,
        verbose_name='Описание группы',
        blank=True,
    )

    class Meta:
        ordering = ('title',)
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    MAX_POST_LENGTH = 15

    text = models.TextField(verbose_name='Текст поста')
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата поста',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        verbose_name='Группа',
        on_delete=models.SET_NULL,
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True,
    )

    class Meta:
        ordering = ('-pub_date',)
        default_related_name = 'posts'
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:self.MAX_POST_LENGTH]


class Comment(models.Model):
    MAX_COMMENT_LENGTH = 15

    text = models.TextField(verbose_name='Текст комментария')
    created = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата комментария',
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
    )

    class Meta:
        ordering = ('-created',)
        default_related_name = 'comments'
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return self.text[:self.MAX_COMMENT_LENGTH]


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='follower',
        verbose_name='Пользователь',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        unique_together = (('user', 'author'),)
        constraints = (
            CheckConstraint(
                name='self_follow',
                check=~Q(user=F('author')),
            ),
        )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
