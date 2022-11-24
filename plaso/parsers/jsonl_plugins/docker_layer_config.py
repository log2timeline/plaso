# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Docker layer configuration files."""

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class DockerLayerConfigurationEventData(events.EventData):
  """Docker layer configuration event data.

  Attributes:
    command: the command used which made Docker create a new layer.
    creation_time (dfdatetime.DateTimeValues): date and time the layer
        was created (added).
    layer_identifier: the identifier of the current Docker layer (SHA-1).
  """

  DATA_TYPE = 'docker:layer:configuration'

  def __init__(self):
    """Initializes event data."""
    super(DockerLayerConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.command = None
    self.creation_time = None
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
    command = None
    container_configuration = self._GetJSONValue(json_dict, 'container_config')
    if container_configuration:
      command_arguments = self._GetJSONValue(container_configuration, 'Cmd')
      if command_arguments:
        command = ' '.join([
            command_argument.replace('\t', '').strip()
            for command_argument in command_arguments])

    event_data = DockerLayerConfigurationEventData()
    event_data.command = command
    event_data.creation_time = self._ParseISO8601DateTimeString(
        parser_mediator, json_dict, 'created')
    event_data.layer_identifier = self._GetLayerIdentifierFromPath(
        parser_mediator)

    parser_mediator.ProduceEventData(event_data)

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
