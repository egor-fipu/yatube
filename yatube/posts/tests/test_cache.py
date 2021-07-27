from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index(self):
        test_text = 'Тестовый текст для проверки кэша'
        # Проверяем, что на index нет поста с нашим текстом
        response_1 = self.authorized_client.get(reverse('index'))
        self.assertNotContains(response_1, test_text)
        # Делаем новый пост
        self.authorized_client.post(
            reverse('new_post'),
            data={'text': test_text}
        )
        # Проверяем, что он не появился на index
        response_2 = self.authorized_client.get(reverse('index'))
        self.assertNotContains(response_2, test_text)
        # Чистим кэш
        cache.clear()
        response_3 = self.authorized_client.get(reverse('index'))
        self.assertContains(response_3, test_text)
