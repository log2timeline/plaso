# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Docker container configuration files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class DockerContainerConfigurationEventData(events.EventData):
  """Docker container configuration event data.

  Attributes:
    action (str): whether the container was created, started, or finished.
    container_identifier (str): identifier of the container (SHA256).
    container_name (str): name of the container.
  """

  DATA_TYPE = 'docker:container:configuration'

  def __init__(self):
    """Initializes event data."""
    super(DockerContainerConfigurationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.action = None
    self.container_identifier = None
    self.container_name = None


class DockerContainerConfigurationJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Docker container configuration files.

  This parser handles per Docker container configuration files stored in:
  DOCKER_DIR/containers/<container_identifier>/config.json
  """

  NAME = 'docker_container_config'
  DATA_FORMAT = 'Docker container configuration file'

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses a Docker container configuration record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the configuration record.
    """
    event_data = DockerContainerConfigurationEventData()
    event_data.container_identifier = self._GetJSONValue(json_dict, 'ID')

    configuration = self._GetJSONValue(json_dict, 'Config', default_value={})
    event_data.container_name = self._GetJSONValue(
        configuration, 'Hostname', default_value='Unknown container name')

    json_state = self._GetJSONValue(json_dict, 'State', default_value={})

    started_at = self._GetJSONValue(json_state, 'StartedAt')
    if started_at:
      event_data.action = 'Container Started'

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(started_at)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse container start time string: {0:s} with error: '
            '{1!s}').format(started_at, exception))
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_START)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    # If the timestamp is 0001-01-01T00:00:00Z, the container
    # is still running, so we don't generate a Finished event.
    finished_at = self._GetJSONValue(json_state, 'FinishedAt')
    if finished_at and finished_at != '0001-01-01T00:00:00Z':
      event_data.action = 'Container Finished'

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(finished_at)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse container finish at: {0:s} with error: '
            '{1!s}').format(finished_at, exception))
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_END)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    created = self._GetJSONValue(json_dict, 'Created')
    if created:
      event_data.action = 'Container Created'

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(created)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse container created: {0:s} with error: '
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
    configuration = json_dict.get('Config') or None
    driver = json_dict.get('Driver') or None
    identifier = json_dict.get('ID') or None

    if None in (configuration, driver, identifier):
      return False

    # TODO: validate format of container identifier.

    return True


jsonl_parser.JSONLParser.RegisterPlugin(DockerContainerConfigurationJSONLPlugin)
