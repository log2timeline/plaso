#!/usr/bin/env python3
"""Tests for the atlassian-jira.log parser."""

import io
import unittest

from plaso.lib import errors
from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import atlassian_jira

from tests.parsers.text_plugins import test_lib


class AtlassianJiraTest(test_lib.TextPluginTestCase):
  """Tests for the Atlassian Jira application log parser."""

  # pylint: disable=protected-access

  def testParseTimeElementsInvalidInput(self):
    """Tests _ParseTimeElements raises ParseError on invalid input."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()

    # A tuple with an out-of-bounds month value should raise ParseError.
    with self.assertRaises(errors.ParseError):
      plugin._ParseTimeElements((2022, 13, 1, 0, 0, 0, 0))

  def test_ParseRecord(self):
    """Tests the _ParseRecord function."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()

    # Check an unsupported key.
    with self.assertRaises(errors.ParseError):
      plugin._ParseRecord(None, 'bogus_key', {})

  def testCheckRequiredFormat(self):
    """Tests the CheckRequiredFormat function."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()
    parser_mediator = parsers_mediator.ParserMediator()

    file_object = io.BytesIO(
        b'2022-10-03 09:00:01,042 INFO [main] '
        b'[com.atlassian.jira.startup.JiraStartupLogger] start '
        b'Jira starting up.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check unsupported date and time value.
    file_object = io.BytesIO(
        b'2022-99-99 09:00:01,042 INFO [main] '
        b'[com.atlassian.jira.startup.JiraStartupLogger] start '
        b'Jira starting up.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    # Check non-matching format.
    file_object = io.BytesIO(
        b'Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new '
        b'content in image.dd.\n')
    text_reader = text_parser.EncodedTextReader(file_object)
    text_reader.ReadLines()

    self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

  def testParse(self):
    """Tests the Process function on a Jira application log file."""
    plugin = atlassian_jira.AtlassianJiraTextPlugin()
    storage_writer = self._ParseTextFileWithPlugin(
        ['atlassian-jira.log'], plugin)

    number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
        'event_data')
    self.assertEqual(number_of_event_data, 7)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'extraction_warning')
    self.assertEqual(number_of_warnings, 0)

    number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
        'recovery_warning')
    self.assertEqual(number_of_warnings, 0)

    expected_event_values = {
        'body': (
            'Jira starting up. Version : 9.2.0, Mode : EAR, Build Number : '
            '904000, Build Date : 2022-08-25, Build UID : '
            'abc12345-dead-beef-cafe-1234567890ab'),
        'data_type': 'atlassian:jira:line',
        'level': 'INFO',
        'logger_class': 'com.atlassian.jira.startup.JiraStartupLogger',
        'logger_method': 'start',
        'thread': 'main',
        'written_time': '2022-10-03T09:00:01.042'}

    event_data = storage_writer.GetAttributeContainerByIndex('event_data', 0)
    self.CheckEventData(event_data, expected_event_values)


if __name__ == '__main__':
  unittest.main()
