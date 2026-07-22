import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from content.models import Logo, MarkdownBlock, Page


class MarkdownBlockTests(TestCase):
    def test_page_and_slot_are_unique_together(self):
        page = Page.objects.create(name="test", title="Test")
        MarkdownBlock.objects.create(
            title="Summary",
            page=page,
            slot="summary",
            markdown="First version",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MarkdownBlock.objects.create(
                title="Replacement summary",
                page=page,
                slot="summary",
                markdown="Second version",
            )


class PageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root)

    def test_returns_page_without_authentication(self):
        Page.objects.create(
            name="test-intro",
            title="Test intro",
            background_image=SimpleUploadedFile(
                "background.jpg",
                b"not-validated-until-form-submission",
                content_type="image/jpeg",
            ),
            background_credit="Photo by **Example**",
        )

        response = self.client.get("/content/test-intro/metadata")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "name": "test-intro",
                "title": "Test intro",
                "background_image": "/media/backgrounds/background.jpg",
                "background_credit": "Photo by **Example**",
            },
        )

    def test_unknown_page_returns_not_found(self):
        response = self.client.get("/content/missing/metadata")

        self.assertEqual(response.status_code, 404)

    def test_seeded_intro_page_contains_page_metadata(self):
        response = self.client.get("/content/intro/metadata")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["title"],
            (
                "Climate-related risk analytics for transport, energy & "
                "water infrastructure in Jamaica"
            ),
        )
        self.assertEqual(
            response.json()["background_image"],
            (
                "/media/backgrounds/irma-2017_data-from-nasa-modis_"
                "processed-by-antti-lipponen_1280.jpg"
            ),
        )
        self.assertIn(
            "Photo credit: Hurricane Irma",
            response.json()["background_credit"],
        )


class MarkdownBlockPageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.intro_page = Page.objects.create(
            name="test-intro",
            title="Test intro",
        )
        self.guide_page = Page.objects.create(
            name="guide",
            title="Guide",
        )
        MarkdownBlock.objects.create(
            title="Test intro summary",
            page=self.intro_page,
            slot="summary",
            markdown="Intro **summary**",
        )
        MarkdownBlock.objects.create(
            title="Guide summary",
            page=self.guide_page,
            slot="summary",
            markdown="Guide summary",
        )

    def test_returns_blocks_for_requested_page_without_authentication(self):
        response = self.client.get("/content/test-intro")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [{"slot": "summary", "markdown": "Intro **summary**"}],
        )

    def test_seeded_intro_page_contains_every_markdown_slot(self):
        response = self.client.get("/content/intro")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {block["slot"] for block in response.json()},
            {"summary", "collaboration", "funding"},
        )

    def test_seeded_data_page_contains_every_markdown_slot(self):
        response = self.client.get("/content/data")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {block["slot"] for block in response.json()},
            {"access_notice", "release_notice", "content"},
        )


class LogoPageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.intro_page = Page.objects.create(
            name="test-intro",
            title="Test intro",
        )
        self.guide_page = Page.objects.create(
            name="guide",
            title="Guide",
        )

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root)

    def create_logo(self, **overrides):
        defaults = {
            "name": "Example organisation",
            "page": self.intro_page,
            "slot": "collaboration",
            "image": SimpleUploadedFile(
                "example.png",
                b"not-validated-until-form-submission",
                content_type="image/png",
            ),
            "link": "https://example.com",
            "height": 120,
            "position": 0,
        }
        return Logo.objects.create(**(defaults | overrides))

    def test_returns_logos_for_requested_page_without_authentication(self):
        self.create_logo(
            name="Second",
            position=2,
            image=SimpleUploadedFile("second.png", b"second"),
        )
        self.create_logo(
            name="First",
            position=1,
            image=SimpleUploadedFile("first.png", b"first"),
        )
        self.create_logo(page=self.guide_page)

        response = self.client.get("/content/test-intro/logos")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [logo["alt"] for logo in response.json()],
            ["First", "Second"],
        )
        self.assertEqual(
            response.json()[0],
            {
                "slot": "collaboration",
                "src": "/media/logos/first.png",
                "href": "https://example.com",
                "alt": "First",
                "height": 120,
            },
        )
