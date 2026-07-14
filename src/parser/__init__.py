"""Parser package configuration."""

import os

from dotenv import load_dotenv

from .engine import MISParser


load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/processed/")

__all__ = ["MISParser", "OUTPUT_DIR"]
