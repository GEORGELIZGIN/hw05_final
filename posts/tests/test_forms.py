import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostsFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='Амалия')
        self.another_user = User.objects.create_user(username='Русик')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.guest_client = Client()

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'gagagaga',
        }
        self.guest_client.post(
            reverse('posts:new_post'),
            data=form_data
        )
        self.assertNotEqual(Post.objects.count(), posts_count + 1)
        self.assertFalse(
            Post.objects.filter(
                text='gagagaga',
                author=self.user,
            ).exists()
        )
        with PostsFormTests.uploaded.open() as img:
            form_data = {
                'text': 'gagagaga',
                'image': img
            }
            response = self.authorized_client.post(
                reverse('posts:new_post'),
                data=form_data,
                follow=True
            )
            self.assertRedirects(response, reverse('posts:index'))
            self.assertEqual(Post.objects.count(), posts_count + 1)
            self.assertTrue(
                Post.objects.filter(
                    text='gagagaga',
                    author=self.user,
                    image='posts/small.gif'
                ).exists()
            )

    def test_update_post(self):
        group = Group.objects.create(
            title='group',
            slug='group',
        )
        Post.objects.create(
            text='g',
            group=group,
            author=self.user
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'ga'
        }
        self.guest_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': 'Амалия',
                    'post_id': '1'
                }
            ),
            data=form_data
        )
        self.assertFalse(
            Post.objects.filter(
                text='ga',
                author=self.user,
                group=None,
            ).exists()
        )
        self.assertTrue(
            Post.objects.filter(
                text='g',
                group=group,
                author=self.user,
            ).exists()
        )
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={
                    'username': 'Амалия',
                    'post_id': '1'
                }
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post',
                kwargs={'username': 'Амалия', 'post_id': '1'}))
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='ga',
                author=self.user,
                group=None,
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                text='g',
                group=group,
                author=self.user,
            ).exists()
        )

    def test_create_comment(self):
        post = Post.objects.create(author=self.user, text='a')
        comments = post.comments.count()
        form_data = {
            'text': 'ga'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'username': 'Амалия', 'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post',
                kwargs={'username': 'Амалия', 'post_id': post.pk}))
        self.assertEqual(post.comments.count(), comments + 1)
        self.assertTrue(
            post.comments.filter(text='ga', author=self.user).exists()
        )
        comments = post.comments.count()
        form_data = {
            'text': 'gaga'
        }
        self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'username': 'Амалия', 'post_id': post.pk}),
            data=form_data,
        )
        self.assertNotEqual(post.comments.count(), comments + 1)
        self.assertFalse(
            post.comments.filter(text='gaga').exists()
        )
