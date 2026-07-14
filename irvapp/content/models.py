from django.db import models


class MarkdownBlock(models.Model):
    title = models.CharField(max_length=200)
    page = models.CharField(max_length=20)
    slot = models.CharField(max_length=20)
    markdown = models.TextField()

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
