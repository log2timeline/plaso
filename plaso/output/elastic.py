# -*- coding: utf-8 -*-
"""An output module that saves events to Elasticsearch."""

from __future__ import unicode_literals

from plaso.output import logger
from plaso.output import manager
from plaso.output import shared_elastic


class ElasticsearchOutputModule(shared_elastic.SharedElasticsearchOutputModule):
  """Output module for Elasticsearch."""

  NAME = 'elastic'
  DESCRIPTION = 'Saves the events into an Elasticsearch database.'

  _DEFAULT_MAPPINGS = {
      'properties': {
          'application': {
              'type': 'text',
              'fields': {
                  'keyword': {
                      'type': 'keyword',
                  }
              },
          },
          'data': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
          'doc_type': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'event_type': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'exit_status': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'facility': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'file_reference': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'file_size': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'flags': {'type': 'text', 'fields': {'keyword': {'type': 'keyword'}}},
          'identifier': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'message_status': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'message_type': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'offset': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}}},
          'sequence_number': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'severity': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'source_port': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'user_identifier': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          },
          'version': {
              'type': 'text',
              'fields': {'keyword': {'type': 'keyword'}},
          }
      }
  }
  # Strings longer than this will not be analyzed by elasticsearch.
  _ELASTIC_ANALYZER_STRING_LIMIT = 10922

  def __init__(self, output_mediator):
    """Initializes an Elasticsearch output module.

    Args:
      output_mediator (OutputMediator): mediates interactions between output
          modules and other components, such as storage and dfvfs.
    """
    super(ElasticsearchOutputModule, self).__init__(output_mediator)
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

    if raw_fields:
      logger.debug('Elasticsearch adding raw (non-analyzed) fields.')
    else:
      logger.debug('Elasticsearch not adding raw (non-analyzed) fields.')

  def WriteHeader(self):
    """Connects to the Elasticsearch server and creates the index."""
    mappings = self._DEFAULT_MAPPINGS

    if self._raw_fields:
      # This cannot be static because we use the value of self._document_type
      # from arguments.
      mappings = {
          'dynamic_templates': [{
              'strings': {
                  'mapping': {
                      'fields': {
                          'raw': {
                              'ignore_above': (
                                  self._ELASTIC_ANALYZER_STRING_LIMIT),
                              'index': 'false',
                              'type': 'keyword',
                          },
                      },
                  },
                  'match_mapping_type': 'string',
              },
          }],
      }

    self._Connect()

    self._CreateIndexIfNotExists(self._index_name, mappings)


manager.OutputManager.RegisterOutput(
    ElasticsearchOutputModule, disabled=shared_elastic.elasticsearch is None)
