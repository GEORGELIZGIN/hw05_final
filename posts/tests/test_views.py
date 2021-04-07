import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Follow, Group, Post

User = get_user_model()


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.group = Group.objects.create(
            title='Группа',
            slug='group'
        )
        cls.another_group = Group.objects.create(
            title='Групп',
            slug='s'
        )
        cls.user = User.objects.create_user(username='Amalia')
        cls.text = 'aaaa'
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
            text='aaaa',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.another_user = User.objects.create_user(username='a')
        cls.another_post = Post.objects.create(
            text='aa',
            author=cls.another_user,
            group=cls.another_group
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTests.user)
        self.another_auth_client = Client()
        self.another_auth_client.force_login(
            PostsViewsTests.another_user)

    def check_post_context(self, post):
        self.assertEqual(post.text, PostsViewsTests.text)
        self.assertEqual(post.group, PostsViewsTests.group)
        self.assertEqual(post.author, PostsViewsTests.user)
        self.assertEqual(post.image, 'posts/small.gif')

    def test_pages_use_correct_template(self):
        templates_pages_names = {
            'index.html': reverse('posts:index'),
            'group.html': reverse('posts:group', kwargs={'slug': 'group'}),
            'posts/new_post.html': reverse('posts:new_post'),
            'profile.html': reverse(
                'posts:profile',
                kwargs={'username': 'Amalia'}),
            'post.html': reverse(
                'posts:post',
                kwargs={'username': 'Amalia', 'post_id': '1'}),
            'post_new.html': reverse(
                'posts:post_edit',
                kwargs={'username': 'Amalia', 'post_id': '1'}),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_in_context = response.context['page'][1]
        self.check_post_context(post_in_context)

    def test_new_page_shows_correct_context(self):
        response = self.authorized_client.get(reverse('posts:new_post'))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group', kwargs={'slug': 'group'}))
        group = response.context['group']
        posts = response.context['page']
        self.assertEqual(group.title, PostsViewsTests.group.title)
        self.assertEqual(group.slug, PostsViewsTests.group.slug)
        self.assertNotIn(PostsViewsTests.another_group, posts)

    def test_profile_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'Amalia'})
        )
        page = response.context['page']
        post = page[0]
        self.assertNotIn(PostsViewsTests.another_user, page)
        self.check_post_context(post)

    def test_post_edit_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'username': 'Amalia', 'post_id': '1'}))
        form_fields = {
            'text': forms.CharField,
            'group': forms.ChoiceField,
            'image': forms.ImageField,
        }
        post = response.context['form'].save(commit=False)
        self.check_post_context(post)
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_page_shows_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post',
                kwargs={'username': 'Amalia', 'post_id': '1'}))
        author = response.context['author']
        post = response.context['post']
        num_posts = response.context['num_posts']
        self.check_post_context(post)
        self.assertEqual(author, PostsViewsTests.user)
        self.assertEqual(1, num_posts)

    def test_page_not_found(self):
        response = self.authorized_client.get('/lm/')
        self.assertEqual(response.status_code, 404)

    def test_subscribe_by_auth_user(self):
        follows = Follow.objects.all().count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': 'a'})
        )
        self.assertEqual(follows + 1, Follow.objects.all().count())
        self.assertTrue(
            Follow.objects.filter(
                user=PostsViewsTests.user,
                author=PostsViewsTests.another_user).exists()
        )

    def test_unsuscribe_by_auth_user(self):
        Follow.objects.create(
            author=PostsViewsTests.another_user,
            user=PostsViewsTests.user)
        follows = Follow.objects.all().count()
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': 'a'})
        )
        self.assertEqual(follows - 1, Follow.objects.all().count())
        self.assertFalse(
            Follow.objects.filter(
                user=PostsViewsTests.user,
                author=PostsViewsTests.another_user
            ).exists()
        )

    def test_posts_from_followings(self):
        Follow.objects.create(
            author=PostsViewsTests.another_user, user=PostsViewsTests.user)
        response_from_follower = (
            self.authorized_client.get(
                reverse('posts:follow_index')))
        posts_for_follower = response_from_follower.context['page'].object_list
        response_from_not_follower = (
            self.another_auth_client.get(
                reverse('posts:follow_index')
            ))
        posts_for_not_follower = response_from_not_follower.context['page']
        new_post = (
            Post.objects.create(text='j', author=PostsViewsTests.another_user)
        )
        response_from_follower = (
            self.authorized_client.get(
                reverse('posts:follow_index')))
        response_from_not_follower = (
            self.another_auth_client.get(
                reverse('posts:follow_index')))
        posts_for_follower_after_creating_new = (
            response_from_follower.context['page'].object_list
        )
        posts_for_not_follower_after_creating_new = (
            response_from_not_follower.context['page']
        )
        self.assertNotIn(new_post, posts_for_not_follower)
        self.assertNotIn(new_post, posts_for_not_follower_after_creating_new)
        self.assertNotIn(new_post, posts_for_follower)
        self.assertIn(new_post, posts_for_follower_after_creating_new)


class PaginatorTestViews(TestCase):
    def setUp(self):
        self.group = Group.objects.create(
            title='Группа',
            slug='group'
        )
        self.user = User.objects.create_user(username='Amalia')
        for i in range(13):
            Post.objects.create(
                text=str(i),
                author=self.user,
                group=self.group,
            )
        self.guest_client = Client()

    def test_first_page_containse_ten_records(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        response = self.client.get(
            reverse('posts:index'), {'page': '2'})
        self.assertEqual(len(response.context.get('page').object_list), 3)
