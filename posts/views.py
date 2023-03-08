from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Comment, Follow
from .utils import make_pages


def index(request):
    return render(request, 'posts/index.html', {
        'page_obj': make_pages(
            request,
            Post.objects.select_related('author', 'group'),
        ),
        'index': True,
        'follow': False,
        'get_author': True,
    })


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    return render(request, 'posts/group_list.html', {
        'group': group,
        'page_obj': make_pages(
            request,
            group.posts.select_related('author', 'group')
        ),
        'get_author': True,
    })


def post_detail(request, post_id):
    return render(request, 'posts/post_detail.html', {
        'post': Post.objects.select_related('author', 'group').get(id=post_id),
        'comments': Comment.objects.filter(post=post_id),
        'form': CommentForm(request.POST or None),
    })


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {
            'form': form,
            'is_edit': False,
        })
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', new_post.author.username)


@login_required()
def post_edit(request, post_id):
    instance = get_object_or_404(Post, id=post_id)
    if instance.author == request.user:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=instance
        )
        if not form.is_valid():
            return render(request, 'posts/create_post.html', {
                'form': form,
                'is_edit': True,
            })
        edited_post = form.save(commit=False)
        edited_post.author = request.user
        edited_post.save()
    return redirect('posts:post_detail', post_id)


@login_required()
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = get_object_or_404(Post, id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and (request.user != author)
        and Follow.objects.filter(user=request.user, author=author).exists()
    )
    return render(request, 'posts/profile.html', {
        'author': author,
        'page_obj': make_pages(
            request,
            author.posts.select_related('author', 'group')
        ),
        'following': following,
        'get_author': False,
    })


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollow = get_object_or_404(
        Follow,
        user=request.user,
        author=author,
        # с этим лукапом все корректно работает и мои тесты проходят,
        # внешние тесты валятся
        # user__follower__author__username=username,
    )
    unfollow.delete()
    return redirect('posts:profile', username)


@login_required()
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = make_pages(request, post_list)
    context = {
        'page_obj': page_obj,
        'index': False,
        'follow': True,
        'get_author': True,
    }
    return render(request, 'posts/follow.html', context)
