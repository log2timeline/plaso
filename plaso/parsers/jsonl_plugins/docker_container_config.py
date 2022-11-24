# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Docker container configuration files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class DockerContainerConfigurationEventData(events.EventData):
  """Docker container configuration event data.

  Attributes:
    action (str): whether the container was created, started, or finished.
    container_identifier (str): identifier of the container (SHA256).
    container_name (str): name of the container.
    creation_time (dfdatetime.DateTimeValues): date and time the container
        was created (added).
    end_time (dfdatetime.DateTimeValues): date and time the container
        was stopped.
    start_time (dfdatetime.DateTimeValues): date and time the container
        was started.
  """

  DATA_TYPE = 'docker:container:configuration'

  def __init__(self):
    """Initializes event data."""
    super(DockerContainerConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.action = None
    self.container_identifier = None
    self.container_name = None
    self.creation_time = None
    self.end_time = None
    self.start_time = None


class DockerContainerConfigurationJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Docker container configuration files.

  This parser handles per Docker container configuration files stored in:
  DOCKER_DIR/containers/<container_identifier>/config.json
  """

  NAME = 'docker_container_config'
  DATA_FORMAT = 'Docker container configuration file'

  def _ParseISO8601DateTimeString(self, parser_mediator, json_dict, name):
    """Parses an ISO8601 date and time string.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary.
      name (str): name of the value to retrieve.

    Returns:
      dfdatetime.TimeElementsInMicroseconds: date and time value or None if
          not available.
    """
    iso8601_string = self._GetJSONValue(json_dict, name)
    if not iso8601_string:
      return None

    # A FinishedAt date and time value of 0001-01-01T00:00:00Z represents
    # that the container is still running.
    if name == 'FinishedAt' and iso8601_string == '0001-01-01T00:00:00Z':
      return None

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(iso8601_string)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning((
          'Unable to parse value: {0:s} ISO8601 string: {1:s} with error: '
          '{2!s}').format(name, iso8601_string, exception))
      return None

    return date_time

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses a Docker container configuration record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the configuration record.
    """
    json_state = self._GetJSONValue(json_dict, 'State', default_value={})
    configuration = self._GetJSONValue(json_dict, 'Config', default_value={})

    event_data = DockerContainerConfigurationEventData()
    event_data.container_identifier = self._GetJSONValue(json_dict, 'ID')
    event_data.container_name = self._GetJSONValue(
        configuration, 'Hostname', default_value='Unknown container name')
    event_data.creation_time = self._ParseISO8601DateTimeString(
        parser_mediator, json_dict, 'Created')
    event_data.end_time = self._ParseISO8601DateTimeString(
        parser_mediator, json_state, 'FinishedAt')
    event_data.start_time = self._ParseISO8601DateTimeString(
        parser_mediator, json_state, 'StartedAt')

    parser_mediator.ProduceEventData(event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the configuration record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    configuration = self._GetJSONValue(json_dict, 'Config')
    driver = self._GetJSONValue(json_dict, 'Driver')
    identifier = self._GetJSONValue(json_dict, 'ID')

    if None in (configuration, driver, identifier):
      return False

    # TODO: validate format of container identifier.

    return True


jsonl_parser.JSONLParser.RegisterPlugin(DockerContainerConfigurationJSONLPlugin)
