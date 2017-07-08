#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Mac OS X local users plist plugin."""

import unittest

from plaso.formatters import plist  # pylint: disable=unused-import
from plaso.lib import timelib
from plaso.parsers.plist_plugins import macuser

from tests import test_lib as shared_test_lib
from tests.parsers.plist_plugins import test_lib


class MacUserPluginTest(test_lib.PlistPluginTestCase):
  """Tests for the Mac OS X local user plist plugin."""

  @shared_test_lib.skipUnlessHasTestFile([u'user.plist'])
  def testProcess(self):
    """Tests the Process function."""
    plist_name = u'user.plist'

    plugin = macuser.MacUserPlugin()
    storage_writer = self._ParsePlistFileWithPlugin(
        plugin, [plist_name], plist_name)

    self.assertEqual(storage_writer.number_of_events, 1)

    # The order in which PlistParser generates events is nondeterministic
    # hence we sort the events.
    events = list(storage_writer.GetSortedEvents())

    event = events[0]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-12-28 04:35:47')
    self.assertEqual(event.timestamp, expected_timestamp)

    self.assertEqual(event.key, u'passwordLastSetTime')
    self.assertEqual(event.root, u'/')
    expected_description = (
        u'Last time user (501) changed the password: '
        u'$ml$37313$fa6cac1869263baa85cffc5e77a3d4ee164b7'
        u'5536cae26ce8547108f60e3f554$a731dbb0e386b169af8'
        u'9fbb33c255ceafc083c6bc5194853f72f11c550c42e4625'
        u'ef113b66f3f8b51fc3cd39106bad5067db3f7f1491758ff'
        u'e0d819a1b0aba20646fd61345d98c0c9a411bfd1144dd4b'
        u'3c40ec0f148b66d5b9ab014449f9b2e103928ef21db6e25'
        u'b536a60ff17a84e985be3aa7ba3a4c16b34e0d1d2066ae178')
    self.assertEqual(event.desc, expected_description)

    expected_string = u'//passwordLastSetTime {}'.format(expected_description)
    expected_short = u'{0:s}...'.format(expected_string[:77])
    self._TestGetMessageStrings(event, expected_string, expected_short)


if __name__ == '__main__':
  unittest.main()
