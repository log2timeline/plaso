# -*- coding: utf-8 -*-
"""Analysis plugin to look up file hashes in bloom database

"""
try:
  import flor
except ImportError:
  flor = None

from plaso.analysis import hash_tagging
from plaso.analysis import logger
from plaso.analysis import manager


class BloomAnalysisPlugin(hash_tagging.HashTaggingAnalysisPlugin):
  """Analysis plugin for looking up hashes in bloom file."""

  # hashlookup bloom files can handle a high load
  # so look up all files.
  DATA_TYPES = frozenset(['fs:stat', 'fs:stat:ntfs'])

  NAME = 'bloom'

  SUPPORTED_HASHES = frozenset(['sha1', 'md5', 'sha256'])

  DEFAULT_LABEL = 'bloom_present'


  def __init__(self):
    """Initializes an hashlookup bloom  analysis plugin."""
    super(BloomAnalysisPlugin, self).__init__()
    self._label = self.DEFAULT_LABEL
    self._bloom_database_path = None
    self.bloom_filter_object = None

  def _Analyze(self, hashes):
    """Looks up file hashes in hashlookup bloom file.

    Args:
      hashes (list[str]): hash values to look up.

    Returns:
      list[HashAnalysis]: analysis results, or an empty list on error.

    Raises:
      RuntimeError: when the analyzer fail to get a bloom filter object
    """

    bloom_filter = self._GetBloomFilterObject(cached=True)
    if not bloom_filter:
      raise RuntimeError('Failed to open bloom file')

    hash_analyses = []
    for digest in hashes:
      response = self._QueryHash(digest=digest, bloom_filter=bloom_filter)
      if response is not None:
        hash_analysis = hash_tagging.HashAnalysis(
          subject_hash=digest, hash_information=response)
        hash_analyses.append(hash_analysis)

    return hash_analyses

  def _GenerateLabels(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (bool): response from the hash tagging that indicates
          that the file hash was present or not.

    Returns:
      list[str]: list of labels to apply to event.
    """
    if hash_information:
      return [self._label]
    return []

  def _GetBloomFilterObject(self, cached=True):
    """Load bloom filter file in memory
    Args:
      cached (bool): should the BloomFilter be cached

    Returns:
      Optional(flor.BloomFilter): object containig a BloomFilter.
    """
    if self.bloom_filter_object:
      return self.bloom_filter_object

    logger.info('Open bloom database file {0:s}.'
              .format(self._bloom_database_path))

    if flor.BloomFilter is None:
      logger.error('Missing optional dependency : flor')
      return None

    try:
      bloom_filter = flor.BloomFilter()
      with open(self._bloom_database_path, 'rb') as f:
        bloom_filter.read(f)
    except IOError as exception:
      bloom_filter = None
      logger.error('Unable to open bloom database file {0:s} with error: {1:s}.'
                   .format(self._bloom_database_path, exception))

    if cached:
      self.bloom_filter_object = bloom_filter
      return self.bloom_filter_object
    return bloom_filter

  @staticmethod
  def _QueryHash(digest, bloom_filter):
    """Queries BloomFilter for a specific hash (upercased).

    Args:
      digest (str): hash to look up.
      bloom_filter (flor.BloomFilter): instanced BloomFilter.

    Returns:
      bool: True if the hash was found, False if not or None on error.
    """
    value_to_test = digest.upper().encode()
    return value_to_test in bloom_filter


  def SetLabel(self, label):
    """Sets the tagging label.

    Args:
      label (str): label to apply to events extracted from files that are
          present in the bloom database.
    """
    self._label = label


  def SetBloomDatabasePath(self, bloom_database_path):
    """Set the path to the bloom file containing hash

    Args:
      bloom_database_path (str): Path to the bloom file
    """
    self._bloom_database_path = bloom_database_path


  def TestLoading(self):
    """Test if the bloom file configured exist and is valid

    """
    bf = self._GetBloomFilterObject(cached=False)
    if bf:
      return True
    return False

manager.AnalysisPluginManager.RegisterPlugin(BloomAnalysisPlugin)
