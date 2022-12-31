# -*- coding: utf-8 -*-
"""Analysis result attribute containers."""

from acstore.containers import interface
from acstore.containers import manager


class BrowserSearchAnalysisResult(interface.AttributeContainer):
  """Browser search analysis plugin result container.

  Attributes:
    number_of_queries (int): number of times the search engine was queried.
    search_engine (str): search engine that was queried.
    search_term (str): term searched for.
  """

  CONTAINER_TYPE = 'browser_search_analysis_result'

  SCHEMA = {
      'number_of_queries': 'int',
      'search_engine': 'str',
      'search_term': 'str'}

  def __init__(
      self, number_of_queries=None, search_engine=None, search_term=None):
    """Initializes a browser search analysis plugin result container.

    Args:
      number_of_queries (Optional[int]): number of times the search engine was
          queried.
      search_engine (Optional[str]): search engine that was queried.
      search_term (Optional[str]): term searched for.
    """
    super(BrowserSearchAnalysisResult, self).__init__()
    self.number_of_queries = number_of_queries
    self.search_engine = search_engine
    self.search_term = search_term


class ChromeExtensionAnalysisResult(interface.AttributeContainer):
  """Chrome extension analysis plugin result container.

  Attributes:
    extension (str): name of the Chrome extension.
    extension_identifier (str): identifier of the Chrome extension.
    username (str): name of a user that has installed the Chrome extension.
  """

  CONTAINER_TYPE = 'chrome_extension_analysis_result'

  SCHEMA = {
      'extension': 'str',
      'extension_identifier': 'str',
      'username': 'str'}

  def __init__(
      self, extension=None, extension_identifier=None, username=None):
    """Initializes a Chrome extension analysis plugin result container.

    Args:
      extension (Optional[str]): name of the Chrome extension.
      extension_identifier (Optional[str]): identifier of the Chrome extension.
      username (Optional[str]): name of a user that has installed the Chrome
          extension.
    """
    super(ChromeExtensionAnalysisResult, self).__init__()
    self.extension = extension
    self.extension_identifier = extension_identifier
    self.username = username


manager.AttributeContainersManager.RegisterAttributeContainers([
    BrowserSearchAnalysisResult, ChromeExtensionAnalysisResult])
