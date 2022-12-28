# -*- coding: utf-8 -*-
"""Analysis plugin to look up file hashes in hashlookup bloom database

Also see:
  https://circl.lu/services/hashlookup/#how-to-quickly-check-a-set-of-files-in-a-local-directory
"""

from flor import BloomFilter

from plaso.analysis import hash_tagging
from plaso.analysis import logger
from plaso.analysis import manager


class HashlookupBloomAnalysisPlugin(hash_tagging.HashTaggingAnalysisPlugin):
  """Analysis plugin for looking up hashes in hashlookup bloom file."""

  # hashlookup bloom files can handle a high load
  # so look up all files.
  DATA_TYPES = frozenset(['fs:stat', 'fs:stat:ntfs'])

  NAME = 'hashlookup_bloom'

  SUPPORTED_HASHES = frozenset(['sha1', 'md5', 'sha256'])

  DEFAULT_LABEL = 'hashlookup_present'


  def __init__(self):
    """Initializes an hashlookup bloom  analysis plugin."""
    super(HashlookupBloomAnalysisPlugin, self).__init__()
    self._label = self.DEFAULT_LABEL
    self._bloom_database_path = None
    self.blomm_filter_obj = None

  def _Analyze(self, hashes):
    """Looks up file hashes in hashlookup bloom file.

    Args:
      hashes (list[str]): hash values to look up.

    Returns:
      list[HashAnalysis]: analysis results, or an empty list on error.

    Raises:
      RuntimeError: when the analyzer fail to get a bloom filter object
    """

    bf = self._GetBloomFilterObject()
    if not bf:
      logger.error(f"Faile to open bloom file {bf}")
      raise RuntimeError('Failed to open bloom file')

    hash_analyses = []
    for digest in hashes:
      response = self._QueryHash(bf, digest)
      if response is not None:
        hash_analysis = hash_tagging.HashAnalysis(digest, response)
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
      flor.BloomFilter: object containig a BloomFilter.
    """
    if self.blomm_filter_obj:
      return self.blomm_filter_obj

    logger.info('Open bloom database file {0:s}.'
              .format(self._bloom_database_path))
    try:
      bf = BloomFilter()
      with open(self._bloom_database_path, 'rb') as f:
        bf.read(f)

    except IOError as exception:
      bf = None
      logger.error('Unable to open bloom database file {0:s} with error: {1:s}.'
                   .format(self._bloom_database_path,exception))
    if cached:
      self.blomm_filter_obj = bf
      return self.blomm_filter_obj
    return bf

  @staticmethod
  def _QueryHash(bf, digest):
    """Queries BloomFilter for a specific hash (upercase).

    Args:
      bf (flor.BloomFilter): instanced BloomFilter.
      digest (str): hash to look up.

    Returns:
      bool: True if the hash was found, False if not or None on error.
    """
    value_to_test = digest.upper().encode()
    return value_to_test in bf


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
      bloom_database_path (str): Path to thefile
    """
    self._bloom_database_path = bloom_database_path


  def TestLoading(self):
    """Test if the bloom file configured exist and is valid

    """
    bf = self._GetBloomFilterObject(cached=False)
    if bf:
      return True
    return False

manager.AnalysisPluginManager.RegisterPlugin(HashlookupBloomAnalysisPlugin)
