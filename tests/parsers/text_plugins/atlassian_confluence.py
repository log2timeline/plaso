#!/usr/bin/env python3
"""Tests for the atlassian-confluence.log parser."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import atlassian_confluence

from tests.parsers.text_plugins import test_lib


class AtlassianConfluenceTest(test_lib.TextPluginTestCase):
    """Tests for the Atlassian Confluence application log parser."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = atlassian_confluence.AtlassianConfluenceTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b"2022-07-12 01:08:59,489 INFO [Catalina-utility-1] "
            b"[confluence.cluster.hazelcast.HazelcastClusterManager] "
            b"startCluster Starting the cluster.\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check non-matching format.
        file_object = io.BytesIO(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testParse(self):
        """Main Test parse for Atlassian Confluence."""
        plugin = atlassian_confluence.AtlassianConfluenceTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(
            ["atlassian-confluence.log"], plugin
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 4)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "body": "Starting the cluster.",
            "data_type": "atlassian:confluence:line",
            "level": "INFO",
            "logger_class": "confluence.cluster.hazelcast.HazelcastClusterManager",
            "logger_method": "startCluster",
            "thread": "Catalina-utility-1",
            "written_time": "2022-07-12T01:08:59.489",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
