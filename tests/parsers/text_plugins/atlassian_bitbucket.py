#!/usr/bin/env python3
"""Tests for the Atlassian Bitbucket application log text parser plugin."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import atlassian_bitbucket

from tests.parsers.text_plugins import test_lib


class AtlassianBitbucketTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket application log text parser plugin."""

  # pylint: disable=protected-access

  def test_ParseRecord(self):
    """Tests the _ParseRecord function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()

    # Check an unsupported key.
    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(None, 'bogus_key', {})

  def test_ParseTimeElements(self):
    """Tests the _ParseTimeElements function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()

    time_elements_structure = plugin._DATE_TIME.parse_string(
        '2020-09-08 07:53:45,084')
    date_time = plugin._ParseTimeElements(time_elements_structure)
    self.assertIsNotNone(date_time)

    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements('bogus')

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'2020-09-08 07:53:45,084 INFO [main] '
        b'com.atlassian.bitbucket.internal.boot.log.BuildInfoLogger Starting '
        b'Bitbucket 7.4.0 (204e35a built on Tue Jul 07 14:31:59 NZST 2020)\n'
        b'2022-06-24 08:01:19,381 WARN [git:gc:thread-1] !!! '
        b'c.a.s.i.r.DefaultRepositorySizeCache Size calculation failed\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n'
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No change '
        b'in [/etc/netgroup]. Done\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check unsupported date and time value.
    file_object = io.BytesIO(
        b'2020-09-08 07:53:45,084 INFO [main] '
        b'com.atlassian.bitbucket.internal.boot.log.BuildInfoLogger Starting '
        b'Bitbucket 7.4.0 (204e35a built on Tue Jul 07 14:31:59 NZST 2020)\n'
        b'2022-99-99 08:01:19,381 WARN [git:gc:thread-1] !!! '
        b'c.a.s.i.r.DefaultRepositorySizeCache Size calculation failed\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testParse(self):
    """Tests the Process function."""
    plugin = atlassian_bitbucket.AtlassianBitbucketTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 6)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'Repository 0030-8a2a778e2d97e278f541-5 has been created and '
            'configured successfully'),
        'data_type': 'atlassian:bitbucket:line',
        'ip_address': '10.229.31.195',
        'level': 'INFO',
        'logger_class': 'c.a.b.m.r.DefaultRepositoryManager',
        'request_action': 'TransactionService/Transact',
        'request_identifier': '2CM38K4Fx339x113x2',
        'session_identifier': '@5XDWX5x339x568x0,4SJOMSOBx339x40x2',
        'thread': 'tx:thread-2',
        'user_name': 'admin',
        'written_time': '2022-04-12T05:39:57.408'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 1)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
