# -*- coding: utf-8 -*-
"""Parser for Docker configuration and log files."""

from __future__ import unicode_literals

import codecs
import json
import os

from dfvfs.helpers import text_file

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import interface


class DockerJSONContainerLogEventData(events.EventData):
  """Docker container's log event data.

  Attributes:
    container_id (str): identifier of the container (sha256).
    log_line (str): log line.
    log_source (str): log source.
  """

  DATA_TYPE = 'docker:json:container:log'

  def __init__(self):
    """Initializes event data."""
    super(DockerJSONContainerLogEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.container_id = None
    self.log_line = None
    self.log_source = None


class DockerJSONContainerEventData(events.EventData):
  """Docker container's configuration file event data.

  Attributes:
    action (str): whether the container was created, started, or finished.
    container_id (str): identifier of the container (SHA256).
    container_name (str): name of the container.
  """

  DATA_TYPE = 'docker:json:container'

  def __init__(self):
    """Initializes event data."""
    super(DockerJSONContainerEventData, self).__init__(data_type=self.DATA_TYPE)
    self.container_id = None
    self.container_name = None
    self.action = None


class DockerJSONLayerEventData(events.EventData):
  """Docker filesystem layer configuration file event data.

  Attributes:
    command: the command used which made Docker create a new layer
    layer_id: the identifier of the current Docker layer (sha1)
  """

  DATA_TYPE = 'docker:json:layer'

  def __init__(self):
    """Initializes event data."""
    super(DockerJSONLayerEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.layer_id = None


class DockerJSONParser(interface.FileObjectParser):
  """Generates various events from Docker json config and log files.

  This handles :
  * Per container config file
    DOCKER_DIR/containers/<container_id>/config.json
  * Per container stdout/stderr output log
    DOCKER_DIR/containers/<container_id>/<container_id>-json.log
  * Filesystem layer config files
    DOCKER_DIR/graph/<layer_id>/json
  """

  NAME = 'dockerjson'
  DESCRIPTION = 'Parser for JSON Docker files.'

  _ENCODING = 'utf-8'

  def _GetIdentifierFromPath(self, parser_mediator):
    """Extracts a container or a graph ID from a JSON file's path.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.

    Returns:
      str: container or graph identifier.
    """
    file_entry = parser_mediator.GetFileEntry()
    path = file_entry.path_spec.location
    file_system = file_entry.GetFileSystem()
    path_segments = file_system.SplitPath(path)
    return path_segments[-2]

  def _ParseLayerConfigJSON(self, parser_mediator, file_object):
    """Extracts events from a Docker filesystem layer configuration file.

    The path of each filesystem layer config file is:
    DOCKER_DIR/graph/<layer_id>/json

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file is not a valid layer config file.
    """
    file_content = file_object.read()
    file_content = codecs.decode(file_content, self._ENCODING)

    json_dict = json.loads(file_content)

    if 'docker_version' not in json_dict:
      raise errors.UnableToParseFile(
          'not a valid Docker layer configuration file, missing '
          '\'docker_version\' key.')

    if 'created' in json_dict:
      layer_creation_command_array = [
          x.strip() for x in json_dict['container_config']['Cmd']]
      layer_creation_command = ' '.join(layer_creation_command_array).replace(
          '\t', '')

      event_data = DockerJSONLayerEventData()
      event_data.command = layer_creation_command
      event_data.layer_id = self._GetIdentifierFromPath(parser_mediator)

      timestamp = timelib.Timestamp.FromTimeString(json_dict['created'])
      event = time_events.TimestampEvent(
          timestamp, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseContainerConfigJSON(self, parser_mediator, file_object):
    """Extracts events from a Docker container configuration file.

    The path of each container config file is:
    DOCKER_DIR/containers/<container_id>/config.json

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file is not a valid container config file.
    """
    file_content = file_object.read()
    file_content = codecs.decode(file_content, self._ENCODING)

    json_dict = json.loads(file_content)

    if 'Driver' not in json_dict:
      raise errors.UnableToParseFile(
          'not a valid Docker container configuration file, ' 'missing '
          '\'Driver\' key.')

    container_id_from_path = self._GetIdentifierFromPath(parser_mediator)
    container_id_from_json = json_dict.get('ID', None)
    if not container_id_from_json:
      raise errors.UnableToParseFile(
          'not a valid Docker layer configuration file, the \'ID\' key is '
          'missing from the JSON dict (should be {0:s})'.format(
              container_id_from_path))

    if container_id_from_json != container_id_from_path:
      raise errors.UnableToParseFile(
          'not a valid Docker container configuration file. The \'ID\' key of '
          'the JSON dict ({0:s}) is different from the layer ID taken from the'
          ' path to the file ({1:s}) JSON file.)'.format(
              container_id_from_json, container_id_from_path))

    if 'Config' in json_dict and 'Hostname' in json_dict['Config']:
      container_name = json_dict['Config']['Hostname']
    else:
      container_name = 'Unknown container name'

    event_data = DockerJSONContainerEventData()
    event_data.container_id = container_id_from_path
    event_data.container_name = container_name

    if 'State' in json_dict:
      if 'StartedAt' in json_dict['State']:
        event_data.action = 'Container Started'

        timestamp = timelib.Timestamp.FromTimeString(
            json_dict['State']['StartedAt'])
        event = time_events.TimestampEvent(
            timestamp, definitions.TIME_DESCRIPTION_START)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if 'FinishedAt' in json_dict['State']:
        if json_dict['State']['FinishedAt'] != '0001-01-01T00:00:00Z':
          event_data.action = 'Container Finished'

          # If the timestamp is 0001-01-01T00:00:00Z, the container
          # is still running, so we don't generate a Finished event
          timestamp = timelib.Timestamp.FromTimeString(
              json_dict['State']['FinishedAt'])
          event = time_events.TimestampEvent(
              timestamp, definitions.TIME_DESCRIPTION_END)
          parser_mediator.ProduceEventWithEventData(event, event_data)

    created_time = json_dict.get('Created', None)
    if created_time:
      event_data.action = 'Container Created'

      timestamp = timelib.Timestamp.FromTimeString(created_time)
      event = time_events.TimestampEvent(
          timestamp, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _ParseContainerLogJSON(self, parser_mediator, file_object):
    """Extract events from a Docker container log files.

    The format is one JSON formatted log message per line.

    The path of each container log file (which logs the container stdout and
    stderr) is:
    DOCKER_DIR/containers/<container_id>/<container_id>-json.log

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.
    """
    container_id = self._GetIdentifierFromPath(parser_mediator)

    text_file_object = text_file.TextFile(file_object)
    for log_line in text_file_object:
      json_log_line = json.loads(log_line)

      time = json_log_line.get('time', None)
      if not time:
        continue

      event_data = DockerJSONContainerLogEventData()
      event_data.container_id = container_id
      event_data.log_line = json_log_line.get('log', None)
      event_data.log_source = json_log_line.get('stream', None)
      # TODO: pass line number to offset or remove.
      event_data.offset = 0

      timestamp = timelib.Timestamp.FromTimeString(time)

      event = time_events.TimestampEvent(
          timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses various Docker configuration and log files in JSON format.

    This methods checks whether the file_object points to a docker JSON config
    or log file, and calls the corresponding _Parse* function to generate
    Events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
      ValueError: if the JSON file cannot be decoded.
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.UnableToParseFile(
          'is not a valid JSON file, missing opening brace.')

    file_object.seek(0, os.SEEK_SET)

    file_entry = parser_mediator.GetFileEntry()

    file_system = file_entry.GetFileSystem()

    json_file_path = parser_mediator.GetDisplayName()
    split_path = file_system.SplitPath(json_file_path)
    try:
      if 'containers' in split_path:
        # For our intent, both version of the config file can be parsed
        # the same way
        if split_path[-1] in ['config.json', 'config.v2.json']:
          self._ParseContainerConfigJSON(parser_mediator, file_object)
        if json_file_path.endswith('-json.log'):
          self._ParseContainerLogJSON(parser_mediator, file_object)
      elif 'graph' in split_path:
        if 'json' in split_path:
          self._ParseLayerConfigJSON(parser_mediator, file_object)
    except ValueError as exception:
      if exception == 'No JSON object could be decoded':
        raise errors.UnableToParseFile(exception)
      else:
        raise


manager.ParsersManager.RegisterParser(DockerJSONParser)
