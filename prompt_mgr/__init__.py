"""Prompt Manager - A lightweight CLI tool for managing AI prompt templates."""

__version__ = "0.1.0"

from .manager import PromptManager
from .models import Template, TemplateCollection

__all__ = ["PromptManager", "Template", "TemplateCollection"]
