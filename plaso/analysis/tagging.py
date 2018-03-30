# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tagging file."""

from __future__ import unicode_literals

import io
import re
import os

from efilter import ast as efilter_ast
from efilter import api as efilter_api
from efilter import errors as efilter_errors
from efilter import query as efilter_query

from plaso.analysis import interface
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import reports
from plaso.lib import errors


class TaggingAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that tags events according to rules in a tag file."""

  NAME = 'tagging'

  ENABLE_IN_EXTRACTION = True

  _EVENT_TAG_COMMENT = 'Tag applied by tagging analysis plugin.'

  _OS_TAG_FILES = {
      'macos': 'tag_macos.txt',
      'windows': 'tag_windows.txt'}

  # A line with no indent is a tag name.
  _TAG_LABEL_LINE = re.compile(r'^(\w+)')
  # A line with leading indent is one of the rules for the preceding tag.
  _TAG_RULE_LINE = re.compile(r'^\s+(.+)')
  # If any of these words are in the query then it's probably objectfilter.
  _OBJECTFILTER_WORDS = re.compile(
      r'\s(is|isnot|equals|notequals|inset|notinset|contains|notcontains)\s')

  def __init__(self):
    """Initializes a tagging analysis plugin."""
    super(TaggingAnalysisPlugin, self).__init__()
    self._autodetect_tag_file_attempt = False
    self._number_of_event_tags = 0
    self._tag_rules = None
    self._tagging_file_name = None

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

  def _ParseDefinitions(self, tagging_file_path):
    """Parses the tag file and yields tuples of label name, list of rule ASTs.

    Args:
      tagging_file_path (str): path to the tagging file.

    Yields:
      tuple: contains:

        str: label name.
        list[efilter.query.Query]: efilter queries.
    """
    queries = None
    label_name = None
    with io.open(tagging_file_path, 'r', encoding='utf-8') as tagging_file:
      for line in tagging_file.readlines():
        label_match = self._TAG_LABEL_LINE.match(line)
        if label_match:
          if label_name and queries:
            yield label_name, queries

          queries = []
          label_name = label_match.group(1)
          continue

        event_tagging_expression = self._TAG_RULE_LINE.match(line)
        if not event_tagging_expression:
          continue

        tagging_rule = self._ParseEventTaggingRule(
            event_tagging_expression.group(1))
        queries.append(tagging_rule)

      # Yield any remaining tags once we reach the end of the file.
      if label_name and queries:
        yield label_name, queries

  def _ParseEventTaggingRule(self, event_tagging_expression):
    """Parses an event tagging expression.

    This method attempts to detect whether the event tagging expression is valid
    objectfilter or dottysql syntax.

    Example:
      _ParseEventTaggingRule('5 + 5')
      # Returns Sum(Literal(5), Literal(5))

    Args:
      event_tagging_expression (str): event tagging experssion either in
          objectfilter or dottysql syntax.

    Returns:
      efilter.query.Query: efilter query of the event tagging expression.

    Raises:
      TaggingFileError: when the tagging file cannot be correctly parsed.
    """
    if self._OBJECTFILTER_WORDS.search(event_tagging_expression):
      syntax = 'objectfilter'
    else:
      syntax = 'dottysql'

    try:
      return efilter_query.Query(event_tagging_expression, syntax=syntax)

    except efilter_errors.EfilterParseError as exception:
      stripped_expression = event_tagging_expression.rstrip()
      raise errors.TaggingFileError((
          'Unable to parse event tagging expressoin: "{0:s}" with error: '
          '{1!s}').format(stripped_expression, exception))

  def _ParseTaggingFile(self, tag_file_path):
    """Parses tag definitions from the source.

    Args:
      tag_file_path (str): path to the tag file.

    Returns:
      efilter.ast.Expression: efilter abstract syntax tree (AST), containing the
          tagging rules.
    """
    tags = []
    for label_name, rules in self._ParseDefinitions(tag_file_path):
      if not rules:
        continue

      tag = efilter_ast.IfElse(
          # Union will be true if any of the 'rules' match.
          efilter_ast.Union(*[rule.root for rule in rules]),
          # If so then evaluate to a string with the name of the tag.
          efilter_ast.Literal(label_name),
          # Otherwise don't return anything.
          efilter_ast.Literal(None))
      tags.append(tag)

    # Generate a repeated value with all the tags (None will be skipped).
    return efilter_ast.Repeat(*tags)

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
    self._tag_rules = self._ParseTaggingFile(tagging_file_path)
    self._tagging_file_name = tagging_file_path


manager.AnalysisPluginManager.RegisterPlugin(TaggingAnalysisPlugin)
