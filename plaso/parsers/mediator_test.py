#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the parsers mediator."""

import unittest

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.engine import single_process
from plaso.parsers import test_lib


class ParsersMediatorTest(test_lib.ParserTestCase):
  """Tests for the parsers mediator."""

  def testGetDisplayName(self):
    """Tests the GetDisplayName function."""
    event_queue = single_process.SingleProcessQueue()
    parse_error_queue = single_process.SingleProcessQueue()

    parsers_mediator = self._GetParserMediator(
        event_queue, parse_error_queue, knowledge_base_values=None)

    with self.assertRaises(ValueError):
      _ = parsers_mediator.GetDisplayName(file_entry=None)

    test_path = self._GetTestFilePath([u'syslog.gz'])
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_OS, location=test_path)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(os_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'OS:{0:s}'.format(test_path)
    self.assertEqual(display_name, expected_display_name)

    gzip_path_spec = path_spec_factory.Factory.NewPathSpec(
        definitions.TYPE_INDICATOR_GZIP, parent=os_path_spec)
    file_entry = path_spec_resolver.Resolver.OpenFileEntry(gzip_path_spec)

    display_name = parsers_mediator.GetDisplayName(file_entry=file_entry)

    expected_display_name = u'GZIP:{0:s}'.format(test_path)
    self.assertEqual(display_name, expected_display_name)

    # TODO: add test with relative path.

  # TODO: add more tests.


if __name__ == '__main__':
  unittest.main()
