# -*- coding: utf-8 -*-
"""An output module that saves events to OpenSearch."""

from plaso.output import manager
from plaso.output import shared_opensearch


class OpenSearchOutputModule(shared_opensearch.SharedOpenSearchOutputModule):
  """Output module for OpenSearch."""

  NAME = 'opensearch'
  DESCRIPTION = 'Saves the events into an OpenSearch database.'

  MAPPINGS_FILENAME = 'opensearch.mappings'

  def WriteHeader(self):
    """Connects to the OpenSearch server and creates the index."""
    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, self._mappings)


manager.OutputManager.RegisterOutput(
    OpenSearchOutputModule, disabled=shared_opensearch.opensearchpy is None)
