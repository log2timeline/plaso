#!/usr/bin/env python3
"""Tests for the Atlassian Bitbucket access log text parser plugin."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import bitbucket_access

from tests.parsers.text_plugins import test_lib


class BitbucketAccessTextPluginTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Bitbucket access log text parser plugin."""

  # pylint: disable=protected-access

  def test_GetStrippedValue(self):
    """Tests the _GetStrippedValue function."""
    plugin = bitbucket_access.BitbucketAccessTextPlugin()

    structure = plugin._USER_NAME.parse_string('eaccru')
    value = plugin._GetStrippedValue(structure, 'user_name')
    self.assertEqual(value, 'eaccru')

    structure = plugin._USER_NAME.parse_string('-')
    value = plugin._GetStrippedValue(structure, 'user_name')
    self.assertIsNone(value)

  def test_ParseRecord(self):
    """Tests the _ParseRecord function."""
    plugin = bitbucket_access.BitbucketAccessTextPlugin()

    # Check an unsupported key.
    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(None, 'bogus_key', {})

  def test_ParseTimeElements(self):
    """Tests the _ParseTimeElements function."""
    plugin = bitbucket_access.BitbucketAccessTextPlugin()

    time_elements_structure = plugin._DATE_TIME.parse_string(
        '2012-10-29 00:06:26,838')
    date_time = plugin._ParseTimeElements(time_elements_structure)
    self.assertIsNotNone(date_time)

    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements('bogus')

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = bitbucket_access.BitbucketAccessTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'63.246.22.199,172.16.1.187 | https | o@9K7Z3NNx6x3112x1 | eaccru | '
        b'2012-10-29 00:06:26,838 | "GET '
        b'/git/STASH/mina-sshd-fork.git/info/refs HTTP/1.1" | "" '
        b'"git/1.7.4.1" | 200 | 13 | 0 | refs, cache:hit | 101 | tmpqqw |\n')
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
        b'63.246.22.199,172.16.1.187 | https | o@9K7Z3NNx6x3112x1 | eaccru | '
        b'2012-99-99 00:06:26,838 | "GET '
        b'/git/STASH/mina-sshd-fork.git/info/refs HTTP/1.1" | "" '
        b'"git/1.7.4.1" | 200 | 13 | 0 | refs, cache:hit | 101 | tmpqqw |\n')
    text_reader = text_parser.EncodedTextReader(
        file_object, encoding=plugin.ENCODING)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testProcess(self):
    """Tests the Process function."""
    plugin = bitbucket_access.BitbucketAccessTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-bitbucket-access.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 8)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'data_type': 'atlassian:bitbucket:access',
        'http_request_method': 'GET',
        'http_request_uri': '/git/STASH/mina-sshd-fork.git/info/refs',
        'http_request_user_agent': 'git/1.7.4.1',
        'http_response_bytes_read': 13,
        'http_response_bytes_written': 0,
        'http_response_code': 200,
        'http_version': 'HTTP/1.1',
        'labels': 'refs, cache:hit',
        'mesh_execution_identifier': None,
        'protocol': 'https',
        'recorded_time': '2012-10-29T00:06:26.838',
        'remote_address': '63.246.22.199,172.16.1.187',
        'request_identifier': 'o@9K7Z3NNx6x3112x1',
        'request_time': 101,
        'session_identifier': 'tmpqqw',
        'ssh_repository_path': None,
        'user_name': 'eaccru'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
