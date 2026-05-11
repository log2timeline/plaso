#!/usr/bin/env python3
"""Tests for the Atlassian Bitbucket audit log text parser plugin."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import bitbucket_audit

from tests.parsers.text_plugins import test_lib


class BitbucketAuditTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket audit log text parser plugin."""

  # pylint: disable=protected-access

  def test_GetStrippedValue(self):
    """Tests the _GetStrippedValue function."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()

    structure = plugin._USER_NAME.parse_string('admin')
    value = plugin._GetStrippedValue(structure, 'user_name')
    self.assertEqual(value, 'admin')

    structure = plugin._USER_NAME.parse_string('-')
    value = plugin._GetStrippedValue(structure, 'user_name')
    self.assertIsNone(value)

  def test_ParseRecord(self):
    """Tests _ParseRecord function."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()

    # Check an unsupported key.
    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(None, 'bogus_key', {})

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'0:0:0:0:0:0:0:1 | RestrictedRefAddedEvent | admin | 1400681361906 | '
        b'BITBUCKET/bitbucket | {"id":1,"value":"refs/heads/random-cleanups",'
        b'"users":["user"]} | @8KJQAGx969x538x0 | 6ywzi6\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check unsupported date and time value.
    file_object = io.BytesIO(
        b'0:0:0:0:0:0:0:1 | RestrictedRefAddedEvent | admin | 9999999999999 | '
        b'BITBUCKET/bitbucket | {"id":1,"value":"refs/heads/random-cleanups",'
        b'"users":["user"]} | @8KJQAGx969x538x0 | 6ywzi6\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testParse(self):
    """Tests the Process function."""
    plugin = bitbucket_audit.BitbucketAuditTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket-audit.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 5)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'atlassian:bitbucket:audit',
        'details': (
            '{"id":1,"value":"refs/heads/random-cleanups","users":["user"]}'),
        'entity': 'BITBUCKET/bitbucket',
        'event_name': 'RestrictedRefAddedEvent',
        'recorded_time': '2014-05-21T14:09:21.906+00:00',
        'remote_address': '0:0:0:0:0:0:0:1',
        'request_identifier': '@8KJQAGx969x538x0',
        'session_identifier': '6ywzi6',
        'user_name': 'admin'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
