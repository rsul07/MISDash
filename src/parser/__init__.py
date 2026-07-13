"""Parser package configuration."""

import os

from dotenv import load_dotenv


load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/processed/")

__all__ = ["OUTPUT_DIR"]
