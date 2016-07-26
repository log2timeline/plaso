# -*- coding: utf-8 -*-
"""The multi-process analysis process."""

import logging
import multiprocessing

from plaso.analysis import mediator as analysis_mediator
from plaso.engine import plaso_queue
from plaso.lib import errors
from plaso.lib import timelib
from plaso.multi_processing import base_process


class AnalysisProcess(base_process.MultiProcessBaseProcess):
  """Class that defines a multi-processing analysis process.

  Attributes:
    completion_event (Optional[Multiprocessing.Event]): set when the
        analysis plugin is complete.
    plugin (AnalysisPlugin): analysis plugin run by the process.
  """

  def __init__(
      self, event_queue, analysis_report_queue, knowledge_base, plugin,
      data_location=None, **kwargs):
    """Initializes an analysis process.

    Non-specified keyword arguments (kwargs) are directly passed to
    multiprocessing.Process.

    Args:
      event_queue (Queue): event input queue.
      analysis_plugin_output_queue (Queue): analysis plugin output queue.
      knowledge_base (KnowledgeBase): contains information from the source
          data needed for analysis.
      plugin (AnalysisProcess): plugin running in the process.
      data_location (Optional[str]): path to the location that data files
          should be loaded from.
    """
    super(AnalysisProcess, self).__init__(**kwargs)
    self._abort = False
    self._analysis_report_queue = analysis_report_queue
    self._data_location = data_location
    self._event_queue = event_queue
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
        self._analysis_report_queue)

    mediator = analysis_mediator.AnalysisMediator(
        analysis_report_queue_producer, self._knowledge_base,
        completion_event=self.completion_event,
        data_location=self._data_location)

    try:
      logging.debug(
          u'{0!s} (PID: {1:d}) started monitoring event queue.'.format(
              self._name, self._pid))

      while not self._abort:
        try:
          event = self._event_queue.PopItem()
        except (errors.QueueClose, errors.QueueEmpty) as exception:
          logging.debug(u'ConsumeItems exiting with exception {0:s}.'.format(
              type(exception)))
          break

        if isinstance(event, plaso_queue.QueueAbort):
          logging.debug(u'ConsumeItems exiting, dequeued QueueAbort object.')
          break

        self.plugin.ExamineEvent(mediator, event)

      logging.debug(
          u'{0!s} (PID: {1:d}) stopped monitoring event queue.'.format(
              self._name, self._pid))

    except Exception as exception:  # pylint: disable=broad-except
      logging.warning(
          u'Unhandled exception in worker: {0!s} (PID: {1:d}).'.format(
              self._name, self._pid))
      logging.exception(exception)

      self._abort = True

    # TODO: move to mediator after deprecating analysis_report_queue.
    analysis_report = self.plugin.CompileReport(mediator)
    if analysis_report:
      analysis_report.time_compiled = timelib.Timestamp.GetNow()
      mediator.ProduceAnalysisReport(
          analysis_report, plugin_name=self.plugin.plugin_name)

    self.completion_event.set()
    analysis_report_queue_producer.Close()

  def SignalAbort(self):
    """Signals the process to abort."""
    self._abort = True
