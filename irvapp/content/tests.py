import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from content.models import Logo, MarkdownBlock


class MarkdownBlockTests(TestCase):
    def test_page_and_slot_are_unique_together(self):
        MarkdownBlock.objects.create(
            title="Summary",
            page="test",
            slot="summary",
            markdown="First version",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MarkdownBlock.objects.create(
                title="Replacement summary",
                page="test",
                slot="summary",
                markdown="Second version",
            )


class MarkdownBlockPageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        MarkdownBlock.objects.create(
            title="Test intro summary",
            page="test-intro",
            slot="summary",
            markdown="Intro **summary**",
        )
        MarkdownBlock.objects.create(
            title="Guide summary",
            page="guide",
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
            {"summary", "collaboration", "funding", "background-credit"},
        )


class LogoPageViewTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.media_root = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_root)

    def create_logo(self, **overrides):
        defaults = {
            "name": "Example organisation",
            "page": "test-intro",
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
        self.create_logo(page="guide")

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
