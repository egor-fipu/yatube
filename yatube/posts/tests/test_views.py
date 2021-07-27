import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post, Group, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.user = User.objects.create_user(
            username='test_user',
            first_name='Тесториан',
            last_name='Тестов'
        )
        # создаем еще пользоваетлей, для проверки подписок
        cls.user_2 = User.objects.create_user(username='test_user_2')
        cls.user_3 = User.objects.create_user(username='test_user_3')
        cls.group = Group.objects.create(
            title='Тестовое имя сообщества',
            slug='test-slug',
            description='Тестовое описание сообщества'
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        # создаём 2-ю группу для проверки, что пост не попал в нее
        cls.second_group = Group.objects.create(
            title='Тестовое имя 2-го сообщества',
            slug='second-test-slug',
            description='Тестовое описание 2-го сообщества'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """Функция проверяет используемые шаблоны."""
        templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/group.html': (
                reverse('group_posts', kwargs={'slug': self.group.slug})
            ),
            'posts/profile.html': (
                reverse(
                    'profile',
                    kwargs={'username': self.user.username}
                )
            ),
            'posts/post.html': (
                reverse(
                    'post',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }
                )
            ),
            'posts/new_post.html': reverse('new_post'),
            'posts/post_edit.html': (
                reverse(
                    'post_edit',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }
                )
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_shows_correct_context(self):
        """Функция проверяет словарь контекста страниц: главной, подписок,
        группы, профиля, поста."""
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        Follow.objects.create(user=self.user_2, author=self.user)
        subtests_tuple = (
            # A tuple of (address, subtest_description)
            (reverse('index'), 'posts context "index" page'),
            (reverse('follow_index'), 'posts context "follow index" page'),
            (reverse('group_posts', kwargs={'slug': self.group.slug}),
             'posts context "group" page'),
            (reverse('profile', kwargs={'username': self.user.username}),
             'posts context "profile" page')
        )
        for address, subtest_description in subtests_tuple:
            with self.subTest(subtest_description):
                response = self.authorized_client_2.get(address)
                first_object = response.context['page'][0]
                post_id_0 = first_object.id
                post_text_0 = first_object.text
                post_author_0 = first_object.author
                post_group_0 = first_object.group
                post_image_0 = first_object.image
                self.assertEqual(post_id_0, self.post.id)
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_author_0, self.user)
                self.assertEqual(post_group_0, self.group)
                self.assertEqual(post_image_0, self.post.image)

        with self.subTest('group context "group" page'):
            response = self.authorized_client.get(
                reverse('group_posts', kwargs={'slug': self.group.slug})
            )
            self.assertEqual(
                response.context['group'].title,
                self.group.title
            )
            self.assertEqual(response.context['group'].slug, self.group.slug)
            self.assertEqual(
                response.context['group'].description,
                self.group.description
            )

        with self.subTest('author context "profile" page'):
            response = self.authorized_client.get(
                reverse('profile', kwargs={'username': self.user_2.username})
            )
            self.assertEqual(
                response.context['author'].username,
                self.user_2.username
            )
            self.assertEqual(
                response.context['author'].first_name,
                self.user_2.first_name
            )
            self.assertEqual(
                response.context['author'].last_name,
                self.user_2.last_name
            )
            self.assertFalse(
                response.context['following']
            )

        with self.subTest('context "post" page'):
            response = self.authorized_client_2.get(
                reverse(
                    'post',
                    kwargs={
                        'username': self.user.username,
                        'post_id': self.post.id,
                    }
                )
            )
            self.assertEqual(response.context['post'].id, self.post.id)
            self.assertEqual(response.context['post'].text, self.post.text)
            self.assertEqual(response.context['post'].author, self.user)
            self.assertEqual(response.context['post'].group, self.group)
            self.assertEqual(response.context['post'].image, self.post.image)
            self.assertEqual(
                response.context['author'].username,
                self.user.username
            )
            self.assertEqual(
                response.context['author'].first_name,
                self.user.first_name
            )
            self.assertEqual(
                response.context['author'].last_name,
                self.user.last_name
            )
            self.assertTrue(
                response.context['following']
            )

    def test_new_post_page_shows_correct_context(self):
        """Функция проверяет словарь контекста страниц создания нового поста
        и редактирования поста (в них передаётся форма)."""
        reverse_list = [
            reverse('new_post'),
            reverse(
                'post_edit',
                kwargs={
                    'username': self.user.username,
                    'post_id': self.post.id,
                }
            )
        ]
        for index in reverse_list:
            response = self.authorized_client.get(index)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_on_page_list_is_1(self):
        """Функция проверяет, что при создании поста, он появляется на главной
        странице, странице группы и профиля пользователя."""
        address_kwargs = {
            'index': {},
            'group_posts': {'slug': self.group.slug},
            'profile': {'username': self.user.username},
        }
        for address, kwargs in address_kwargs.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(
                    reverse(address, kwargs=kwargs)
                )
                self.assertEqual(len(response.context['page']), 1)

    def test_post_on_other_page_list_is_0(self):
        """Функция проверяет, что созданный пост не попал в группу,
        для которой не был предназначен"""
        response = self.authorized_client.get(
            reverse(
                'group_posts',
                kwargs={'slug': self.second_group.slug}
            )
        )
        self.assertEqual(len(response.context['page']), 0)

    def test_post_show_only_followers(self):
        """Проверяет, что новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех, кто не подписан на
        него."""
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)
        self.authorized_client_3 = Client()
        self.authorized_client_3.force_login(self.user_3)
        Follow.objects.create(user=self.user_2, author=self.user)
        response = self.authorized_client_2.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page']), 1)
        response = self.authorized_client_3.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page']), 0)

    def test_login_user_follow(self):
        """Проверяет, что авторизованный пользователь может подписываться на
        других пользователей."""
        self.authorized_client.get(reverse(
            'profile_follow', kwargs={'username': self.user_2.username})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.user, author=self.user_2).exists()
        )

    def test_login_user_unfollow(self):
        """Проверяет, что авторизованный пользователь может удалять из
        подписок других пользователей. """
        Follow.objects.create(user=self.user, author=self.user_2)
        self.authorized_client.get(reverse(
            'profile_unfollow', kwargs={'username': self.user_2.username})
        )
        self.assertFalse(
            Follow.objects.filter(user=self.user, author=self.user_2).exists()
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='Тестовое имя сообщества',
            slug='test-slug',
            description='Тестовое описание сообщества'
        )
        # создаем 13 постов для тестирования пажинатора
        for _ in range(13):
            Post.objects.create(
                text='Тестовый текст поста',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_pages_contains_ten_records(self):
        """Функция проверяет количество постов (должно == 10) на первых
        страницах главной, группы и профиля."""
        address_kwargs = {
            'index': {},
            'group_posts': {'slug': self.group.slug},
            'profile': {'username': self.user.username},
        }
        for address, kwargs in address_kwargs.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(
                    reverse(address, kwargs=kwargs)
                )
                self.assertEqual(
                    len(response.context.get('page').object_list), 10
                )

    def test_second_pages_contains_three_records(self):
        """Функция проверяет количество постов (должно == 3) на вторых
        страницах главной, группы и профиля."""
        address_kwargs = {
            'index': {},
            'group_posts': {'slug': self.group.slug},
            'profile': {'username': self.user.username},
        }
        for address, kwargs in address_kwargs.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(
                    reverse(address, kwargs=kwargs) + '?page=2'
                )
                self.assertEqual(
                    len(response.context.get('page').object_list), 3
                )
