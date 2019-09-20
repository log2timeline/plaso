#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Trend Micro AV Log parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import networkminer

from tests.parsers import test_lib

class NetworkMinerUnitTest(test_lib.ParserTestCase):

	def testParse(self):
		"""Tests the Parse function."""
		parser = networkminer.NetworkMinerParser()
		storage_writer = self._ParseFile(['networkminer.pcap.FileInfos.csv'], parser)

		self.assertEqual(storage_writer.number_of_warnings, 0)
		self.assertEqual(storage_writer.number_of_events, 4)

if __name__ == '__main__':
  unittest.main()