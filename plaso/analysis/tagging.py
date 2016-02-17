# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tag file."""

import logging
import os

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.filters import manager as filters_manager
from plaso.lib import event


class TaggingPlugin(interface.AnalysisPlugin):
  """Analysis plugin that tags events according to rules in a tag file."""

  NAME = u'tagging'

  ENABLE_IN_EXTRACTION = True

  _OS_TAG_FILES = {u'macosx': u'tag_macosx.txt', u'windows': u'tag_windows.txt'}

  def __init__(self, incoming_queue):
    """Initializes the tagging engine object.

    Args:
      target_filename: filename for a Plaso storage file to be tagged.
      tag_input: filesystem path to the tagging input file.
      quiet: Optional boolean value to indicate the progress output should
             be suppressed.
    """
    super(TaggingPlugin, self).__init__(incoming_queue)
    self._autodetect_tag_file_attempt = False
    self._tag_rules = None
    self._tagging_file_name = None
    self._tags = []


  def SetAndLoadTagFile(self, tagging_file_path):
    """Set the tag file to be used by the plugin.

    Args:
      tagging_file_path: The path to the tagging file to use.
    """
    self._tagging_file_name = tagging_file_path
    self._tag_rules = self._ParseTaggingFile(self._tagging_file_name)

  def _AttemptAutoDetectTagFile(self, analysis_mediator):
    """Detect which tag file is most appropriate.

    Args:
      analysis_mediator: The analysis mediator (Instance of
                         AnalysisMediator).

    Returns:
      True if a tag file is autodetected, False otherwise.
    """
    self._autodetect_tag_file_attempt = True
    if not analysis_mediator.data_location:
      return False
    platform = analysis_mediator.platform
    filename = self._OS_TAG_FILES.get(platform.lower(), None)
    if not filename:
      return False
    logging.info(u'Using auto detected tag file: {0:s}'.format(filename))
    tag_file_path = os.path.join(analysis_mediator.data_location, filename)
    self.SetAndLoadTagFile(tag_file_path)
    return True

  def ExamineEvent(self, analysis_mediator, event_object, **kwargs):
    """Analyzes an EventObject and tags it according to rules in the tag file.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: The event object (instance of EventObject) to examine.
    """
    if self._tag_rules is None:
      if self._autodetect_tag_file_attempt:
        # There's nothing to tag with, and we've already tried to find a good
        # tag file, so there's nothing we can do with this event (or any other).
        return
      if not self._AttemptAutoDetectTagFile(analysis_mediator):
        logging.info(
            u'No tag definition file specified, and plaso was not able to '
            u'autoselect a tagging file. As no definitions were specified, '
            u'no events will be tagged.')
        return

    matched_tags = []
    for tag, my_filters in iter(self._tag_rules.items()):
      for my_filter in my_filters:
        if my_filter.Match(event_object):
          matched_tags.append(tag)
          break

    if not matched_tags:
      return

    event_uuid = getattr(event_object, u'uuid')
    event_tag = event.EventTag(
        comment=u'Tag applied by tagging analysis plugin.',
        event_uuid=event_uuid)
    event_tag.AddLabels(matched_tags)

    logging.debug(u'Tagging event: {0!s}'.format(event_uuid))
    self._tags.append(event_tag)

  def _ParseTaggingFile(self, input_path):
    """Parses tagging input file.

    Parses a tagging input file and returns a dictionary of tags, where each
    key represents a tag and each entry is a list of plaso filters.

    Args:
      input_path: filesystem path to the tagging input file.

    Returns:
      A dictionary whose keys are tags and values are EventObjectFilter objects.
    """
    with open(input_path, 'rb') as tag_input_file:
      tags = {}
      current_tag = u''
      for line in tag_input_file:
        line_rstrip = line.rstrip()
        line_strip = line_rstrip.lstrip()
        if not line_strip or line_strip.startswith(u'#'):
          continue

        if not line_rstrip[0].isspace():
          current_tag = line_rstrip
          tags[current_tag] = []
        else:
          if not current_tag:
            continue

          compiled_filter = filters_manager.FiltersManager.GetFilterObject(
              line_strip)
          if not compiled_filter:
            logging.warning(
                u'Tag "{0:s}" contains invalid filter: {1:s}'.format(
                    current_tag, line_strip))

          elif compiled_filter not in tags[current_tag]:
            tags[current_tag].append(compiled_filter)

    return tags

  def CompileReport(self, analysis_mediator):
    """Compiles a report of the analysis.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport(self.NAME)
    report.SetTags(self._tags)
    report.SetText([u'Tagging plugin produced {0:d} tags.'.format(
        len(self._tags))])
    return report


manager.AnalysisPluginManager.RegisterPlugin(TaggingPlugin)
