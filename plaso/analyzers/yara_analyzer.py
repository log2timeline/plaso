# -*- coding: utf-8 -*-
"""The Yara analyzer implementation"""

import logging

import yara

from plaso.containers import analyzer_result
from plaso.analyzers import interface
from plaso.analyzers import manager


class YaraAnalyzer(interface.BaseAnalyzer):
  """This class provides Yara matching functionality."""

  NAME = u'yara'

  INCREMENTAL = False

  DESCRIPTION = u'Matches Yara rules over input data.'

  def __init__(self):
    """Initializes the Yara analyzer."""
    super(YaraAnalyzer, self).__init__()
    self._rules = None
    self._matches = []

  def SetRules(self, rules_string):
    """Sets the rules that the Yara analyzer will use.

    Args:
      rules_string(str): Yara rule definitions
    """
    self._rules = yara.compile(source=rules_string)

  def Analyze(self, data):
    """Analyzes data, attempting to match Yara rules to it.

    Args:
      data(str): a string of data.
    """
    if not self._rules:
      return
    try:
      self._matches = self._rules.match(data=data, timeout=60)
    except yara.YaraTimeoutError:
      logging.error(u'Could not process file in time.')
    except yara.YaraError:
      logging.error(u'Error processing file with Yara.')

  def Update(self, data):
    """Anal"""

  def GetResults(self):
    """Retrieves the results of the processing of all data.

    Returns:
      list[AnalyzerResult): results.
    """
    results = []
    for match in self._matches:
      result = analyzer_result.AnalyzerResult()
      result.analyzer_name = self.NAME
      result.attribute_name = u'yara_match'
      result.attribute_value = match.rule
      results.append(result)
    return results

  def Reset(self):
    """Resets the internal state of the analyzer."""
    self._matches = []


manager.AnalyzersManager.RegisterAnalyzer(YaraAnalyzer)
