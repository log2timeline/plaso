# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tag file."""

import logging
import re
import os

from efilter import ast as efilter_ast
from efilter import api as efilter_api
from efilter import syntax as efilter_syntax
from efilter import query as efilter_query

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import events
from plaso.containers import reports
from plaso.filters import manager as filters_manager


class TagFile(efilter_syntax.Syntax):
  """Parses the Plaso tag file format."""
  # A line with no indent is a tag name.
  TAG_DECL_LINE = re.compile(r'^(\w+)')
  # A line with leading indent is one of the rules for the preceding tag.
  TAG_RULE_LINE = re.compile(r'^\s+(.+)')
  # If any of these words are in the query then it's probably objectfilter.
  OBJECTFILTER_WORDS = re.compile(
      r'\s(is|isnot|equals|notequals|inset|notinset|contains|notcontains)\s')

  _root = None

  def __init__(self, path=None, original=None, **kwargs):
    """Initializes a parser for the Plaso tag file format.

    Args:
      path: TODO
      original: TODO
    """
    if original is None:
      if path is not None:
        original = open(path, u'r')
      else:
        raise ValueError(
            u'Either a path to a tag file or a file-like object must be '
            u'provided as path or original.')
    elif path is not None:
      raise ValueError(u'Cannot provide both a path and an original.')
    elif not callable(getattr(original, u'__iter__', None)):
      raise TypeError(
          u'The "original" argument to TagFile must be an iterable of lines '
          u'(like a file object).')

    super(TagFile, self).__init__(original=original, **kwargs)


  @property
  def root(self):
    if not self._root:
      self._root = self.parse()

    return self._root


  def __del__(self):
    if not self.original.closed:
      self.original.close()


  def _parse_query(self, source):
    """Parse one of the rules as either objectfilter or dottysql.

    Example:
        _parse_query('5 + 5')
        # Returns Sum(Literal(5), Literal(5))

    Arguments:
        source: A rule in either objectfilter or dottysql syntax.

    Returns:
        The AST to represent the rule.
    """
    if self.OBJECTFILTER_WORDS.search(source):
      syntax_ = u'objectfilter'
    else:
      syntax_ = None  # Default it is.

    return efilter_query.Query(source, syntax=syntax_)


  def _parse_tagfile(self):
    """Parse the tagfile and yield tuples of tag_name, list of rule ASTs."""
    rules = None
    tag = None
    for line in self.original:
      match = self.TAG_DECL_LINE.match(line)
      if match:
        if tag and rules:
          yield tag, rules
        rules = []
        tag = match.group(1)
        continue

      match = self.TAG_RULE_LINE.match(line)
      if match:
        source = match.group(1)
        rules.append(self._parse_query(source))

  def parse(self):
    tags = []
    for tag_name, rules in self._parse_tagfile():
      tag = efilter_ast.IfElse(
          # Union will be true if any of the 'rules' match.
          efilter_ast.Union(*[rule.root for rule in rules]),
          # If so then evaluate to a string with the name of the tag.
          efilter_ast.Literal(tag_name),
          # Otherwise don't return anything.
          efilter_ast.Literal(None))
      tags.append(tag)

    self.original.close()
    # Generate a repeated value with all the tags (None will be skipped).
    return efilter_ast.Repeat(*tags)


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
    event_tag = events.EventTag(
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
    """Compiles an analysis report.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report_text = u'Tagging plugin produced {0:d} tags.\n'.format(
        len(self._tags))
    analysis_report = reports.AnalysisReport(
        plugin_name=self.NAME, text=report_text)
    analysis_report.SetTags(self._tags)
    return analysis_report


manager.AnalysisPluginManager.RegisterPlugin(TaggingPlugin)
