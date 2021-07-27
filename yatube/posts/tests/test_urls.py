from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.other_user = User.objects.create_user(username='other_test_user')
        cls.group = Group.objects.create(
            title='Тестовое имя сообщества',
            slug='test-slug',
            description='Тестовое описание сообщества'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.other_authorized_client = Client()
        self.other_authorized_client.force_login(self.other_user)

    def test_posts_urls_exists_at_desired_location_anonymous(self):
        """Функция проверяет общедоступные страницы для неавторизированных
        пользователей, а также, что их редиректит со страниц только
        для залогиненных."""
        address_code = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/{self.user.username}/': HTTPStatus.OK,
            f'/{self.user.username}/{self.post.id}/': HTTPStatus.OK,
            '/new/': HTTPStatus.FOUND,
            f'/{self.user.username}/{self.post.id}/edit/': HTTPStatus.FOUND,
            f'/{self.user.username}/{self.post.id}/comment/': HTTPStatus.FOUND,
        }
        for address, code in address_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_posts_url_redirect_anonymous_on_auth_login(self):
        """Функция проверяет редиректы для неавторизованного пользователя."""
        address_redirect = {
            '/new/': '/auth/login/?next=/new/',
            f'/{self.user.username}/{self.post.id}/edit/': (
                f'/auth/login/?next=/{self.user.username}/{self.post.id}/edit/'
            ),
            f'/{self.user.username}/{self.post.id}/comment/': (
                f'/auth/login/?next=/'
                f'{self.user.username}/{self.post.id}/comment/'
            ),
        }
        for address, redirect in address_redirect.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect)

    def test_posts_urls_exists_at_desired_location_login_user(self):
        """Функция проверяет страницы доступные только для авторизированного
        пользователя, а также что он может редактивать свой пост."""
        address_code = {
            '/new/': HTTPStatus.OK,
            f'/{self.user.username}/{self.post.id}/edit/': HTTPStatus.OK,
        }
        for address, code in address_code.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_posts_edit_url_not_available_other_login_user(self):
        """Функция проверяет, что страница редактирования поста не доступна
        для авторизированного пользователя, не написавшего этот пост."""
        response = self.other_authorized_client.get(
            f'/{self.user.username}/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_posts_edit_redirect_other_login_user(self):
        """Функция проверяет редирект со страницы редактирвоания поста для
        авторизированного пользователя, не написавшего этот пост."""
        response = self.other_authorized_client.get(
            f'/{self.user.username}/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            f'/{self.user.username}/{self.post.id}/'
        )

    def test_urls_uses_correct_template(self):
        """Функция проверяет вызываемых шаблонов для каждого адреса"""
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/{self.user.username}/',
            'posts/post.html': f'/{self.user.username}/{self.post.id}/',
            'posts/new_post.html': '/new/',
            'posts/post_edit.html': (
                f'/{self.user.username}/{self.post.id}/edit/'
            ),
        }
        for template, address in templates_url_names.items():
            with self.subTest(adress=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_not_found_url_use_correct_template(self):
        """Проверка шаблона misc/404.html для запроса несуществующей
        страницы."""
        response = self.guest_client.get('/unknown_url/')
        self.assertTemplateUsed(response, 'misc/404.html')
