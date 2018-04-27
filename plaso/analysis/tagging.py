# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tagging file."""

from __future__ import unicode_literals

import os

from efilter import api as efilter_api
from efilter import errors as efilter_errors

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import reports
from plaso.engine import tagging_file


class TaggingAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that tags events according to rules in a tagging file."""

  NAME = 'tagging'

  ENABLE_IN_EXTRACTION = True

  _EVENT_TAG_COMMENT = 'Tag applied by tagging analysis plugin.'

  _OS_TAG_FILES = {
      'macos': 'tag_macos.txt',
      'windows': 'tag_windows.txt'}

  def __init__(self):
    """Initializes a tagging analysis plugin."""
    super(TaggingAnalysisPlugin, self).__init__()
    self._autodetect_tag_file_attempt = False
    self._number_of_event_tags = 0
    self._tag_rules = None

  def _AttemptAutoDetectTagFile(self, analysis_mediator):
    """Detects which tag file is most appropriate.

    Args:
      analysis_mediator (AnalysisMediator): analysis mediator.

    Returns:
      bool: True if a tag file is autodetected.
    """
    self._autodetect_tag_file_attempt = True
    if not analysis_mediator.data_location:
      return False

    operating_system = analysis_mediator.operating_system.lower()
    filename = self._OS_TAG_FILES.get(operating_system, None)
    if not filename:
      return False

    logger.info('Using auto detected tag file: {0:s}'.format(filename))
    tag_file_path = os.path.join(analysis_mediator.data_location, filename)
    self.SetAndLoadTagFile(tag_file_path)
    return True

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: analysis report.
    """
    report_text = 'Tagging plugin produced {0:d} tags.\n'.format(
        self._number_of_event_tags)
    self._number_of_event_tags = 0
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)

  def ExamineEvent(self, mediator, event):
    """Analyzes an EventObject and tags it according to rules in the tag file.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
    """
    if self._tag_rules is None:
      if self._autodetect_tag_file_attempt:
        # There's nothing to tag with, and we've already tried to find a good
        # tag file, so there's nothing we can do with this event (or any other).
        return
      if not self._AttemptAutoDetectTagFile(mediator):
        logger.info(
            'No tag definition file specified, and plaso was not able to '
            'autoselect a tagging file. As no definitions were specified, '
            'no events will be tagged.')
        return

    try:
      matched_labels = efilter_api.apply(self._tag_rules, vars=event)
    except efilter_errors.EfilterTypeError as exception:
      logger.warning('Unable to apply efilter query with error: {0!s}'.format(
          exception))
      matched_labels = None

    if not matched_labels:
      return

    labels = list(efilter_api.getvalues(matched_labels))
    event_tag = self._CreateEventTag(event, self._EVENT_TAG_COMMENT, labels)

    mediator.ProduceEventTag(event_tag)
    self._number_of_event_tags += 1

  def SetAndLoadTagFile(self, tagging_file_path):
    """Sets the tag file to be used by the plugin.

    Args:
      tagging_file_path (str): path of the tagging file.
    """
    tag_file = tagging_file.TaggingFile(tagging_file_path)
    self._tag_rules = tag_file.GetEventTaggingRules()


manager.AnalysisPluginManager.RegisterPlugin(TaggingAnalysisPlugin)
