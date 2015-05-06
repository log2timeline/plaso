# -*- coding: utf-8 -*-
"""This file contains basic interface for analysis plugins."""

import abc

from plaso.engine import queue
from plaso.lib import timelib


class AnalysisPlugin(queue.ItemQueueConsumer):
  """Class that implements the analysis plugin object interface."""

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
  def __init__(self, incoming_queue):
    """Initializes an analysis plugin.

    Args:
      incoming_queue: A queue that is used to listen to incoming events.
    """
    super(AnalysisPlugin, self).__init__(incoming_queue)
    self.plugin_type = self.TYPE_REPORT

  def _ConsumeItem(self, item, analysis_mediator=None, **kwargs):
    """Consumes an item callback for ConsumeItems.

    Args:
      item: the item object.
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      kwargs: keyword arguments to pass to the _ConsumeItem callback.
    """
    # TODO: rename to ExamineItem.
    self.ExamineEvent(analysis_mediator, item, **kwargs)

  @property
  def plugin_name(self):
    """Return the name of the plugin."""
    return self.NAME

  @abc.abstractmethod
  def CompileReport(self, analysis_mediator):
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

  @abc.abstractmethod
  def ExamineEvent(self, analysis_mediator, event_object, **kwargs):
    """Analyzes an event object.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """

  def RunPlugin(self, analysis_mediator):
    """For each item in the queue send the read event to analysis.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
    """
    self.ConsumeItems(analysis_mediator=analysis_mediator)

    analysis_report = self.CompileReport(analysis_mediator)

    if analysis_report:
      # TODO: move this into the plugins?
      analysis_report.time_compiled = timelib.Timestamp.GetNow()
      analysis_mediator.ProduceAnalysisReport(
          analysis_report, plugin_name=self.plugin_name)
