# -*- coding: utf-8 -*-
"""This file contains basic interface for analysis plugins."""

import abc

from plaso.engine import queue
from plaso.lib import registry
from plaso.lib import timelib


class AnalysisPlugin(queue.EventObjectQueueConsumer):
  """Analysis plugin gets a copy of each read event for analysis."""

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  # The URLS should contain a list of URLs with additional information about
  # this analysis plugin.
  URLS = []

  # The name of the plugin. This is the name that is matched against when
  # loading plugins, so it is important that this name is short, concise and
  # explains the nature of the plugin easily. It also needs to be unique.
  NAME = 'Plugin'

  # A flag indicating whether or not this plugin should be run during extraction
  # phase or reserved entirely for post processing stage.
  # Typically this would mean that the plugin is perhaps too computationally
  # heavy to be run during event extraction and should rather be run during
  # post-processing.
  # Since most plugins should perhaps rather be run during post-processing
  # this is set to False by default and needs to be overwritten if the plugin
  # should be able to run during the extraction phase.
  ENABLE_IN_EXTRACTION = False

  # All the possible report types.
  TYPE_ANOMALY = 1    # Plugin that is inspecting events for anomalies.
  TYPE_STATISTICS = 2   # Statistical calculations.
  TYPE_ANNOTATION = 3    # Inspecting events with the primary purpose of
                         # annotating or tagging them.
  TYPE_REPORT = 4    # Inspecting events to provide a summary information.

  # Optional arguments to be added to the argument parser.
  # An example would be:
  #   ARGUMENTS = [('--myparameter', {
  #       'action': 'store',
  #       'help': 'This is my parameter help',
  #       'dest': 'myparameter',
  #       'default': '',
  #       'type': 'unicode'})]
  #
  # Where all arguments into the dict object have a direct translation
  # into the argparse parser.
  ARGUMENTS = []

  # We need to implement the interface for analysis plugins, but we don't use
  # command line options here, so disable checking for unused args.
  # pylint: disable=unused-argument
  def __init__(self, incoming_queue, options=None):
    """Initializes an analysis plugin.

    Args:
      incoming_queue: A queue that is used to listen to incoming events.
      options: Optional command line arguments (instance of
        argparse.Namespace). The default is None.
    """
    super(AnalysisPlugin, self).__init__(incoming_queue)
    self.plugin_type = self.TYPE_REPORT

  # pylint: enable=unused-argument
  def _ConsumeEventObject(self, event_object, analysis_context=None, **kwargs):
    """Consumes an event object callback for ConsumeEventObjects.

    Args:
      event_object: An event object (instance of EventObject).
      analysis_context: Optional analysis context object (instance of
                        AnalysisContext). The default is None.
    """
    self.ExamineEvent(analysis_context, event_object, **kwargs)

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.NAME

  @abc.abstractmethod
  def CompileReport(self, analysis_context):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      analysis_context: The analysis context object. Instance of
                        AnalysisContext.

    Returns:
      The analysis report (instance of AnalysisReport).
    """

  @abc.abstractmethod
  def ExamineEvent(self, analysis_context, event_object, **kwargs):
    """Analyzes an event object.

    Args:
      analysis_context: An analysis context object (instance of
        AnalysisContext).
      event_object: An event object (instance of EventObject).
    """

  def RunPlugin(self, analysis_context):
    """For each item in the queue send the read event to analysis.

    Args:
      analysis_context: An analysis context object (instance of
        AnalysisContext).
    """
    self.ConsumeEventObjects(analysis_context=analysis_context)

    analysis_report = self.CompileReport(analysis_context)

    if analysis_report:
      # TODO: move this into the plugins?
      analysis_report.time_compiled = timelib.Timestamp.GetNow()
      analysis_context.ProduceAnalysisReport(
          analysis_report, plugin_name=self.plugin_name)
