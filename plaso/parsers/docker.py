# -*- coding: utf-8 -*-
"""Parser for Docker configuration and log files."""

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

  DATA_TYPE = u'docker:json:container:log'

  def __init__(self):
    """Initializes event data."""
    super(DockerJSONContainerLogEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.container_id = None
    self.log_line = None
    self.log_source = None


class DockerJSONContainerEvent(time_events.TimestampEvent):
  """Event parsed from a Docker container's configuration file.

  Attributes:
    action (str): whether the container was created, started, or finished.
    container_id (str): identifier of the container (sha256).
    container_name (str): name of the container.
  """

  DATA_TYPE = u'docker:json:container'

  def __init__(self, timestamp, event_type, attributes):
    super(DockerJSONContainerEvent, self).__init__(
        timestamp, event_type)
    self.container_id = attributes[u'container_id']
    self.container_name = attributes[u'container_name']
    self.action = attributes[u'action']


class DockerJSONLayerEvent(time_events.TimestampEvent):
  """Event parsed from a Docker filesystem layer configuration file

  Attributes:
    command: the command used which made Docker create a new layer
    layer_id: the identifier of the current Docker layer (sha1)
  """

  DATA_TYPE = u'docker:json:layer'

  def __init__(self, timestamp, event_type, attributes):
    super(DockerJSONLayerEvent, self).__init__(
        timestamp, event_type)
    self.command = attributes[u'command']
    self.layer_id = attributes[u'layer_id']


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

  NAME = u'dockerjson'
  DESCRIPTION = u'Parser for JSON Docker files.'

  def _GetIDFromPath(self, parser_mediator):
    """Extracts a container or a graph ID from a JSON file's path.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    file_entry = parser_mediator.GetFileEntry()
    path = file_entry.path_spec.location
    file_system = file_entry.GetFileSystem()
    _id = file_system.SplitPath(path)[-2]
    return _id

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
    json_dict = json.load(file_object)
    layer_id_from_path = self._GetIDFromPath(parser_mediator)
    event_attributes = {u'layer_id': layer_id_from_path}

    if u'docker_version' not in json_dict:
      raise errors.UnableToParseFile(
          u'not a valid Docker layer configuration file, missing '
          u'\'docker_version\' key.')

    if u'created' in json_dict:
      timestamp = timelib.Timestamp.FromTimeString(json_dict[u'created'])
      layer_creation_command_array = [
          x.strip() for x in json_dict[u'container_config'][u'Cmd']]
      layer_creation_command = u' '.join(layer_creation_command_array).replace(
          u'\t', '')

      event_attributes[u'command'] = layer_creation_command

      event = DockerJSONLayerEvent(
          timestamp, definitions.TIME_DESCRIPTION_ADDED, event_attributes)
      parser_mediator.ProduceEvent(event)

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
    json_dict = json.load(file_object)
    container_id_from_path = self._GetIDFromPath(parser_mediator)
    event_attributes = {u'container_id': container_id_from_path}

    if u'Driver' not in json_dict:
      raise errors.UnableToParseFile(
          u'not a valid Docker container configuration file, ' u'missing '
          u'\'Driver\' key.')

    container_id_from_json = json_dict.get(u'ID', None)
    if not container_id_from_json:
      raise errors.UnableToParseFile(
          u'not a valid Docker layer configuration file, the \'ID\' key is '
          u'missing from the JSON dict (should be {0:s})'.format(
              container_id_from_path))

    if container_id_from_json != container_id_from_path:
      raise errors.UnableToParseFile(
          u'not a valid Docker container configuration file. The \'ID\' key of '
          u'the JSON dict ({0:s}) is different from the layer ID taken from the'
          u' path to the file ({1:s}) JSON file.)'.format(
              container_id_from_json, container_id_from_path))

    if u'Config' in json_dict and u'Hostname' in json_dict[u'Config']:
      event_attributes[u'container_name'] = json_dict[u'Config'][u'Hostname']
    else:
      event_attributes[u'container_name'] = u'Unknown container name'

    if u'State' in json_dict:
      if u'StartedAt' in json_dict[u'State']:
        timestamp = timelib.Timestamp.FromTimeString(
            json_dict[u'State'][u'StartedAt'])
        event_attributes[u'action'] = u'Container Started'
        parser_mediator.ProduceEvent(DockerJSONContainerEvent(
            timestamp, definitions.TIME_DESCRIPTION_START, event_attributes))
      if u'FinishedAt' in json_dict['State']:
        if json_dict['State']['FinishedAt'] != u'0001-01-01T00:00:00Z':
          # If the timestamp is 0001-01-01T00:00:00Z, the container
          # is still running, so we don't generate a Finished event
          event_attributes['action'] = u'Container Finished'
          timestamp = timelib.Timestamp.FromTimeString(
              json_dict['State']['FinishedAt'])
          parser_mediator.ProduceEvent(DockerJSONContainerEvent(
              timestamp, definitions.TIME_DESCRIPTION_END, event_attributes))

    created_time = json_dict.get(u'Created', None)
    if created_time:
      timestamp = timelib.Timestamp.FromTimeString(created_time)
      event_attributes[u'action'] = u'Container Created'
      parser_mediator.ProduceEvent(
          DockerJSONContainerEvent(
              timestamp, definitions.TIME_DESCRIPTION_ADDED, event_attributes)
      )

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
    container_id = self._GetIDFromPath(parser_mediator)

    text_file_object = text_file.TextFile(file_object)
    for log_line in text_file_object:
      json_log_line = json.loads(log_line)

      time = json_log_line.get(u'time', None)
      if not time:
        continue

      event_data = DockerJSONContainerLogEventData()
      event_data.container_id = container_id
      event_data.log_line = json_log_line.get(u'log', None)
      event_data.log_source = json_log_line.get(u'stream', None)
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
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.UnableToParseFile(
          u'is not a valid JSON file, missing opening brace.')

    file_object.seek(0, os.SEEK_SET)

    file_entry = parser_mediator.GetFileEntry()

    file_system = file_entry.GetFileSystem()

    json_file_path = parser_mediator.GetDisplayName()
    split_path = file_system.SplitPath(json_file_path)
    try:
      if u'containers' in split_path:
        if u'config.json' in split_path:
          self._ParseContainerConfigJSON(parser_mediator, file_object)
        if json_file_path.endswith(u'-json.log'):
          self._ParseContainerLogJSON(parser_mediator, file_object)
      elif u'graph' in split_path:
        if u'json' in split_path:
          self._ParseLayerConfigJSON(parser_mediator, file_object)
    except ValueError as exception:
      if exception == u'No JSON object could be decoded':
        raise errors.UnableToParseFile(exception)
      else:
        raise


manager.ParsersManager.RegisterParser(DockerJSONParser)
