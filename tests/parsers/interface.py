#!/usr/bin/env python3
"""Tests for the parsers and plugins interface classes."""

import unittest

from plaso.parsers import interface
from plaso.parsers import plugins

from tests.parsers import test_lib


class TestParserWithPlugins(interface.BaseParser):
    """Test parser with plugins."""

    NAME = "test_parser_with_plugins"
    DATA_FORMAT = "Test parser with plugins"

    _plugin_classes = {}


class TestPlugin(plugins.BasePlugin):
    """Test plugin."""

    NAME = "test_plugin"
    DATA_FORMAT = "Test plugin"


class BaseParserTest(test_lib.ParserTestCase):
    """Tests for the parser interface."""

    # pylint: disable=protected-access

    def testEnablePlugins(self):
        """Tests the EnablePlugins function."""
        parser = interface.BaseParser()

        parser.EnablePlugins([])
        self.assertEqual(len(parser._plugins_per_name), 0)

        parser.EnablePlugins(parser.ALL_PLUGINS)
        self.assertEqual(len(parser._plugins_per_name), 0)

    def testGetPluginNames(self):
        """Tests the GetPluginNames function."""
        plugin_names = TestParserWithPlugins.GetPluginNames()
        self.assertEqual(plugin_names, [])

        TestParserWithPlugins.RegisterPlugin(TestPlugin)

        try:
            plugin_names = TestParserWithPlugins.GetPluginNames()
            self.assertEqual(plugin_names, ["test_plugin"])

        finally:
            TestParserWithPlugins.DeregisterPlugin(TestPlugin)

    def testGetPluginObjectByName(self):
        """Tests the GetPluginObjectByName function."""
        TestParserWithPlugins.RegisterPlugin(TestPlugin)

        try:
            plugin = TestParserWithPlugins.GetPluginObjectByName("test_plugin")
            self.assertIsInstance(plugin, TestPlugin)

            plugin = TestParserWithPlugins.GetPluginObjectByName("bogus")
            self.assertIsNone(plugin)

        finally:
            TestParserWithPlugins.DeregisterPlugin(TestPlugin)

    def testGetPlugins(self):
        """Tests the GetPlugins function."""
        plugin_tuples = list(TestParserWithPlugins.GetPlugins())
        self.assertEqual(plugin_tuples, [])

        TestParserWithPlugins.RegisterPlugin(TestPlugin)

        try:
            plugin_tuples = list(TestParserWithPlugins.GetPlugins())
            self.assertEqual(plugin_tuples, [("test_plugin", TestPlugin)])

        finally:
            TestParserWithPlugins.DeregisterPlugin(TestPlugin)

    def testInitialize(self):
        """Tests the initialization."""
        parser = interface.BaseParser()

        self.assertIsNotNone(parser)
        self.assertIsNone(parser._default_plugin)
        self.assertEqual(parser._plugins_per_name, {})

    def testSupportsPlugins(self):
        """Tests the SupportsPlugins function."""
        self.assertFalse(interface.BaseParser.SupportsPlugins())
        self.assertTrue(TestParserWithPlugins.SupportsPlugins())

    # The DeregisterPlugin and RegisterPlugin functions are tested in manager.py


if __name__ == "__main__":
    unittest.main()
