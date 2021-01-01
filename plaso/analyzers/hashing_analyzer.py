# -*- coding: utf-8 -*-
"""The hashing analyzer implementation."""

from plaso.analyzers import interface
from plaso.analyzers import logger
from plaso.analyzers import manager
from plaso.analyzers.hashers import manager as hashers_manager
from plaso.containers import analyzer_result
from plaso.lib import definitions


class HashingAnalyzer(interface.BaseAnalyzer):
  """This class contains code for calculating file hashes of input files.

  In Plaso, hashers are classes that map arbitrarily sized file content to a
  fixed size value. See: https://en.wikipedia.org/wiki/Hash_function
  """

  NAME = 'hashing'
  DESCRIPTION = 'Calculates hashes of file content.'

  PROCESSING_STATUS_HINT = definitions.STATUS_INDICATOR_HASHING

  INCREMENTAL_ANALYZER = True

  def __init__(self):
    """Initializes a hashing analyzer."""
    super(HashingAnalyzer, self).__init__()
    self._hasher_names_string = ''
    self._hashers = []

  def Analyze(self, data):
    """Updates the internal state of the analyzer, processing a block of data.

    Repeated calls are equivalent to a single call with the concatenation of
    all the arguments.

    Args:
      data (bytes): block of data from the data stream.
    """
    for hasher in self._hashers:
      hasher.Update(data)

  def GetResults(self):
    """Retrieves the hashing results.

    Returns:
      list[AnalyzerResult]: results.
    """
    results = []
    for hasher in self._hashers:
      logger.debug('Processing results for hasher {0:s}'.format(hasher.NAME))
      result = analyzer_result.AnalyzerResult()
      result.analyzer_name = self.NAME
      result.attribute_name = hasher.ATTRIBUTE_NAME
      result.attribute_value = hasher.GetStringDigest()
      results.append(result)
    return results

  def Reset(self):
    """Resets the internal state of the analyzer."""
    hasher_names = hashers_manager.HashersManager.GetHasherNamesFromString(
        self._hasher_names_string)
    self._hashers = hashers_manager.HashersManager.GetHashers(hasher_names)

  def SetHasherNames(self, hasher_names_string):
    """Sets the hashers that should be enabled.

    Args:
      hasher_names_string (str): comma separated names of hashers to enable.
    """
    hasher_names = hashers_manager.HashersManager.GetHasherNamesFromString(
        hasher_names_string)

    debug_hasher_names = ', '.join(hasher_names)
    logger.debug('Got hasher names: {0:s}'.format(debug_hasher_names))

    self._hashers = hashers_manager.HashersManager.GetHashers(hasher_names)
    self._hasher_names_string = hasher_names_string


manager.AnalyzersManager.RegisterAnalyzer(HashingAnalyzer)
