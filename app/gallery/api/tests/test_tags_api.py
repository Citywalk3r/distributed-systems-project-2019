from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, UploadedImage, Gallery

from gallery.serializers import TagSerializer


TAGS_URL = reverse('gallery-api:tag-list')


def sample_gallery(user, title='NiceG'):
    """Create and return a sample gallery"""
    return Gallery.objects.create(user=user, name=title)


class PublicTagsApiTest(TestCase):
    """Test the publicly available tags API"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that login is required for retrieving tags"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
    """Test the authorized user tags API"""

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'password123'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieving_tags(self):
        """Test retrieving tags"""
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')

        res = self.client.get(TAGS_URL)

        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        """Test that tags returned are for authenticated user"""
        user2 = get_user_model().objects.create_user(
            'other@gmail.com'
            'testpasss'
        )
        Tag.objects.create(user=user2, name='Fruity')
        tag = Tag.objects.create(user=self.user, name='Comfort Food')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)

    def test_create_tag_successful(self):
        """Test creating a new tag"""
        payload = {'name': 'Test tag'}
        self.client.post(TAGS_URL, payload)
        exists = Tag.objects.filter(
            user=self.user,
            name=payload['name']
        ).exists()

        self.assertTrue(exists)

    def test_create_tag_invalid(self):
        """Test creating a new tag with invalid payload"""
        payload = {'name': ''}
        res = self.client.post(TAGS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_tags_assigned_to_images(self):
        """Test filtering tags by those assigned to images"""
        gallery = sample_gallery(self.user)
        tag1 = Tag.objects.create(user=self.user, name='Sunny')
        tag2 = Tag.objects.create(user=self.user, name='Cloudy')
        u_img = UploadedImage.objects.create(
            gallery=gallery,
            name='Sunrise',
            user=self.user
        )
        u_img.tags.add(tag1)
        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        # serialize the created tags to verify if they are cointeined
        # inside the response json object
        serializer1 = TagSerializer(tag1)
        serializer2 = TagSerializer(tag2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    # we need to return a distinct set of results
    # if a tag is assigned to multiple images, we want it to return once
    def test_retrieve_tags_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""
        gallery = sample_gallery(self.user)
        tag = Tag.objects.create(user=self.user, name='Winter')
        Tag.objects.create(user=self.user, name='Autumn')
        u_img1 = UploadedImage.objects.create(
            gallery=gallery,
            name='Flowers',
            user=self.user
        )
        u_img1.tags.add(tag)
        u_img2 = UploadedImage.objects.create(
            gallery=gallery,
            name='grassland',
            user=self.user
        )
        u_img2.tags.add(tag)

        res = self.client.get(TAGS_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
