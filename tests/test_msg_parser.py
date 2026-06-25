#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Tests for `msg_parser` package."""

import os
import unittest

from msg_parser.cli import create_parser
from msg_parser.msg_parser import Message, MsOxMessage

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
TEST_FILES = os.path.join(SCRIPT_PATH, "files")

TEST_NESTED_MSG = os.path.join(TEST_FILES, "outer.msg")
TEST_ATTACHED_EML = os.path.join(TEST_FILES, "other.msg")
TEST_COMPLETE_MSG = os.path.join(TEST_FILES, "complete.msg")


class TextMessageParsing(unittest.TestCase):

    def test_command_line_interface(self):
        """Test the CLI."""
        parsed = create_parser(["-i", TEST_COMPLETE_MSG, "--json"])
        self.assertTrue(parsed.json_output)

    def test_msg_parsing_1(self):
        ms_msg = MsOxMessage(TEST_COMPLETE_MSG)
        self.assertTrue(ms_msg.get_properties())

    def test_msg_parsing_2(self):
        ms_msg = MsOxMessage(TEST_ATTACHED_EML)
        self.assertTrue(ms_msg.get_properties())

    def test_msg_parsing_3(self):
        ms_msg = MsOxMessage(TEST_NESTED_MSG)
        self.assertTrue(ms_msg.get_properties())

    def test_json_output(self):
        ms_msg = MsOxMessage(TEST_COMPLETE_MSG)
        self.assertTrue(ms_msg.get_message_as_json())

    def test_save_as_eml_1(self):
        ms_msg = MsOxMessage(TEST_COMPLETE_MSG)
        self.assertTrue(ms_msg.save_email_file(TEST_FILES))

    def test_save_as_eml_2(self):
        ms_msg = MsOxMessage(TEST_ATTACHED_EML)
        self.assertTrue(ms_msg.save_email_file(TEST_FILES))

    def test_save_as_eml_3(self):
        ms_msg = MsOxMessage(TEST_NESTED_MSG)
        self.assertTrue(ms_msg.save_email_file(TEST_FILES))


class PropertyTypeResolutionTests(unittest.TestCase):
    """The MAPI property type must come from the authoritative position in the
    stream name (``__substg1.0_<4-hex id><4-hex type>``), not from the static
    ID map, which is unreliable for named (>= 0x8000) properties.
    """

    def test_named_property_type_read_from_stream_name(self):
        # 0x8005 is a named property whose stream encodes the real type 0x101F
        # (PtypMultipleString).  The static ID map guesses 0x001F (PtypString),
        # which previously caused string data to be decoded as an integer.
        details = Message._get_canonical_property_name("__substg1.0_8005101F")
        self.assertEqual(details["data_type"], "0x101F")

    def test_multivalue_element_stream_type(self):
        # Per-element streams carry an index suffix that must not be mistaken
        # for the type; the type is still taken from positions 4:8.
        details = Message._get_canonical_property_name("__substg1.0_8005101F-00000002")
        self.assertEqual(details["data_type"], "0x101F")

    def test_standard_property_type_unchanged(self):
        # When the embedded type already matches the map there is no regression.
        details = Message._get_canonical_property_name("__substg1.0_8004001F")
        self.assertEqual(details["data_type"], "0x001F")
