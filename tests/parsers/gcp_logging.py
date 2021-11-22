# -*- coding: utf-8 -*
"""Tests for the GCP Logging parser."""

import unittest

from plaso.parsers import gcp_logging

from tests.parsers import test_lib

class GCPLoggingUnitTest(test_lib.ParserTestCase):
  """Tests for the GCP Logging parser."""

  def testParseGCPLogs(self):
    """Tests the _ParseLogJSON function."""
    parser = gcp_logging.GCPLogsParser()
    path_segments = ['gcp_logging.json']

    storage_writer = self._ParseFile(path_segments, parser)

    self.assertEqual(storage_writer.number_of_events, 9)


if __name__ == '__main__':
  unittest.main()
