#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A simple dump information gathered from a plaso storage container.

pinfo stands for Plaso INniheldurFleiriOrd or plaso contains more words.
"""

import argparse
import logging
import os
import pprint
import sys
import uuid

from plaso.cli import analysis_tool
from plaso.cli import views as cli_views
from plaso.frontend import analysis_frontend
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import timelib
from plaso.storage import zip_file as storage_zip_file


class PinfoTool(analysis_tool.AnalysisTool):
  """Class that implements the pinfo CLI tool."""

  NAME = u'pinfo'
  DESCRIPTION = (
      u'Gives you information about the storage file, how it was '
      u'collected, what information was gained from the image, etc.')

  _INDENTATION_LEVEL = 8

  _PREPROCESSING_VALUE_DESCRIPTIONS = {
      u'code_page': u'Code page',
      u'guessed_os': u'Operating system',
      u'hostname': u'Hostname',
      u'name': u'Name',
      u'osversion': u'Operating system',
      u'path': u'Profile path',
      u'plugin_counter': u'Number of plugins',
      u'programfiles': u'%ProgramFiles%',
      u'sid': u'SID',
      u'systemroot': u'%SystemRoot%',
      u'sysregistry': u'Registry path',
      u'users': u'Users information',
      u'time_zone_str': u'Time zone',
      u'windir': u'%WinDir%',
      u'zone': u'Time zone',
  }

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader: the input reader (instance of InputReader).
                    The default is None which indicates the use of the stdin
                    input reader.
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
    """
    super(PinfoTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._compare_storage_file_path = None

    self._front_end = analysis_frontend.AnalysisFrontend()

    self._verbose = False
    self.compare_storage_information = False

  def _CompareInformationDict(
      self, identifier, storage_information, compare_storage_information,
      ignore_values=None):
    """Compares the information dictionaries.

    Args:
      identifier: The identifier of the dictionary to compare.
      storage_information: The storage information object (instance of
                            PreprocessObject).
      compare_storage_information: The storage information object (instance of
                                   PreprocessObject) to compare against.
      ignore_values: optional list of value identifier to ignore. The default
                     is None.

    Returns:
      A boolean value indicating if the information dictionaries are identical
      or not.
    """
    information = getattr(storage_information, identifier, None)
    compare_information = getattr(compare_storage_information, identifier, None)

    if not information and not compare_information:
      return True

    # Determine the union of the keys.
    if not information:
      keys = set(compare_information.keys())
    elif not compare_information:
      keys = set(information.keys())
    else:
      keys = set(information.keys()) | set(compare_information.keys())

    result = True
    for key in keys:
      if ignore_values and key in ignore_values:
        continue

      description = u'{0:s}.{1:s}'.format(identifier, key)
      if not self._CompareInformationValue(
          key, description, information, compare_information):
        result = False

    return result

  def _CompareInformationValue(
      self, identifier, description, information, compare_information):
    """Compares the information values.

    Args:
      identifier: The identifier of the value to compare.
      description: Human readable description of the value.
      information: The information dictionary.
      compare_information: The information dictionary to compare against.

    Returns:
      A boolean value indicating if the information values are identical or not.
    """
    has_value = information.has_key(identifier)
    compare_has_value = compare_information.has_key(identifier)

    if not has_value and not compare_has_value:
      return True

    if not has_value:
      self._output_writer.Write(u'{0:s} value not present in {1:s}.\n'.format(
          description, self._storage_file_path))
      return False

    if not compare_has_value:
      self._output_writer.Write(u'{0:s} value not present in {1:s}.\n'.format(
          description, self._compare_storage_file_path))
      return False

    value = information.get(identifier, None)
    compare_value = compare_information.get(identifier, None)
    if value != compare_value:
      self._output_writer.Write(
          u'{0:s} value mismatch {1!s} != {2!s}.\n'.format(
              description, value, compare_value))
      return False

    return True

  def _CompareStorageInformationObjects(
      self, storage_information, compare_storage_information):
    """Compares the storage information objects.

    Args:
      storage_information: The storage information object (instance of
                            PreprocessObject).
      compare_storage_information: The storage information object (instance of
                                   PreprocessObject) to compare against.

    Returns:
      A boolean value indicating if the storage information objects are
      identical or not.
    """
    result = True
    if not self._CompareInformationDict(
        u'collection_information', storage_information,
        compare_storage_information, ignore_values=[
            u'cmd_line', u'output_file', u'time_of_run']):
      result = False

    if not self._CompareInformationDict(
        u'counter', storage_information, compare_storage_information):
      result = False

    if not self._CompareInformationDict(
        u'plugin_counter', storage_information, compare_storage_information):
      result = False

    # TODO: compare stores.
    # TODO: compare remaining preprocess information.
    # TODO: compare reports.

    return result

  def _CompareStorageInformation(self, storage_file, compare_storage_file):
    """Compares the storage information.

    Args:
      storage_file: The storage file (instance of StorageFile).
      compare_storage_file: The storage file (instance of StorageFile) to
                            compare against.

    Returns:
      A boolean value indicating if the storage information objects are
      identical or not.
    """
    storage_information_list = storage_file.GetStorageInformation()
    compare_storage_information_list = (
        compare_storage_file.GetStorageInformation())

    if not storage_information_list and not compare_storage_information_list:
      self._output_writer.Write(u'No storage information found.\n')
      return True

    storage_information_list_length = len(storage_information_list)
    compare_storage_information_list_length = len(
        compare_storage_information_list)
    number_of_list_entries = min(
        storage_information_list_length,
        compare_storage_information_list_length)

    result = True
    for list_entry in range(0, number_of_list_entries):
      if not self._CompareStorageInformationObjects(
          storage_information_list[list_entry],
          compare_storage_information_list[list_entry]):
        result = False

    if number_of_list_entries < storage_information_list_length:
      self._output_writer.Write((
          u'Storage file: {0:s} contains: {1:d} additional storage '
          u'information entries.\n').format(
              self._storage_file_path,
              storage_information_list_length - number_of_list_entries))
      result = False

    if number_of_list_entries < compare_storage_information_list_length:
      self._output_writer.Write((
          u'Storage file: {0:s} contains: {1:d} additional storage '
          u'information entries.\n').format(
              self._compare_storage_file_path,
              compare_storage_information_list_length - number_of_list_entries))
      result = False

    if result:
      self._output_writer.Write(u'Storage files are identical.\n')

    return result

  def _FormatCollectionInformation(self, lines_of_text, storage_information):
    """Formats the collection information.

    Args:
      lines_of_text: A list containing the lines of text.
      storage_information: The storage information object (instance of
                            PreprocessObject).
    """
    collection_information = getattr(
        storage_information, u'collection_information', None)
    if not collection_information:
      lines_of_text.append(u'Missing collection information.')
      return

    filename = collection_information.get(u'file_processed', u'N/A')
    time_of_run = collection_information.get(u'time_of_run', 0)
    time_of_run = timelib.Timestamp.CopyToIsoFormat(time_of_run)

    lines_of_text.append(u'Source processed:\t{0:s}'.format(filename))
    lines_of_text.append(u'Time of processing:\t{0:s}'.format(time_of_run))

    lines_of_text.append(u'')
    lines_of_text.append(u'Collection information:')

    for key, value in collection_information.iteritems():
      if key in (u'file_processed', u'time_of_run'):
        continue
      if key == u'parsers':
        value = u', '.join(sorted(value))
      lines_of_text.append(u'\t{0:s} = {1!s}'.format(key, value))

  def _FormatCounterInformation(
      self, lines_of_text, description, counter_information):
    """Formats the counter information.

    Args:
      lines_of_text: A list containing the lines of text.
      description: The counter information description.
      counter_information: The counter information dict.
    """
    if not counter_information:
      return

    if lines_of_text:
      lines_of_text.append(u'')

    lines_of_text.append(u'{0:s}:'.format(description))

    total_value = None
    for key, value in sorted(counter_information.most_common()):
      if key == u'total':
        total_value = value
      else:
        lines_of_text.append(u'\t{0:s} = {1:d}'.format(key, value))

    if total_value is not None:
      lines_of_text.append(u'\tTotal = {0:d}'.format(total_value))

  def _FormatPreprocessingInformationValue(self, key, value):
    """Formats a processing information value.

    Args:
      key: The key of the value.
      value: The value.

    Returns:
      A line of text containing the formatted processing information value.
    """
    description = self._PREPROCESSING_VALUE_DESCRIPTIONS.get(key, key)
    # Make sure we have the same tab alignment for all the values.
    if len(description) < 7:
      text = u'\t{0:s}\t\t\t: {1!s}'.format(description, value)
    elif len(description) < 15:
      text = u'\t{0:s}\t\t: {1!s}'.format(description, value)
    else:
      text = u'\t{0:s}\t: {1!s}'.format(description, value)

    return text

  def _FormatPreprocessingInformation(self, lines_of_text, storage_information):
    """Formats the processing information.

    Args:
      lines_of_text: A list containing the lines of text.
      storage_information: The storage information object (instance of
                           PreprocessObject).
    """
    if lines_of_text:
      lines_of_text.append(u'')

    if not self._verbose:
      lines_of_text.append(
          u'Preprocessing information omitted (to see use: --verbose).')
      return

    lines_of_text.append(u'Preprocessing information:')

    for key in (u'osversion', u'hostname', u'time_zone_str', u'codepage'):
      value = getattr(storage_information, key, None)
      if value:
        text = self._FormatPreprocessingInformationValue(key, value)
        lines_of_text.append(text)

    for key in (u'programfiles', u'systemroot', u'windir'):
      value = getattr(storage_information, key, None)
      if value:
        text = self._FormatPreprocessingInformationValue(key, value)
        lines_of_text.append(text)

    key = u'users'
    users_list = getattr(storage_information, key, [])
    if users_list:
      description = self._PREPROCESSING_VALUE_DESCRIPTIONS.get(key, key)
      lines_of_text.append(u'    {0:s}:'.format(description))
      for user_dict in users_list:
        for key in (u'name', u'sid', u'path'):
          value = user_dict.get(key, None)
          if value:
            text = self._FormatPreprocessingInformationValue(key, value)
            lines_of_text.append(text)

    # TODO: clean this up after restructuring the preprocessing information.
    lines_of_text.append(u'    Other:')
    for key, value in storage_information.__dict__.iteritems():
      if key in frozenset([
          u'_user_ids_to_names', u'codepage', u'collection_information',
          u'counter', u'hostname', u'osversion', u'plugin_counter',
          u'programfiles', u'stores', u'systemroot', u'time_zone_str',
          u'users', u'windir']):
        continue

      if value:
        text = self._FormatPreprocessingInformationValue(key, value)
        lines_of_text.append(text)

  def _FormatReports(self, storage_file):
    """Formats the reports.

    Args:
      storage_file: The storage file (instance of StorageFile).

    Returns:
      A string containing the formatted reports.
    """
    if not storage_file.HasAnalysisReports():
      return u'No analysis reports stored.'

    if not self._verbose:
      return u'Reporting information omitted (to see use: --verbose).'

    report_strings = [
        report.GetString() for report in storage_file.GetAnalysisReports()]
    return u'\n'.join(report_strings)

  def _FormatStorageInformation(
      self, lines_of_text, storage_information, storage_file, last_entry=False):
    """Formats the storage information.

    Args:
      lines_of_text: A list containing the lines of text.
      storage_information: The storage information object (instance of
                           PreprocessObject).
      storage_file: The storage file (instance of StorageFile).
      last_entry: Optional boolean value to indicate this is the last
                  information entry.
    """
    self._FormatCollectionInformation(lines_of_text, storage_information)

    counter_information = getattr(storage_information, u'counter', None)
    self._FormatCounterInformation(
        lines_of_text, u'Parser counter information', counter_information)

    counter_information = getattr(storage_information, u'plugin_counter', None)
    self._FormatCounterInformation(
        lines_of_text, u'Plugin counter information', counter_information)

    printer_object = pprint.PrettyPrinter(indent=self._INDENTATION_LEVEL)
    self._FormatStoreInformation(
        printer_object, lines_of_text, storage_information)

    self._FormatPreprocessingInformation(lines_of_text, storage_information)

    lines_of_text.append(u'')
    if last_entry:
      reports = self._FormatReports(storage_file)
      lines_of_text.append(reports)

    lines_of_text.append(u'-+' * 40)
    lines_of_text.append(u'')

  def _FormatStoreInformation(
      self, printer_object, lines_of_text, storage_information):
    """Formats the store information.

    Args:
      printer_object: A pretty printer object (instance of PrettyPrinter).
      lines_of_text: A list containing the lines of text.
      storage_information: The storage information object (instance of
                           PreprocessObject).
    """
    store_information = getattr(storage_information, u'stores', None)
    if not store_information:
      return

    if lines_of_text:
      lines_of_text.append(u'')

    lines_of_text.append(u'Store information:')
    lines_of_text.append(u'\tNumber of available stores: {0:d}'.format(
        store_information[u'Number']))

    if not self._verbose:
      lines_of_text.append(
          u'\tStore information details omitted (to see use: --verbose)')
      return

    for key, value in store_information.iteritems():
      if key != u'Number':
        lines_of_text.append(
            u'\t{0:s} =\n{1!s}'.format(key, printer_object.pformat(value)))

  def _PrintSessionsDetails(self, storage):
    """Prints the details of the sessions.

    Args:
      storage (BaseStorage): storage.
    """
    for session_start, session_completion in storage.GetSessions():
      session_identifier = uuid.UUID(hex=session_start.identifier)
      title = u'Session: {0!s}'.format(session_identifier)
      table_view = cli_views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      start_time = timelib.Timestamp.CopyToIsoFormat(
          session_start.timestamp)
      table_view.AddRow([u'Start time', start_time])

      completion_time = timelib.Timestamp.CopyToIsoFormat(
          session_completion.timestamp)
      table_view.AddRow([u'Completion time', completion_time])

      table_view.AddRow([u'Product name', session_start.product_name])
      table_view.AddRow([u'Product version', session_start.product_version])
      table_view.AddRow([
          u'Command line arguments', session_start.command_line_arguments])
      table_view.AddRow([
          u'Parser filter expression', session_start.parser_filter_expression])
      table_view.AddRow([
          u'Preferred encoding', session_start.preferred_encoding])
      table_view.AddRow([u'Debug mode', session_start.debug_mode])
      table_view.AddRow([u'Filter file', session_start.filter_file])
      table_view.AddRow([u'Filter expression', session_start.filter_expression])

      table_view.Write(self._output_writer)

  def _PrintSessionsOverview(self, storage):
    """Prints a sessions overview.

    Args:
      storage (BaseStorage): storage.
    """
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Sessions')

    for session_start, _ in storage.GetSessions():
      start_time = timelib.Timestamp.CopyToIsoFormat(
          session_start.timestamp)
      session_identifier = uuid.UUID(hex=session_start.identifier)
      table_view.AddRow([str(session_identifier), start_time])

    table_view.Write(self._output_writer)

  def _PrintStorageInformation(self, storage):
    """Prints information about the storage.

    Args:
      storage (BaseStorage): storage.
    """
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Plaso Storage Information')
    table_view.AddRow([u'Path', self._storage_file_path])
    table_view.AddRow([u'Format version', storage.format_version])
    table_view.AddRow([u'Serialization format', storage.serialization_format])
    table_view.Write(self._output_writer)

    if storage.storage_type == definitions.STORAGE_TYPE_SESSION:
      self._PrintSessionsOverview(storage)
      self._PrintSessionsDetails(storage)

    elif storage.storage_type == definitions.STORAGE_TYPE_TASK:
      self._PrintTasksInformation(storage)

    return

  def _PrintTasksInformation(self, storage):
    """Prints information about the tasks.

    Args:
      storage (BaseStorage): storage.
    """
    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Tasks')

    for task_start, _ in storage.GetSessions():
      start_time = timelib.Timestamp.CopyToIsoFormat(
          task_start.timestamp)
      task_identifier = uuid.UUID(hex=task_start.identifier)
      table_view.AddRow([str(task_identifier), start_time])

    table_view.Write(self._output_writer)

  def CompareStorageInformation(self):
    """Compares the storage information.

    Returns:
      A boolean value indicating if the storage information objects are
      identical or not.
    """
    try:
      storage_file = storage_zip_file.StorageFile(
          self._storage_file_path, read_only=True)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    try:
      compare_storage_file = storage_zip_file.StorageFile(
          self._compare_storage_file_path, read_only=True)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._compare_storage_file_path, exception))
      storage_file.Close()
      return

    result = self._CompareStorageInformation(storage_file, compare_storage_file)

    storage_file.Close()
    compare_storage_file.Close()

    return result

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      A boolean value indicating the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddStorageFileOptions(argument_parser)

    argument_parser.add_argument(
        u'-v', u'--verbose', dest=u'verbose', action=u'store_true',
        default=False, help=u'Print verbose output.')

    argument_parser.add_argument(
        u'--compare', dest=u'compare_storage_file', type=str,
        action=u'store', default=u'', metavar=u'STORAGE_FILE', help=(
            u'The path of the storage file to compare against.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_usage())

      return False

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PinfoTool, self).ParseOptions(options)

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    self._ConfigureLogging(log_level=logging_level)

    self._verbose = getattr(options, u'verbose', False)

    compare_storage_file_path = self.ParseStringOption(
        options, u'compare_storage_file')
    if compare_storage_file_path:
      if not os.path.isfile(compare_storage_file_path):
        raise errors.BadConfigOption(
            u'No such storage file: {0:s}.'.format(compare_storage_file_path))

      self._compare_storage_file_path = compare_storage_file_path
      self.compare_storage_information = True

  def PrintStorageInformation(self):
    """Prints the storage information."""
    try:
      storage_file = storage_zip_file.StorageFile(
          self._storage_file_path, read_only=True)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    self._PrintStorageInformation(storage_file)

    storage_file.Close()


def Main():
  """The main function."""
  tool = PinfoTool()

  if not tool.ParseArguments():
    return False

  result = True
  if tool.compare_storage_information:
    result = tool.CompareStorageInformation()
  else:
    tool.PrintStorageInformation()
  return result


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
