from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class AboutViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_accessible_by_name(self):
        address_code = {
            'about:author': HTTPStatus.OK,
            'about:tech': HTTPStatus.OK,
        }
        for address, code in address_code.items():
            with self.subTest(address=address):
                response = self.guest_client.get(reverse(address))
                self.assertEqual(response.status_code, code)

    def test_about_pages_uses_correct_template(self):
        address_template = {
            'about:author': 'about/author.html',
            'about:tech': 'about/tech.html',
        }
        for address, template in address_template.items():
            with self.subTest(template=template):
                response = self.guest_client.get(reverse(address))
                self.assertTemplateUsed(response, template)
