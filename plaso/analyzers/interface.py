# -*- coding: utf-8 -*-
"""Definitions to provide a whole-file processing framework."""

import abc


class BaseAnalyzer(object):
  """Class that provides the interface for whole-file analysis."""

  NAME = u'base_analyzer'
  DESCRIPTION = u''

  INCREMENTAL = False
  SIZE_LIMIT = 32 * 1024 * 1024

  @abc.abstractmethod
  def Analyze(self, data):
    """Analyzes a block of data, updating the state of the analyzer

    Args:
      data(str): a string of data to process.
    """

  def Update(self, data):
    """Updates the current state of the analyzer with a new block of data.

    Repeated calls to update are equivalent to one single call with the
    concatenation of the arguments.

    Args:
      data(str): data with which to update the context of the analyzer.

    Raises:
      NotImplementedError: if the Analyzer does not support incremental
          updates.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def GetResults(self):
    """Retrieves the results of the analysis of all data.

    Returns:
      list(AnalyzerResult): results.
    """
    raise NotImplementedError

  @abc.abstractmethod
  def Reset(self):
    """Resets the internal state of the analyzer."""
