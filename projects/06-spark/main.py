"""Ponto de entrada para `spark-submit main.py <comando>` (mesmo caminho local e em cluster)."""

import sys

from sparkjobs.cli import main

sys.exit(main())
