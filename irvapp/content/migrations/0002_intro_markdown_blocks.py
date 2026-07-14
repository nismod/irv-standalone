from django.db import migrations


INTRO_BLOCKS = [
    {
        "title": "Introduction summary",
        "page": "intro",
        "slot": "summary",
        "markdown": (
            "The Jamaica Systemic Risk Assessment Tool (J‑SRAT) supports "
            "climate adaptation decision-making by identifying spatial "
            "criticalities and risks under current and future climate "
            "scenarios.\n\n"
            "## Transport\n\n"
            "Roads, rail, ports and airports.\n\n"
            "## Energy\n\n"
            "Electricity generation, transmission and distribution.\n\n"
            "## Water\n\n"
            "Water supply, wastewater and irrigation."
        ),
    },
    {
        "title": "Collaboration",
        "page": "intro",
        "slot": "collaboration",
        "markdown": (
            "The research, analysis and development has been led by "
            "researchers in the [Oxford Programme for Sustainable "
            "Infrastructure Systems](https://opsis.eci.ox.ac.uk/), "
            "University of Oxford, in collaboration with the Planning "
            "Institute of Jamaica and supported by engagement with "
            "infrastructure and climate specialists and related government "
            "bodies."
        ),
    },
    {
        "title": "Funding and support",
        "page": "intro",
        "slot": "funding",
        "markdown": (
            "## Funding and support\n\n"
            "This project is led by researchers in the [Oxford Programme "
            "for Sustainable Infrastructure Systems]"
            "(https://opsis.eci.ox.ac.uk/) in the Environmental Change "
            "Institute, University of Oxford, with the Government of "
            "Jamaica (GoJ), funded by UK Aid through the UK Foreign and "
            "Commonwealth Development Office (FCDO). The initiative forms "
            "part of the Coalition for Climate Resilient Investment’s "
            "(CCRI) work on “Systemic Resilience” in collaboration with the "
            "Green Climate Fund."
        ),
    },
    {
        "title": "Background image credit",
        "page": "intro",
        "slot": "background-credit",
        "markdown": (
            "Photo credit: Hurricane Irma, 7 September 2017. Data: "
            "MODIS/Terra (NASA WorldView). Processed by Antti Lipponen "
            "([@anttilip](https://twitter.com/anttilip)) "
            "[CC-BY](https://creativecommons.org/licenses/by/2.0/)"
        ),
    },
]


def add_intro_blocks(apps, schema_editor):
    MarkdownBlock = apps.get_model("content", "MarkdownBlock")
    MarkdownBlock.objects.bulk_create(
        MarkdownBlock(**block) for block in INTRO_BLOCKS
    )


def remove_intro_blocks(apps, schema_editor):
    MarkdownBlock = apps.get_model("content", "MarkdownBlock")
    MarkdownBlock.objects.filter(
        page="intro",
        slot__in=[block["slot"] for block in INTRO_BLOCKS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_intro_blocks, remove_intro_blocks),
    ]
