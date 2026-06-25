# -*- coding: utf-8 -*-

"""Top-level package for msg_parser."""

from .markdown_converter import MarkdownConverter
from .markdown_converter import convert as convert_to_markdown
from .markdown_converter import convert_directory
from .markdown_converter import convert_msg_to_markdown
from .markdown_converter import save_markdown_file
from .msg_parser import MsOxMessage

__all__ = [
    "MsOxMessage",
    "MarkdownConverter",
    "convert_to_markdown",
    "convert_directory",
    "convert_msg_to_markdown",
    "save_markdown_file",
]
