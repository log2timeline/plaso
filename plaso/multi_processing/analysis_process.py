# -*- coding: utf-8 -*-
"""The multi-process analysis process."""

import multiprocessing

from plaso.analysis import mediator as analysis_mediator
from plaso.engine import plaso_queue
from plaso.multi_processing import base_process


class AnalysisProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing analysis process.

  Attributes:
    completion_event (Optional[Multiprocessing.Event]): set when the
        analysis plugin is complete.
    plugin (AnalysisPlugin): analysis plugin run by the process.
  """

  def __init__(
      self, analysis_plugin_output_queue, knowledge_base, plugin,
      data_location=None, **kwargs):
    """Initializes an analysis process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      analysis_plugin_output_queue (Queue): analysis plugin output queue.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for analysis.
      plugin: the plugin running in the process (instance of AnalysisProcess).
      data_location (Optional[str]): path to the location that data files
          should be loaded from.
    """
    super(AnalysisProcess, self).__init__(**kwargs)
    self._abort = False
    self._analysis_plugin_output_queue = analysis_plugin_output_queue
    self._data_location = data_location
    self._knowledge_base = knowledge_base

    self.completion_event = multiprocessing.Event()
    self.plugin = plugin

  def _GetStatus(self):
    """Returns status information.

    Returns:
      dict[str, object]: status attributes, indexed by name.
    """
    return {}

  def _Main(self):
    """The main loop."""
    analysis_report_queue_producer = plaso_queue.ItemQueueProducer(
        self._analysis_plugin_output_queue)

    mediator = analysis_mediator.AnalysisMediator(
        analysis_report_queue_producer, self._knowledge_base,
        completion_event=self.completion_event,
        data_location=self._data_location)

    self.plugin.RunPlugin(mediator)

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
