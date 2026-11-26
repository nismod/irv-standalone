"""Run the Django feature-layer importer from Snakemake."""

import subprocess
import sys
from pathlib import Path


if __name__ == "__main__":
    manage_py = Path("../irvapp/manage.py").resolve()
    source = snakemake.input[0]
    subprocess.run(
        [sys.executable, str(manage_py), "import_feature_layers", str(source)],
        check=True,
    )
    Path(str(snakemake.output[0])).write_text(f"Loaded from {source}\n")
