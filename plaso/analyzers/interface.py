# -*- coding: utf-8 -*-
"""Definitions to provide a whole-file processing framework."""

import abc


class BaseAnalyzer(object):
  """Class that provides the interface for whole-file analysis."""

  NAME = u'base_analyzer'
  DESCRIPTION = u''

  INCREMENTAL_ANALYZER = False
  SIZE_LIMIT = 32 * 1024 * 1024

  @abc.abstractmethod
  def Analyze(self, data):
    """Analyzes a block of data, updating the state of the analyzer

    Args:
      data(bytes): block of data to process.
    """

  @abc.abstractmethod
  def GetResults(self):
    """Retrieves the results of the analysis.

    Returns:
      list[AnalyzerResult]: results.
    """

  @abc.abstractmethod
  def Reset(self):
    """Resets the internal state of the analyzer."""
