#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Unit tests for the low-level MAPI property :class:`DataModel` conversions.

These exercise the byte-decoding helpers directly so that the exact decoded
value can be asserted.  MSG/MAPI stores numeric properties little-endian.
"""

import unittest

from msg_parser.data_models import DataModel, get_multi_value_offsets


class IntegerConversionTests(unittest.TestCase):
    def test_ptyp_integer16_reads_little_endian(self):
        self.assertEqual(DataModel.PtypInteger16(b"\x01\x00"), 1)
        self.assertEqual(DataModel.PtypInteger16(b"\x00\x01"), 256)

    def test_ptyp_integer32_reads_little_endian(self):
        # This is the conversion that crashed in the reported traceback.
        self.assertEqual(DataModel.PtypInteger32(b"\x01\x00\x00\x00"), 1)
        self.assertEqual(DataModel.PtypInteger32(b"\x00\x01\x00\x00"), 256)
        self.assertEqual(DataModel.PtypInteger32(b"\xff\x00\x00\x00"), 255)

    def test_ptyp_integer64_reads_little_endian(self):
        self.assertEqual(
            DataModel.PtypInteger64(b"\x01\x00\x00\x00\x00\x00\x00\x00"), 1
        )


class BooleanConversionTests(unittest.TestCase):
    def test_ptyp_boolean_true(self):
        self.assertIs(DataModel.PtypBoolean(b"\x01\x00"), True)

    def test_ptyp_boolean_false(self):
        self.assertIs(DataModel.PtypBoolean(b"\x00\x00"), False)


class MultipleValueConversionTests(unittest.TestCase):
    def test_ptyp_multiple_integer16(self):
        self.assertEqual(DataModel.PtypMultipleInteger16(b"\x01\x00\x02\x00"), [1, 2])

    def test_ptyp_multiple_integer32(self):
        self.assertEqual(
            DataModel.PtypMultipleInteger32(b"\x01\x00\x00\x00\x02\x00\x00\x00"),
            [1, 2],
        )

    def test_ptyp_multiple_integer64(self):
        data = b"\x01\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00"
        self.assertEqual(DataModel.PtypMultipleInteger64(data), [1, 2])

    def test_get_multi_value_offsets_single_entry(self):
        # ulCount == 1 takes the fixed [8] offset branch.
        ul_count, offsets = get_multi_value_offsets(b"\x01\x00\x00\x00rest")
        self.assertEqual(ul_count, 1)
        self.assertEqual(offsets, [8, len(b"\x01\x00\x00\x00rest")])


if __name__ == "__main__":
    unittest.main()
