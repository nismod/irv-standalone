from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from content.models import MarkdownBlock


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
