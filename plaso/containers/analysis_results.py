# -*- coding: utf-8 -*-
"""Analysis result attribute container."""

from plaso.containers import interface
from plaso.containers import manager


class BrowserSearchAnalysisResult(interface.AttributeContainer):
  """Browser search analyzer result attribute container.

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
    """Initializes a browser search analyzer result attribute container.

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


manager.AttributeContainersManager.RegisterAttributeContainers([
    BrowserSearchAnalysisResult])
