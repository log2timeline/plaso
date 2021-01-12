# -*- coding: utf-8 -*-
"""An output module that saves events to Elasticsearch."""

from plaso.output import manager
from plaso.output import shared_elastic


class ElasticsearchOutputModule(shared_elastic.SharedElasticsearchOutputModule):
  """Output module for Elasticsearch."""

  NAME = 'elastic'
  DESCRIPTION = 'Saves the events into an Elasticsearch database.'

  MAPPINGS_FILENAME = 'elasticsearch.mappings'

  def WriteHeader(self):
    """Connects to the Elasticsearch server and creates the index."""
    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, self._mappings)


manager.OutputManager.RegisterOutput(
    ElasticsearchOutputModule, disabled=shared_elastic.elasticsearch is None)
