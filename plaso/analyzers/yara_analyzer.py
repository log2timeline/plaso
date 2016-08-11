# -*- coding: utf-8 -*-
"""The Yara analyzer implementation"""

import logging

import yara

from plaso.analyzers import interface
from plaso.analyzers import manager
from plaso.containers import analyzer_result
from plaso.lib import definitions


class YaraAnalyzer(interface.BaseAnalyzer):
  """This class provides Yara matching functionality."""

  NAME = u'yara'
  DESCRIPTION = u'Matches Yara rules over input data.'

  PROCESSING_STATUS_HINT = definitions.PROCESSING_STATUS_YARA_SCAN

  INCREMENTAL_ANALYZER = False

  _ATTRIBUTE_NAME = u'yara_match'
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
    except yara.YaraTimeoutError:
      logging.error(u'Could not process file within timeout: {0:d}'.format(
          self._MATCH_TIMEOUT))
    except yara.YaraError as exception:
      logging.error(u'Error processing file with Yara: {0!s}.'.format(
          exception))

  def GetResults(self):
    """Retrieves results of the most recent analysis.

    Returns:
      list[AnalyzerResult]: results.
    """
    result = analyzer_result.AnalyzerResult()
    result.analyzer_name = self.NAME
    result.attribute_name = self._ATTRIBUTE_NAME
    rule_names = [match.rule for match in self._matches]
    result.attribute_value = u','.join(rule_names)
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
