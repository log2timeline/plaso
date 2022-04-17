# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Docker layer configuration files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class DockerLayerConfigurationEventData(events.EventData):
  """Docker layer configuration event data.

  Attributes:
    command: the command used which made Docker create a new layer.
    layer_identifier: the identifier of the current Docker layer (SHA-1).
  """

  DATA_TYPE = 'docker:layer:configuration'

  def __init__(self):
    """Initializes event data."""
    super(DockerLayerConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.command = None
    self.layer_identifier = None


class DockerLayerConfigurationJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Docker layer configuration files.

  This parser handles per Docker layer configuration files stored in:
  DOCKER_DIR/graph/<layer_identifier>/json
  """

  NAME = 'docker_layer_config'
  DATA_FORMAT = 'Docker layer configuration file'

  def _GetLayerIdentifierFromPath(self, parser_mediator):
    """Extracts a layer (or graph) identifier from a path.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.

    Returns:
      str: layer identifier.
    """
    file_entry = parser_mediator.GetFileEntry()
    file_system = file_entry.GetFileSystem()

    path_segments = file_system.SplitPath(file_entry.path_spec.location)
    # TODO: validate format of layer identifier.
    return path_segments[-2]

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses a Docker layer configuration record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the configuration record.
    """
    created = self._GetJSONValue(json_dict, 'created')
    if created:
      container_configuration = self._GetJSONValue(
          json_dict, 'container_config', default_value={})
      commands = self._GetJSONValue(
          container_configuration, 'Cmd', default_value=[])

      event_data = DockerLayerConfigurationEventData()
      event_data.command = ' '.join([
          command.replace('\t', '').strip() for command in commands])
      event_data.layer_identifier = self._GetLayerIdentifierFromPath(
          parser_mediator)

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(created)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse created time string: {0:s} with error: '
            '{1!s}').format(created, exception))
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the configuration record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    container_configuration = json_dict.get('container_config') or None
    docker_version = json_dict.get('docker_version') or None

    if None in (container_configuration, docker_version):
      return False

    return True


jsonl_parser.JSONLParser.RegisterPlugin(DockerLayerConfigurationJSONLPlugin)
