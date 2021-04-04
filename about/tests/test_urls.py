from django.test import Client, TestCase


class AboutUrlsTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_urls_exist_at_desired_location(self):
        urls = [
            '/about/author/',
            '/about/tech/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_urls_use_correct_template(self):
        urls_to_templates = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, template in urls_to_templates.items():
            with self.subTest(url=url, template=template):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)
