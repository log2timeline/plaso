# -*- coding: utf-8 -*-
"""Analyzer that matches Yara rules."""

import yara

try:
  from yara import Error as YaraError
except ImportError:
  from yara import YaraError

try:
  from yara import TimeoutError as YaraTimeoutError
except ImportError:
  from yara import YaraTimeoutError

from plaso.analyzers import interface
from plaso.analyzers import logger
from plaso.analyzers import manager
from plaso.containers import analyzer_result
from plaso.lib import definitions


class YaraAnalyzer(interface.BaseAnalyzer):
  """Analyzer that matches Yara rules."""

  # pylint: disable=no-member

  NAME = 'yara'
  DESCRIPTION = 'Matches Yara rules over input data.'

  PROCESSING_STATUS_HINT = definitions.STATUS_INDICATOR_YARA_SCAN

  INCREMENTAL_ANALYZER = False

  _ATTRIBUTE_NAME = 'yara_match'
  _MATCH_TIMEOUT = 60

  def __init__(self):
    """Initializes the Yara analyzer."""
    super(YaraAnalyzer, self).__init__()
    self._matches = []
    self._rules = None

  def Analyze(self, data):
    """Analyzes a block of data, attempting to match Yara rules to it.

    Args:
      data(bytes): a block of data.
    """
    if not self._rules:
      return

    try:
      self._matches = self._rules.match(data=data, timeout=self._MATCH_TIMEOUT)

    except YaraTimeoutError:
      logger.error('Could not process file within timeout: {0:d}'.format(
          self._MATCH_TIMEOUT))

    except YaraError as exception:
      logger.error('Error processing file with Yara: {0!s}.'.format(
          exception))

  def GetResults(self):
    """Retrieves results of the most recent analysis.

    Returns:
      list[AnalyzerResult]: results.
    """
    result = analyzer_result.AnalyzerResult()
    result.analyzer_name = self.NAME
    result.attribute_name = self._ATTRIBUTE_NAME
    result.attribute_value = [match.rule for match in self._matches]
    return [result]

  def Reset(self):
    """Resets the internal state of the analyzer."""
    self._matches = []

  def SetRules(self, rules_string):
    """Sets the rules that the Yara analyzer will use.

    Args:
      rules_string(str): Yara rule definitions
    """
    self._rules = yara.compile(source=rules_string)


manager.AnalyzersManager.RegisterAnalyzer(YaraAnalyzer)
