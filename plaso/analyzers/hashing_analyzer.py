# -*- coding: utf-8 -*-
"""The hashing analyzer implementation"""

import logging

from plaso.containers import analyzer_result
from plaso.analyzers import interface
from plaso.analyzers import manager
from plaso.analyzers.hashers import manager as hashers_manager


class HashingAnalyzer(interface.BaseAnalyzer):
  """This class contains code for calculating file hashes of input files."""
  NAME = u'hashing'

  INCREMENTAL = True

  DESCRIPTION = u'Calculates hashes of file content.'

  def __init__(self):
    """Initializes a hashing analyzer."""
    super(HashingAnalyzer, self).__init__()
    self._hashers = []
    self._hasher_names_string = u''

  def SetHasherNames(self, hasher_names_string):
    """Sets the hashers that should be enabled.

    Args:
      hasher_names_string(str): comma separated names of hashers to enable.
    """
    hasher_names = hashers_manager.HashersManager.GetHasherNamesFromString(
        hasher_names_string)
    self._hasher_names_string = hasher_names_string
    logging.debug(u'Got hasher names {0:s}'.format(hasher_names))
    self._hashers = hashers_manager.HashersManager.GetHasherObjects(
        hasher_names)
    logging.debug(u'Got hashers {0:s}'.format(self._hashers))

  def Update(self, data):
    """Updates the internal state of the analyzer.

    Args:
      data(str): data from the data stream.
    """
    if not self._hashers:
      return {}

    for hasher in self._hashers:
      hasher.Update(data)

  def Analyze(self, data):
    """Processes the contents of a data stream.

    Args:
      data(str): the content of the data stream.
    """
    self.Update(data)

  def GetResults(self):
    """Retrieves the results of the processing of all data.

    Returns:
      list(AnalyzerResult): results.
    """
    results = []
    for hasher in self._hashers:
      logging.debug(u'Processing results for hasher {0:s}'.format(hasher))
      result = analyzer_result.AnalyzerResult()
      result.analyzer_name = self.NAME
      result.attribute_name = u'{0:s}_hash'.format(hasher.NAME)
      result.attribute_value = hasher.GetStringDigest()
      results.append(result)
    return results

  def Reset(self):
    """Resets the internal state of the analyzer."""
    hasher_names = hashers_manager.HashersManager.GetHasherNamesFromString(
        self._hasher_names_string)
    self._hashers = hashers_manager.HashersManager.GetHasherObjects(
        hasher_names)


manager.AnalyzersManager.RegisterAnalyzer(HashingAnalyzer)
