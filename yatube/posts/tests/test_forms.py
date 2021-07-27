import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
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
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст создания поста',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response_new = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response_new, reverse('index'))
        self.assertEqual(Post.objects.count(), post_count + 1)
        # Проверяем, что создался пост с нужными полями
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст редактирования поста',
            'group': '',
        }
        response_edit = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={'username': self.post.author, 'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(
            response_edit,
            reverse(
                'post',
                kwargs={'username': self.post.author, 'post_id': self.post.id}
            ),
        )
        # Проверяем, не изменилось ли число постов
        self.assertEqual(Post.objects.count(), post_count)
        # Проверяем, что пост изменился
        response_post_view = self.authorized_client.get(
            reverse(
                'post',
                kwargs={'username': self.post.author, 'post_id': self.post.id}
            )
        )
        self.assertEqual(
            response_post_view.context['post'].text,
            form_data['text']
        )
        self.assertEqual(
            response_post_view.context['post'].group,
            None
        )

    def test_login_user_create_comment(self):
        """Проверяет, что авторизированный пользователь может комментировать
        посты."""
        comment_count = self.post.comments.count()
        form_data = {
            'text': 'Тестовый текст комментария'
        }
        response = self.authorized_client.post(
            reverse(
                'add_comment',
                kwargs={'username': self.post.author, 'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'post',
                kwargs={'username': self.post.author, 'post_id': self.post.id}
            )
        )
        self.assertEqual(self.post.comments.count(), comment_count + 1)
        # Проверяем, что создался коммент с нужными полями
        self.assertTrue(
            Comment.objects.filter(
                text=form_data['text'],
                author=self.user,
                post=self.post
            ).exists()
        )
