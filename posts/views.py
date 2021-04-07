from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post

User = get_user_model()


def index(request):
    paginator = Paginator(Post.objects.all(), 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    index_page = f'index_{page_number}'
    return render(
        request,
        'index.html',
        {'page': page, 'index_page': index_page}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    paginator = Paginator(group.posts.all(), 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'group.html', {'group': group, 'page': page})


class NewPostView(LoginRequiredMixin, CreateView):
    form_class = PostForm
    success_url = reverse_lazy('posts:index')
    template_name = 'posts/new_post.html'

    def form_valid(self, form):
        new_post = form.save(commit=False)
        new_post.author = self.request.user
        new_post.save()
        return super().form_valid(form)


def profile(request, username):
    following = request.user.is_authenticated and (
        request.user.follower.filter(author__username=username).exists())
    author = get_object_or_404(User, username=username)
    paginator = Paginator(author.posts.all(), 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    num_posts = author.posts.count()
    context = {
        'num_posts': num_posts,
        'page': page,
        'author': author,
        'following': following
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    if request.method == 'POST':
        return add_comment(request, username, post_id)
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    num_posts = author.posts.count()
    comments = post.comments.all()
    form = CommentForm()
    context = {
        'form': form,
        'comments': comments,
        'author': author,
        'post': post,
        'num_posts': num_posts
    }
    return render(request, 'post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(
        Post,
        id=post_id,
        author__username=username)
    if request.user.username != username:
        return redirect(
            reverse_lazy(
                'posts:profile',
                kwargs={'username': username}
            )
        )
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect(
            reverse_lazy(
                'posts:post',
                kwargs={'username': username, 'post_id': post_id}
            )
        )
    context = {
        'form': form,
        'post': post
    }
    return render(request, 'post_new.html', context)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect(
        reverse_lazy(
            'posts:post',
            kwargs={'username': username, 'post_id': post_id}
        )
    )


@login_required
def follow_index(request):
    posts = Post.objects.filter(
        author__following__user=request.user)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request, 'follow.html',
        {
            'page': page,
            'paginator': paginator})


@login_required
def profile_follow(request, username):
    if(
        request.user.follower.filter(
            author__username=username).exists() or (
                request.user.username == username)
    ):
        return redirect(
            reverse_lazy(
                'posts:profile',
                kwargs={'username': username}
            ))
    author = User.objects.get(username=username)
    Follow.objects.create(
        user=request.user,
        author=author
    )
    return redirect(
        reverse_lazy(
            'posts:profile',
            kwargs={'username': username}
        )
    )


@login_required
def profile_unfollow(request, username):
    follow = get_object_or_404(
        Follow,
        user=request.user,
        author__username=username)
    follow.delete()
    return redirect(
        reverse_lazy(
            'posts:profile',
            kwargs={'username': username}
        )
    )
