from django.contrib.auth import get_user_model
from django.test import TestCase

from posts.models import Post, Group

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(title='test_group')
        cls.post = Post.objects.create(
            text='Тестовый текст один',
            author=cls.user,
            group=cls.group,
        )

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'author': 'Автор',
            'group': 'Сообщество',
            'pub_date': 'Дата публикации'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_object_name_is_text_field(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))

    def test_text_field_max_length(self):
        post = PostModelTest.post
        max_length_text_field = 15
        length_text_field = len(str(post))
        self.assertEqual(max_length_text_field, length_text_field)


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое имя сообщества',
            slug='address',
            description='Тестовое описание сообщества'
        )

    def test_object_name_is_title_field(self):
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
