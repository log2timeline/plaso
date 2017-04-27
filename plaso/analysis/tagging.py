# -*- coding: utf-8 -*-
"""A plugin to tag events according to rules in a tag file."""

import logging
import re
import os

from efilter import ast as efilter_ast
from efilter import api as efilter_api
from efilter import errors as efilter_errors
from efilter import query as efilter_query

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class TaggingAnalysisPlugin(interface.AnalysisPlugin):
  """Analysis plugin that tags events according to rules in a tag file."""

  NAME = u'tagging'

  ENABLE_IN_EXTRACTION = True

  _EVENT_TAG_COMMENT = u'Tag applied by tagging analysis plugin.'

  _OS_TAG_FILES = {
      u'macosx': u'tag_macosx.txt',
      u'windows': u'tag_windows.txt'}

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

    platform = analysis_mediator.platform
    filename = self._OS_TAG_FILES.get(platform.lower(), None)
    if not filename:
      return False

    logging.info(u'Using auto detected tag file: {0:s}'.format(filename))
    tag_file_path = os.path.join(analysis_mediator.data_location, filename)
    self.SetAndLoadTagFile(tag_file_path)
    return True

  def _ParseDefinitions(self, tag_file_path):
    """Parses the tag file and yields tuples of label name, list of rule ASTs.

    Args:
      tag_file_path (str): path to the tag file.

    Yields:
      tuple: contains:

        str: label name.
        list[efilter.query.Query]: efilter queries.
    """
    queries = None
    tag = None
    with open(tag_file_path, u'r') as tag_file:
      for line in tag_file.readlines():
        label_match = self._TAG_LABEL_LINE.match(line)
        if label_match:
          if tag and queries:
            yield tag, queries
          queries = []
          tag = label_match.group(1)
          continue

        rule_match = self._TAG_RULE_LINE.match(line)
        if rule_match:
          rule = rule_match.group(1)
          query = self._ParseRule(rule)
          if query:
            queries.append(query)

      # Yield any remaining tags once we reach the end of the file.
      if tag and queries:
        yield tag, queries

  def _ParseRule(self, rule):
    """Parses a single tagging rule.

    This method attempts to detect whether the rule is written with objectfilter
    or dottysql syntax - either is acceptable.

    Example:
      _ParseRule('5 + 5')
      # Returns Sum(Literal(5), Literal(5))

    Args:
      rule (str): rule in either objectfilter or dottysql syntax.

    Returns:
      efilter.query.Query: efilter query of the rule or None.
    """
    if self._OBJECTFILTER_WORDS.search(rule):
      syntax = u'objectfilter'
    else:
      syntax = u'dottysql'

    try:
      return efilter_query.Query(rule, syntax=syntax)

    except efilter_errors.EfilterParseError as exception:
      stripped_rule = rule.rstrip()
      logging.warning(
          u'Unable to build query from rule: "{0:s}" with error: {1:s}'.format(
              stripped_rule, exception.message))

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
        logging.warning(u'All rules for label "{0:s}" are invalid.'.format(
            label_name))
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
    report_text = u'Tagging plugin produced {0:d} tags.\n'.format(
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
        logging.info(
            u'No tag definition file specified, and plaso was not able to '
            u'autoselect a tagging file. As no definitions were specified, '
            u'no events will be tagged.')
        return

    try:
      matched_labels = efilter_api.apply(self._tag_rules, vars=event)
    except efilter_errors.EfilterTypeError as exception:
      logging.warning(u'Unable to apply efilter query with error: {0:s}'.format(
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
    self._tagging_file_name = tagging_file_path
    self._tag_rules = self._ParseTaggingFile(self._tagging_file_name)


manager.AnalysisPluginManager.RegisterPlugin(TaggingAnalysisPlugin)
