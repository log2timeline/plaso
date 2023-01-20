# -*- coding: utf-8 -*-
"""The Apple Unified Logging (AUL) Timesync file parser."""
import os

from dfvfs.helpers import file_system_searcher
from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import dtfabric_helper
from plaso.lib import errors

from plaso.parsers import interface


class TimesyncParser(
  interface.FileObjectParser, dtfabric_helper.DtFabricHelper):
  """Timesync record file parser

  Attributes:
    records (List[timesync_boot_record]): List of Timesync records.
  """
  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'timesync.yaml')

  def __init__(self):
    """Initialises the parser."""
    super(TimesyncParser, self).__init__()
    self.records = []

  def ParseAll(self, parser_mediator, file_entry, file_system):
    """Finds and parses all the timesync files

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_system (dfvfs.FileSystem): file system.
      file_entry (dfvfs.FileEntry): file entry.
    """
    path_segments = file_system.SplitPath(file_entry.path_spec.location)
    timesync_location = file_system.JoinPath(path_segments[:-2] + ['timesync'])
    kwargs = {}
    if file_entry.path_spec.parent:
      kwargs['parent'] = file_entry.path_spec.parent
    kwargs['location'] = timesync_location
    timesync_file_path_spec = path_spec_factory.Factory.NewPathSpec(
        file_entry.path_spec.TYPE_INDICATOR, **kwargs)

    find_spec = file_system_searcher.FindSpec(
        file_entry_types=[definitions.FILE_ENTRY_TYPE_FILE])

    path_spec_generator = file_system_searcher.FileSystemSearcher(
        file_system, timesync_file_path_spec).Find(
          find_specs=[find_spec])

    for path_spec in path_spec_generator:
      try:
        timesync_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
            path_spec)

      except RuntimeError as exception:
        message = (
            'Unable to open timesync file: {0:s} with error: '
            '{1!s}'.format(path_spec, exception))
        parser_mediator.ProduceExtractionWarning(message)
        continue
      try:
        timesync_file_object = timesync_file_entry.GetFileObject()
        self.ParseFileObject(parser_mediator, timesync_file_object)
      except (IOError, errors.ParseError) as exception:
        message = (
            'Unable to parse data block file: {0:s} with error: '
            '{1!s}').format(path_spec, exception)
        parser_mediator.ProduceExtractionWarning(message)
        continue

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a shared-cache strings (dsc) file-like object.

    Args:
      parser_mediator (ParserMediator): a parser mediator.
      file_object (dfvfs.FileIO): a file-like object to parse.

    Raises:
      ParseError: if the records cannot be parsed.
    """
    boot_record_data_map = self._GetDataTypeMap('timesync_boot_record')
    sync_record_data_map = self._GetDataTypeMap('timesync_sync_record')

    file_size = file_object.get_size()
    offset = 0
    current_boot_record = None
    while offset < file_size:
      try:
        boot_record, size = self._ReadStructureFromFileObject(
            file_object, offset, boot_record_data_map)
        offset += size
        if current_boot_record is not None:
          self.records.append(current_boot_record)
        current_boot_record = boot_record
        current_boot_record.sync_records = []
        continue
      except errors.ParseError:
        pass

      try:
        sync_record, size = self._ReadStructureFromFileObject(
            file_object, offset, sync_record_data_map)
        offset += size
        current_boot_record.sync_records.append(sync_record)
      except errors.ParseError as exception:
        raise errors.ParseError(
            'Unable to parse time sync file with error: {0!s}'.format(
                exception))
    self.records.append(current_boot_record)
