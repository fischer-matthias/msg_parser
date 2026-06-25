#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for the msg-to-Markdown conversion feature."""

import contextlib
import io
import os
import shutil
import tempfile
import unittest

import yaml

from msg_parser import (
    MarkdownConverter,
    MsOxMessage,
    convert_directory,
    convert_msg_to_markdown,
    convert_to_markdown,
)
from msg_parser.cli import create_parser

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_FILES = os.path.join(SCRIPT_PATH, "files")

TEST_NESTED_MSG = os.path.join(TEST_FILES, "outer.msg")
TEST_ATTACHED_EML = os.path.join(TEST_FILES, "other.msg")
TEST_COMPLETE_MSG = os.path.join(TEST_FILES, "complete.msg")


def split_frontmatter(markdown):
    """Return ``(frontmatter_dict, body)`` for a Markdown document."""
    assert markdown.startswith("---\n")
    _, frontmatter, body = markdown.split("---\n", 2)
    return yaml.safe_load(frontmatter), body


class MarkdownConversionTests(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_returns_string_with_frontmatter(self):
        markdown = convert_msg_to_markdown(TEST_COMPLETE_MSG)
        self.assertTrue(markdown.startswith("---\n"))
        self.assertIn("\n---\n", markdown)

    def test_frontmatter_is_valid_yaml(self):
        markdown = convert_msg_to_markdown(TEST_COMPLETE_MSG)
        frontmatter, body = split_frontmatter(markdown)
        self.assertIsInstance(frontmatter, dict)
        self.assertIn("subject", frontmatter)
        self.assertTrue(frontmatter["subject"])
        self.assertTrue(body.strip())

    def test_frontmatter_contains_expected_headers(self):
        markdown = convert_msg_to_markdown(TEST_COMPLETE_MSG)
        frontmatter, _ = split_frontmatter(markdown)
        self.assertIn("from", frontmatter)
        self.assertIn("to", frontmatter)
        self.assertIsInstance(frontmatter["to"], list)
        self.assertIn("attachments", frontmatter)
        self.assertIsInstance(frontmatter["attachments"], list)
        for attachment in frontmatter["attachments"]:
            self.assertIn("filename", attachment)

    def test_converter_class_matches_helper(self):
        message = MsOxMessage(TEST_COMPLETE_MSG)
        self.assertEqual(
            MarkdownConverter(message).to_markdown(),
            convert_msg_to_markdown(TEST_COMPLETE_MSG),
        )

    def test_msox_message_methods(self):
        message = MsOxMessage(TEST_NESTED_MSG)
        markdown = message.get_message_as_markdown()
        self.assertTrue(markdown.startswith("---\n"))

        written = message.save_markdown_file(self.tmp_dir)
        self.assertTrue(os.path.isfile(written))
        with open(written, encoding="utf-8") as handle:
            self.assertEqual(handle.read(), markdown)

    def test_save_single_file_to_directory(self):
        written = convert_to_markdown(TEST_COMPLETE_MSG, self.tmp_dir)
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].endswith("complete.md"))
        self.assertTrue(os.path.isfile(written[0]))

    def test_convert_directory(self):
        written = convert_directory(TEST_FILES, self.tmp_dir)
        self.assertEqual(len(written), 3)
        names = sorted(os.path.basename(path) for path in written)
        self.assertEqual(names, ["complete.md", "other.md", "outer.md"])
        for path in written:
            self.assertTrue(os.path.isfile(path))

    def test_convert_dispatches_on_directory(self):
        written = convert_to_markdown(TEST_FILES, self.tmp_dir)
        self.assertEqual(len(written), 3)

    def test_html_to_markdown_fallback(self):
        html = "<html><body><p>Hello <b>world</b></p><br>second line</body></html>"
        text = MarkdownConverter._html_to_markdown(html)
        self.assertIn("Hello", text)
        self.assertIn("world", text)
        self.assertNotIn("<b>", text)

    def test_address_normalization(self):
        message = MsOxMessage(TEST_COMPLETE_MSG)
        converter = MarkdownConverter(message)
        self.assertEqual(
            converter._normalize_address("user@example.com <user@example.com>"),
            "user@example.com",
        )
        self.assertEqual(
            converter._normalize_address("<user@example.com>"),
            "user@example.com",
        )

    def test_cli_markdown_flag(self):
        parsed = create_parser(["-i", TEST_COMPLETE_MSG, "-m", "-o", self.tmp_dir])
        self.assertTrue(parsed.markdown)
        self.assertFalse(parsed.recursive)


class DirectoryConversionResilienceTests(unittest.TestCase):
    """A single unreadable ``.msg`` must not abort a whole-directory run."""

    def setUp(self):
        self.src_dir = tempfile.mkdtemp()
        self.dst_dir = tempfile.mkdtemp()
        # A valid message and a deliberately corrupt one. "bad.msg" sorts
        # before "good.msg", so it is processed first.
        shutil.copy(TEST_COMPLETE_MSG, os.path.join(self.src_dir, "good.msg"))
        with open(os.path.join(self.src_dir, "bad.msg"), "wb") as handle:
            handle.write(b"this is not a valid OLE/MSG file")

    def tearDown(self):
        shutil.rmtree(self.src_dir, ignore_errors=True)
        shutil.rmtree(self.dst_dir, ignore_errors=True)

    def test_bad_file_does_not_abort_batch(self):
        with contextlib.redirect_stderr(io.StringIO()):
            written = convert_directory(self.src_dir, self.dst_dir)
        self.assertEqual(len(written), 1)
        self.assertTrue(written[0].endswith("good.md"))
        self.assertTrue(os.path.isfile(written[0]))

    def test_failure_is_reported_to_stderr(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            convert_directory(self.src_dir, self.dst_dir)
        self.assertIn("bad.msg", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
