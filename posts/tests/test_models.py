from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = User.objects.create(username='Амалия')
        group = Group.objects.create(
            title='Группа Амалии',
            slug='Amalia',
            description='Блог Амалии')
        cls.post = Post.objects.create(
            text='Как же хочется капучино с круассаном',
            author=user,
            group=group
        )

    def test_verbose_name(self):
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст',
            'group': 'Группа'
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name,
                    expected)

    def test_help_text(self):
        post = PostModelTest.post
        field_help_text = {
            'text': 'Поделитесь своим любимым произведением',
            'group': 'Укажите, какой группе принадлежит произведение'
        }
        for value, expected in field_help_text.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_str_method(self):
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEquals(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Группа Амалии',
            slug='Amalia',
            description='Блог Амалии')

    def test_str_method(self):
        group = GroupModelTest.group
        self.assertEquals(group.title, str(group))
