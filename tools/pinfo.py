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

from plaso.cli import analysis_tool
from plaso.frontend import analysis_frontend
from plaso.lib import errors
from plaso.lib import timelib


class PinfoTool(analysis_tool.AnalysisTool):
  """Class that implements the pinfo CLI tool."""

  _INDENTATION_LEVEL = 8

  NAME = u'pinfo'
  DESCRIPTION = (
      u'Gives you information about the storage file, how it was '
      u'collected, what information was gained from the image, etc.')

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

    # TODO: clean up arguments after front-end refactor.
    self._front_end = analysis_frontend.AnalysisFrontend(None, None)

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
      ignore_values: optional list of value indentifier to ignore. The default
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
          u'Storage file: {0:s} contains: {1:d} addititional storage '
          u'information entries.\n').format(
              self._storage_file_path,
              storage_information_list_length - number_of_list_entries))
      result = False

    if number_of_list_entries < compare_storage_information_list_length:
      self._output_writer.Write((
          u'Storage file: {0:s} contains: {1:d} addititional storage '
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

    self._FormatHeader(lines_of_text)

    filename = collection_information.get(u'file_processed', u'N/A')
    time_of_run = collection_information.get(u'time_of_run', 0)
    time_of_run = timelib.Timestamp.CopyToIsoFormat(time_of_run)

    lines_of_text.append(u'Storage file:\t\t{0:s}'.format(
        self._storage_file_path))
    lines_of_text.append(u'Source processed:\t{0:s}'.format(filename))
    lines_of_text.append(u'Time of processing:\t{0:s}'.format(time_of_run))

    lines_of_text.append(u'')
    lines_of_text.append(u'Collection information:')

    for key, value in collection_information.iteritems():
      if key in [u'file_processed', u'time_of_run']:
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

    for key, value in counter_information.most_common():
      lines_of_text.append(u'\tCounter: {0:s} = {1:d}'.format(key, value))

  def _FormatHeader(self, lines_of_text):
    """Formats a header.

    Args:
      lines_of_text: A list containing the lines of text.
    """
    lines_of_text.append(u'-' * self._LINE_LENGTH)
    lines_of_text.append(u'\t\tPlaso Storage Information')
    lines_of_text.append(u'-' * self._LINE_LENGTH)

  def _FormatPreprocessingInformation(
      self, printer_object, lines_of_text, storage_information):
    """Formats the processing information.

    Args:
      printer_object: A pretty printer object (instance of PrettyPrinter).
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
    for key, value in storage_information.__dict__.iteritems():
      if key in [u'collection_information', u'counter', u'stores']:
        continue

      if isinstance(value, list):
        value = printer_object.pformat(value)
        lines_of_text.append(u'\t{0:s} ='.format(key))
        lines_of_text.append(u'{0!s}'.format(value))
      else:
        lines_of_text.append(u'\t{0:s} = {1!s}'.format(key, value))

  def _FormatReports(self, storage_file):
    """Formats the reports.

    Args:
      storage_file: The storage file (instance of StorageFile).

    Returns:
      A string containing the formatted reports.
    """
    if not storage_file.HasReports():
      return u'No reports stored.'

    if not self._verbose:
      return u'Reporting information omitted (to see use: --verbose).'

    return u'\n'.join([
        report.GetString() for report in storage_file.GetReports()])

  def _FormatStorageInformation(
      self, storage_information, storage_file, last_entry=False):
    """Formats the storage information.

    Args:
      storage_information: The storage information object (instance of
                           PreprocessObject).
      storage_file: The storage file (instance of StorageFile).
      last_entry: Optional boolean value to indicate this is the last
                  information entry. The default is False.

    Returns:
      A string containing the formatted storage information.
    """
    printer_object = pprint.PrettyPrinter(indent=self._INDENTATION_LEVEL)
    lines_of_text = []

    self._FormatCollectionInformation(lines_of_text, storage_information)

    counter_information = getattr(storage_information, u'counter', None)
    self._FormatCounterInformation(
        lines_of_text, u'Parser counter information', counter_information)

    counter_information = getattr(storage_information, u'plugin_counter', None)
    self._FormatCounterInformation(
        lines_of_text, u'Plugin counter information', counter_information)

    self._FormatStoreInformation(
        printer_object, lines_of_text, storage_information)

    self._FormatPreprocessingInformation(
        printer_object, lines_of_text, storage_information)

    if last_entry:
      lines_of_text.append(u'')
      reports = self._FormatReports(storage_file)
    else:
      reports = u''

    information = u'\n'.join(lines_of_text)

    return u'\n'.join([information, reports, u'-+' * 40, u''])

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
      if key not in [u'Number']:
        lines_of_text.append(
            u'\t{0:s} =\n{1!s}'.format(key, printer_object.pformat(value)))

  def _PrintStorageInformation(self, storage_file):
    """Prints the storage information.

    Args:
      storage_file: The storage file (instance of StorageFile).
    """
    storage_information_list = storage_file.GetStorageInformation()

    if not storage_information_list:
      self._output_writer.Write(u'No storage information found.\n')
      return

    for index, storage_information in enumerate(storage_information_list):
      last_entry = index + 1 == len(storage_information_list)
      storage_information = self._FormatStorageInformation(
          storage_information, storage_file, last_entry=last_entry)

      self._output_writer.Write(storage_information)

  def CompareStorageInformation(self):
    """Compares the storage information.

    Returns:
      A boolean value indicating if the storage information objects are
      identical or not.
    """
    try:
      storage_file = self._front_end.OpenStorage(self._storage_file_path)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    try:
      compare_storage_file = self._front_end.OpenStorage(
          self._compare_storage_file_path)
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
    logging.basicConfig(
        level=logging.INFO, format=u'[%(levelname)s] %(message)s')

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False)

    self.AddBasicOptions(argument_parser)
    self.AddStorageFileOptions(argument_parser)

    argument_parser.add_argument(
        u'-v', u'--verbose', dest=u'verbose', action=u'store_true',
        default=False, help=u'Print verbose output.')

    argument_parser.add_argument(
        u'--compare', dest=u'compare_storage_file', type=unicode,
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
      self._output_writer.Write(argument_parser.format_help())

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

    self._verbose = getattr(options, u'verbose', False)

    compare_storage_file_path = getattr(options, u'compare_storage_file', None)
    if compare_storage_file_path:
      if not os.path.isfile(compare_storage_file_path):
        raise errors.BadConfigOption(
            u'No such storage file: {0:s}.'.format(compare_storage_file_path))

      self._compare_storage_file_path = compare_storage_file_path
      self.compare_storage_information = True

  def PrintStorageInformation(self):
    """Prints the storage information."""
    try:
      storage_file = self._front_end.OpenStorage(self._storage_file_path)
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
