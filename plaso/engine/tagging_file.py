# -*- coding: utf-8 -*-
"""Tagging file."""

from __future__ import unicode_literals

import io
import re

from plaso.filters import event_filter
from plaso.lib import errors


class TaggingFile(object):
  """Tagging file that defines one or more event tagging rules."""

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

  def GetEventTaggingRules(self):
    """Retrieves the event tagging rules from the tagging file.

    Returns:
      dict[str, FilterObject]: tagging rules, that consists of one or more
          filter objects per label.

    Raises:
      TaggingFileError: if a filter expression cannot be compiled.
    """
    tagging_rules = {}

    label_name = None
    with io.open(self._path, 'r', encoding='utf-8') as tagging_file:
      for line in tagging_file.readlines():
        line = line.rstrip()

        stripped_line = line.lstrip()
        if not stripped_line or stripped_line[0] == '#':
          continue

        if not line[0].isspace():
          label_name = line
          tagging_rules[label_name] = []
          continue

        if not label_name:
          continue

        filter_object = event_filter.EventObjectFilter()

        try:
          filter_object.CompileFilter(stripped_line)
        except errors.ParseError as exception:
          raise errors.TaggingFileError((
              'Unable to compile filter for label: {0:s} with error: '
              '{1!s}').format(label_name, exception))

        if filter_object not in tagging_rules[label_name]:
          tagging_rules[label_name].append(filter_object)

    return tagging_rules
