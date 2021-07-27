from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import PAGE_SIZE
from .forms import PostForm, CommentForm, SearchUserForm
from .models import Group, Post, Follow

User = get_user_model()


def index(request):
    post_list = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
    }
    return render(request, 'posts/index.html', context)


@login_required
def follow_index(request):
    user = request.user
    post_list = Post.objects.select_related(
        'author', 'group').filter(author__following__user=user)
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('profile', username=author)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username=author)


def groups_index(request):
    group_list = Group.objects.all()
    paginator = Paginator(group_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
    }
    return render(request, 'posts/groups.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.post_set.all()
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'group': group,
        'page': page
    }
    return render(request, 'posts/group.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = request.user.is_authenticated and (
        Follow.objects.filter(user=request.user, author=author).exists()
    )
    post_list = (
        Post.objects.select_related('author', 'group').filter(author=author)
    )
    paginator = Paginator(post_list, PAGE_SIZE)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'author': author,
        'page': page,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id,
        author__username=username
    )
    author = post.author
    comments = post.comments.all()
    following = request.user.is_authenticated and (
        Follow.objects.filter(user=request.user, author=author).exists()
    )
    form = CommentForm()
    context = {
        'author': author,
        'post': post,
        'following': following,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post.html', context)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
        return redirect('post', username=username, post_id=post_id)

    return redirect('post', username=username, post_id=post_id)


def search_user(request):
    if request.method == 'POST':
        form = SearchUserForm(request.POST)
        if form.is_valid():
            search = form.data['search']
            find_username = User.objects.filter(username__icontains=search)
            find_first_name = User.objects.filter(first_name__icontains=search)
            find_last_name = User.objects.filter(last_name__icontains=search)
            find_user = find_username.union(find_first_name, find_last_name)
            find_post = Post.objects.filter(text__icontains=search)
            context = {
                'form': form,
                'find_user': find_user,
                'find_post': find_post,
            }
            return render(request, 'posts/search.html', context)
        return render(request, 'posts/search.html', {'form': form})
    form = SearchUserForm()
    return render(request, 'posts/search.html', {'form': form})


@login_required
def del_post(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)

    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)

    post.delete()

    return redirect('profile', username=username)


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)

        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('index')

        return render(request, 'posts/new_post.html', {'form': form})

    form = PostForm()
    return render(request, 'posts/new_post.html', {'form': form})


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)

    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)

    context = {
        'form': form,
        'post': post,
    }
    return render(request, 'posts/post_edit.html', context)


def page_not_found(request, exception):
    return render(
        request,
        'misc/404.html',
        {'path': request.path},
        status=404
    )


def server_error(request):
    return render(request, 'misc/500.html', status=500)
