from django.shortcuts import reverse
from django.test import Client, TestCase


class TestViewsAbout(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_about_pages_use_correct_template(self):
        templates_to_urls = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }
        for template, url in templates_to_urls.items():
            with self.subTest(template=template, url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
