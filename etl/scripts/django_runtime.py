"""Initialize the application when a Snakemake script runs from etl/."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path('../irvapp').resolve()))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'irvapp.settings')

import django

django.setup()
