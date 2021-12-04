#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the analysis plugin manager."""

import unittest

from plaso.analysis import interface
from plaso.analysis import manager

from tests import test_lib as shared_test_lib


class TestAnalysisPlugin(interface.AnalysisPlugin):
  """Test analysis plugin."""

  NAME = 'test_plugin'

  # pylint: disable=arguments-renamed
  # pylint: disable=unused-argument
  def CompileReport(self, mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
    """
    return

  # pylint: disable=arguments-differ,unused-argument
  def ExamineEvent(self, mediator, event, **unused_kwargs):
    """Analyzes an event object.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event.
    """
    return


class AnalysisPluginManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the analysis plugin manager."""

  # pylint: disable=protected-access

  def testPluginRegistration(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    number_of_plugins = len(manager.AnalysisPluginManager._plugin_classes)

    manager.AnalysisPluginManager.RegisterPlugin(TestAnalysisPlugin)
    self.assertEqual(
        len(manager.AnalysisPluginManager._plugin_classes),
        number_of_plugins + 1)

    with self.assertRaises(KeyError):
      manager.AnalysisPluginManager.RegisterPlugin(TestAnalysisPlugin)

    manager.AnalysisPluginManager.DeregisterPlugin(TestAnalysisPlugin)
    self.assertEqual(
        len(manager.AnalysisPluginManager._plugin_classes),
        number_of_plugins)

  def testGetPlugins(self):
    """Tests the GetPlugins function."""
    manager.AnalysisPluginManager.RegisterPlugin(TestAnalysisPlugin)

    # Use set-comprehension to create a set of the analysis plugin names.
    plugin_set = {name for name, _ in list(
        manager.AnalysisPluginManager.GetPlugins())}
    self.assertTrue('test_plugin' in plugin_set)

    manager.AnalysisPluginManager.DeregisterPlugin(TestAnalysisPlugin)

  # TODO: add tests for GetPluginNames.


if __name__ == '__main__':
  unittest.main()
