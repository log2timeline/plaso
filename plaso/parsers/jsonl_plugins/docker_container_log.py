# -*- coding: utf-8 -*-
"""JSON-L parser plugin for Docker container log files."""

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import jsonl_parser
from plaso.parsers.jsonl_plugins import interface


class DockerContainerLogEventData(events.EventData):
  """Docker container log event data.

  Attributes:
    container_identifier (str): identifier of the container (SHA256).
    log_line (str): log line.
    log_source (str): log source.
  """

  DATA_TYPE = 'docker:container:log:entry'

  def __init__(self):
    """Initializes event data."""
    super(DockerContainerLogEventData, self).__init__(data_type=self.DATA_TYPE)
    self.container_identifier = None
    self.log_line = None
    self.log_source = None


class DockerContainerLogJSONLPlugin(interface.JSONLPlugin):
  """JSON-L parser plugin for Docker container log files.

  This parser handles per Docker container log files stored in:
  DOCKER_DIR/containers/<container_identifier>/<container_identifier>-json.log
  """

  NAME = 'docker_container_log'
  DATA_FORMAT = 'Docker container log file'

  def __init__(self):
    """Initializes a JSON-L parser plugin."""
    super(DockerContainerLogJSONLPlugin, self).__init__()
    self._container_identifier = None

  def _GetContainerIdentifierFromPath(self, parser_mediator):
    """Extracts a container identifier from a path.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.

    Returns:
      str: container identifier.
    """
    file_entry = parser_mediator.GetFileEntry()
    file_system = file_entry.GetFileSystem()

    path_segments = file_system.SplitPath(file_entry.path_spec.location)
    # TODO: validate format of container identifier.
    return path_segments[-2]

  def _ParseRecord(self, parser_mediator, json_dict):
    """Parses a Docker container log record.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      json_dict (dict): JSON dictionary of the log record.
    """
    if not self._container_identifier:
      self._container_identifier = self._GetContainerIdentifierFromPath(
          parser_mediator)

    time = self._GetJSONValue(json_dict, 'time')
    if not time:
      parser_mediator.ProduceExtractionWarning(
          'time value missing from log entry')

    log_line = self._GetJSONValue(json_dict, 'log', default_value='')

    event_data = DockerContainerLogEventData()
    event_data.container_identifier = self._container_identifier
    # TODO: escape special characters in log line.
    event_data.log_line = log_line
    event_data.log_source = self._GetJSONValue(json_dict, 'stream')

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(time)
    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning((
          'Unable to parse written time string: {0:s} with error: '
          '{1!s}').format(time, exception))
      date_time = dfdatetime_semantic_time.InvalidTime()

    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_WRITTEN)
    parser_mediator.ProduceEventWithEventData(event, event_data)

  def CheckRequiredFormat(self, json_dict):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      json_dict (dict): JSON dictionary of the log record.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    log = json_dict.get('log') or None
    stream = json_dict.get('stream') or None
    time = json_dict.get('time') or None

    if None in (log, stream, time):
      return False

    try:
      date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
      date_time.CopyFromStringISO8601(time)
    except ValueError:
      return False

    self._container_identifier = None

    return True


jsonl_parser.JSONLParser.RegisterPlugin(DockerContainerLogJSONLPlugin)
