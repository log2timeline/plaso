#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the analysis plugin manager."""

import unittest

from plaso.analysis import interface
from plaso.analysis import manager


class TestAnalysisPlugin(interface.AnalysisPlugin):
  """Test analysis plugin."""

  NAME = 'test_analysis_plugin'

  def CompileReport(self, unused_analysis_mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    return

  def ExamineEvent(
      self, unused_analysis_mediator, unused_event_object, **unused_kwargs):
    """Analyzes an event object.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """
    return


class AnalysisPluginManagerTest(unittest.TestCase):
  """Tests for the analysis plugin manager."""

  def testPluginRegistration(self):
    """Tests the RegisterPlugin and DeregisterPlugin functions."""
    # pylint: disable=protected-access
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

    plugin_set = set([name for name, _ in list(
        manager.AnalysisPluginManager.GetPlugins())])
    self.assertTrue(u'test_analysis_plugin' in plugin_set)

    manager.AnalysisPluginManager.DeregisterPlugin(TestAnalysisPlugin)


if __name__ == '__main__':
  unittest.main()
