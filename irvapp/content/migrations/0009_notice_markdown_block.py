from django.db import migrations


NOTICE_PAGE_NAME = "notice"
NOTICE_BLOCKS = [
    {
        "title": "Access notice drawer",
        "slot": "content",
        "markdown": (
            "The systemic risk analysis data and results shown in this tool "
            "contain licensed data that must not be shared outside the "
            "Government of Jamaica. By accessing the tool, you acknowledge "
            "that you understand this and agree not to download any data or "
            "share your access credentials with anyone else. "
            "[Read more about the data](/data).\n"
        ),
    },
]


def add_notice_blocks(apps, schema_editor):
    MarkdownBlock = apps.get_model("content", "MarkdownBlock")
    Page = apps.get_model("content", "Page")

    page, _ = Page.objects.get_or_create(
        name=NOTICE_PAGE_NAME,
        defaults={"title": "Notice"},
    )

    for block in NOTICE_BLOCKS:
        MarkdownBlock.objects.update_or_create(
            page=page,
            slot=block["slot"],
            defaults={
                "title": block["title"],
                "markdown": block["markdown"],
            },
        )


def remove_notice_blocks(apps, schema_editor):
    MarkdownBlock = apps.get_model("content", "MarkdownBlock")

    MarkdownBlock.objects.filter(
        page=NOTICE_PAGE_NAME,
        slot__in=[block["slot"] for block in NOTICE_BLOCKS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0008_guide_markdown_blocks"),
    ]

    operations = [
        migrations.RunPython(add_notice_blocks, remove_notice_blocks),
    ]
