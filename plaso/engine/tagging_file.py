# -*- coding: utf-8 -*-
"""Tagging file."""

from __future__ import unicode_literals

import io
import re

from efilter import ast as efilter_ast
from efilter import errors as efilter_errors
from efilter import query as efilter_query

from plaso.lib import errors


class TaggingFile(object):
  """Tagging file.

  A tagging file contains one or more event tagging rules.
  """

  # A line with no indent is a tag name.
  _TAG_LABEL_LINE = re.compile(r'^(\w+)')

  # A line with leading indent is one of the rules for the preceding tag.
  _TAG_RULE_LINE = re.compile(r'^\s+(.+)')

  # If any of these words are in the query then it's probably objectfilter.
  _OBJECTFILTER_WORDS = re.compile(
      r'\s(is|isnot|equals|notequals|inset|notinset|contains|notcontains)\s')

  def __init__(self, path):
    """Initializes a tagging file.

    Args:
      path (str): path to a file that contains one or more event tagging rules.
    """
    super(TaggingFile, self).__init__()
    self._path = path

  def _ParseDefinitions(self, tagging_file_path):
    """Parses the tag file and yields tuples of label name, list of rule ASTs.

    Args:
      tagging_file_path (str): path to the tagging file.

    Yields:
      tuple: containing:

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

  def GetEventTaggingRules(self):
    """Retrieves the event tagging rules from the tagging file.

    Returns:
      efilter.ast.Expression: efilter abstract syntax tree (AST), containing the
          tagging rules.
    """
    tags = []
    for label_name, rules in self._ParseDefinitions(self._path):
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
