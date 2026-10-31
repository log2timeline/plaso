#!/usr/bin/env python3
"""Tests for the analysis mediator."""

import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.analysis import interface
from plaso.analysis import mediator
from plaso.containers import artifacts
from plaso.containers import events
from plaso.containers import reports
from plaso.storage.fake import writer as fake_writer

from tests.analysis import test_lib


class TestAnalysisPlugin(interface.AnalysisPlugin):
    """Test analysis plugin."""

    NAME = "test_plugin"

    # pylint: disable=unused-argument
    def ExamineEvent(self, analysis_mediator, event, event_data, event_data_stream):
        """Analyzes an event.

        Args:
          analysis_mediator (AnalysisMediator): mediates interactions between
              analysis plugins and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.
        """
        return


class TestNoReportAnalysisPlugin(TestAnalysisPlugin):
    """Test analysis plugin that does not compile a report."""

    NAME = "test_no_report_plugin"

    def CompileReport(self, analysis_mediator):
        """Compiles a report of the analysis, which this plugin does not produce.

        Args:
          analysis_mediator (AnalysisMediator): mediates interactions between
              analysis plugins and other components, such as storage and dfVFS.
        """
        return None


class AnalysisMediatorTest(test_lib.AnalysisPluginTestCase):
    """Tests for the analysis mediator."""

    def testGetDisplayNameForPathSpec(self):
        """Tests the GetDisplayNameForPathSpec function."""
        analysis_mediator = mediator.AnalysisMediator()

        test_path = self._GetTestFilePath(["syslog.gz"])
        os_path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_OS, location=test_path
        )

        display_name = analysis_mediator.GetDisplayNameForPathSpec(os_path_spec)
        self.assertEqual(display_name, f"OS:{test_path:s}")

    def testGetUsernameForPath(self):
        """Tests the GetUsernameForPath function."""
        test_user1 = artifacts.UserAccountArtifact(
            identifier="1000",
            path_separator="\\",
            user_directory="C:\\Users\\testuser1",
            username="testuser1",
        )

        analysis_mediator = mediator.AnalysisMediator(user_accounts=[test_user1])

        username = analysis_mediator.GetUsernameForPath(
            "C:\\Users\\testuser1\\Downloads"
        )
        self.assertEqual(username, "testuser1")

        username = analysis_mediator.GetUsernameForPath(
            "C:\\Users\\testuser2\\Downloads"
        )
        self.assertIsNone(username)

    def testProduceAnalysisReport(self):
        """Tests the ProduceAnalysisReport function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            analysis_mediator = mediator.AnalysisMediator()
            analysis_mediator.SetStorageWriter(storage_writer)

            analysis_mediator.ProduceAnalysisReport(TestAnalysisPlugin())

            self.assertEqual(analysis_mediator.number_of_produced_analysis_reports, 1)
            self.assertEqual(
                analysis_mediator.analysis_reports_counter["test_plugin"], 1
            )
            self.assertEqual(analysis_mediator.analysis_reports_counter["total"], 1)
            self.assertGreater(analysis_mediator.last_activity_timestamp, 0.0)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                reports.AnalysisReport.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            analysis_report = storage_writer.GetAttributeContainerByIndex(
                reports.AnalysisReport.CONTAINER_TYPE, 0
            )
            self.assertEqual(analysis_report.plugin_name, "test_plugin")

            # A plugin that does not compile a report should not produce one.
            analysis_mediator.ProduceAnalysisReport(TestNoReportAnalysisPlugin())

            self.assertEqual(analysis_mediator.number_of_produced_analysis_reports, 1)
            self.assertEqual(
                analysis_mediator.analysis_reports_counter["test_no_report_plugin"], 0
            )

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                reports.AnalysisReport.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

        finally:
            storage_writer.Close()

    def testProduceEventTag(self):
        """Tests the ProduceEventTag function."""
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()

        try:
            event = events.EventObject()
            storage_writer.AddAttributeContainer(event)

            analysis_mediator = mediator.AnalysisMediator()
            analysis_mediator.SetStorageWriter(storage_writer)

            event_tag = events.EventTag()
            event_tag.SetEventIdentifier(event.GetIdentifier())
            event_tag.AddLabels(["malware", "browser_search"])

            analysis_mediator.ProduceEventTag(event_tag)

            self.assertEqual(analysis_mediator.number_of_produced_event_tags, 1)
            self.assertEqual(analysis_mediator.event_labels_counter["malware"], 1)
            self.assertEqual(
                analysis_mediator.event_labels_counter["browser_search"], 1
            )
            self.assertEqual(analysis_mediator.event_labels_counter["total"], 2)
            self.assertGreater(analysis_mediator.last_activity_timestamp, 0.0)

            number_of_containers = storage_writer.GetNumberOfAttributeContainers(
                events.EventTag.CONTAINER_TYPE
            )
            self.assertEqual(number_of_containers, 1)

            stored_event_tag = storage_writer.GetEventTagByEventIdentifier(
                event.GetIdentifier()
            )
            self.assertEqual(
                sorted(stored_event_tag.labels), ["browser_search", "malware"]
            )

        finally:
            storage_writer.Close()

    def testSignalAbort(self):
        """Tests the SignalAbort function."""
        analysis_mediator = mediator.AnalysisMediator()

        analysis_mediator.SignalAbort()


if __name__ == "__main__":
    unittest.main()
