#!/usr/bin/env python3
"""Tests for the report attribute containers."""

import unittest

from plaso.containers import reports

from tests import test_lib as shared_test_lib


class AnalysisReportTest(shared_test_lib.BaseTestCase):
    """Tests for the analysis report attribute container."""

    def testGetAttributeNames(self):
        """Tests the GetAttributeNames function."""
        attribute_container = reports.AnalysisReport()

        expected_attribute_names = [
            "analysis_counter",
            "event_filter",
            "plugin_name",
            "text",
            "time_compiled",
        ]

        attribute_names = sorted(attribute_container.GetAttributeNames())

        self.assertEqual(attribute_names, expected_attribute_names)

    def testCopyToDict(self):
        """Tests the CopyToDict function."""
        attribute_container = reports.AnalysisReport(
            plugin_name="test_plugin", text="test report"
        )

        self.assertEqual(
            attribute_container.CopyToDict(),
            {"plugin_name": "test_plugin", "text": "test report"},
        )

        attribute_container.event_filter = "data_type is 'test:event'"
        attribute_container.time_compiled = 1281643591546875

        expected_dict = {
            "event_filter": "data_type is 'test:event'",
            "plugin_name": "test_plugin",
            "text": "test report",
            "time_compiled": 1281643591546875,
        }
        self.assertEqual(attribute_container.CopyToDict(), expected_dict)

        attribute_container = reports.AnalysisReport()
        self.assertEqual(attribute_container.CopyToDict(), {})


if __name__ == "__main__":
    unittest.main()
