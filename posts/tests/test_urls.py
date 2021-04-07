from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа',
            slug='group'
        )
        cls.user = User.objects.create_user(username='Amalia')
        cls.user_not_author = User.objects.create_user(username='Bob')
        Post.objects.create(
            text='aa',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        self.authorized_not_author_client = Client()
        self.authorized_not_author_client.force_login(
            PostURLTests.user_not_author)

    def test_posts_urls_exist_at_desired_location(self):
        public_urls = [
            '/',
            '/group/group/',
            '/Amalia/',
            '/Amalia/1/',
        ]
        private_urls = [
            '/new/',
            '/Amalia/1/edit/',
            '/follow/',
        ]
        for url in public_urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, 200)
        for url in private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)

    def test_posts_new_edit_comment_follow_url_redirects_anonymous_user(self):
        urls_to_redirects = {
            '/new/': '/auth/login/?next=/new/',
            '/Amalia/1/edit/': '/auth/login/?next=/Amalia/1/edit/',
            '/Amalia/1/comment/': '/auth/login/?next=/Amalia/1/comment/',
            '/Amalia/follow/': '/auth/login/?next=/Amalia/follow/',
            '/Amalia/unfollow/': '/auth/login/?next=/Amalia/unfollow/',
        }
        for url, redirect in urls_to_redirects.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, redirect)

    def test_posts_post_edit_url_redirects_not_author_user(self):
        response = self.authorized_not_author_client.get(
            '/Amalia/1/edit/',
            follow=True)
        self.assertRedirects(response, '/Amalia/')

    def test_urls_use_correct_templates(self):
        templates_urls_names = {
            '/': 'index.html',
            '/group/group/': 'group.html',
            '/new/': 'posts/new_post.html',
            '/Amalia/': 'profile.html',
            '/Amalia/1/edit/': 'post_new.html',
            '/follow/': 'follow.html',
        }
        for reverse_name, template in templates_urls_names.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
