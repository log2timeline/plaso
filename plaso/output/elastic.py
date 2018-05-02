# -*- coding: utf-8 -*-
"""An output module that saves events to Elasticsearch."""

from __future__ import unicode_literals

from elasticsearch import Elasticsearch

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_elastic


class ElasticSearchOutputModule(shared_elastic.SharedElasticsearchOutputModule):
  """Output module for Elasticsearch."""

  NAME = 'elastic'
  DESCRIPTION = 'Saves the events into an Elasticsearch database.'

  # Strings longer than this will not be analyzed by elasticsearch.
  _ELASTIC_ANALYZER_STRING_LIMIT = 10922

  def __init__(self, output_mediator):
    """Initializes an Elasticsearch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(ElasticSearchOutputModule, self).__init__(output_mediator)
    self._raw_fields = False

  def SetRawFields(self, raw_fields):
    """Set raw (non-analyzed) fields.

    This is used for sorting and aggregations in Elasticsearch.
    https://www.elastic.co/guide/en/elasticsearch/guide/current/
    multi-fields.html

    Args:
      raw_fields (bool): True if raw (non-analyzed) fields should be added.
    """
    self._raw_fields = raw_fields
    logger.info('Elasticsearch adding raw (non-analyzed) fields: {0:s}'.format(
        ', '.join(self._raw_fields)))

  def WriteHeader(self):
    """Connects to the Elasticsearch server and creates the index."""
    if self._raw_fields:
      if self._document_type not in self._mappings:
        self._mappings[self._document_type] = {}

      _raw_field_mapping = [{
          'strings': {
              'match_mapping_type': 'string',
              'mapping': {
                  'fields': {
                      'raw': {
                          'type': 'text',
                          'index': 'not_analyzed',
                          'ignore_above': self._ELASTIC_ANALYZER_STRING_LIMIT
                      }
                  }
              }
          }
      }]
      self._mappings[self._document_type]['dynamic_templates'] = (
          _raw_field_mapping)

    self._Connect()


manager.OutputManager.RegisterOutput(
    ElasticSearchOutputModule, disabled=Elasticsearch is None)
