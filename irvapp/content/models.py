from django.db import models
from martor.models import MartorField


class MarkdownBlock(models.Model):
    title = models.CharField(max_length=200)
    page = models.CharField(max_length=20)
    slot = models.CharField(max_length=20)
    markdown = MartorField()

    class Meta:
        db_table = 'markdown_block'
        constraints = [
            models.UniqueConstraint(
                fields=["page", "slot"],
                name="unique_markdown_block_page_slot",
            ),
        ]
        ordering = ["page", "slot"]

    def __str__(self):
        return self.title


class Logo(models.Model):
    name = models.CharField(
        max_length=200,
        help_text="The organisation name, also used as the image alt text.",
    )
    page = models.CharField(max_length=20, default="intro")
    slot = models.CharField(
        max_length=20,
        help_text="The named page slot in which this logo should appear.",
    )
    image = models.ImageField(upload_to="logos/")
    link = models.URLField()
    height = models.PositiveSmallIntegerField(
        default=100,
        help_text="Displayed logo height in pixels.",
    )
    position = models.PositiveSmallIntegerField(
        default=0,
        help_text="Logos in the same slot are displayed in ascending order.",
    )

    class Meta:
        db_table = "logo"
        ordering = ["page", "slot", "position", "name"]

    def __str__(self):
        return self.name
