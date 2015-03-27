#!/usr/bin/python
# -*- coding: utf-8 -*-
"""A simple dump information gathered from a plaso storage container.

pinfo stands for Plaso INniheldurFleiriOrd or plaso contains more words.
"""

import argparse
import logging
import pprint
import sys

from plaso.cli import analysis_tool
from plaso.frontend import analysis_frontend
from plaso.lib import errors
from plaso.lib import timelib


# pylint: disable=logging-format-interpolation
class PinfoTool(analysis_tool.AnalysisTool):
  """Class that implements the pinfo CLI tool."""

  _INDENTATION_LEVEL = 8

  NAME = u'pinfo'
  USAGE = (
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
    self._verbose = False

  def _AddCollectionInformation(self, lines_of_text, collection_information):
    """Adds the lines of text that make up the collection information.

    Args:
      lines_of_text: A list containing the lines of text.
      collection_information: The collection information dict.
    """
    filename = collection_information.get(u'file_processed', u'N/A')
    time_of_run = collection_information.get(u'time_of_run', 0)
    time_of_run = timelib.Timestamp.CopyToIsoFormat(time_of_run)

    lines_of_text.append(u'Storage file:\t\t{0:s}'.format(
        self._storage_file_path))
    lines_of_text.append(u'Source processed:\t{0:s}'.format(filename))
    lines_of_text.append(u'Time of processing:\t{0:s}'.format(time_of_run))

    lines_of_text.append(u'')
    lines_of_text.append(u'Collection information:')

    for key, value in collection_information.items():
      if key not in [u'file_processed', u'time_of_run']:
        lines_of_text.append(u'\t{0:s} = {1!s}'.format(key, value))

  def _AddCounterInformation(
      self, lines_of_text, description, counter_information):
    """Adds the lines of text that make up the counter information.

    Args:
      lines_of_text: A list containing the lines of text.
      description: The counter information description.
      counter_information: The counter information dict.
    """
    lines_of_text.append(u'')
    lines_of_text.append(u'{0:s}:'.format(description))

    for key, value in counter_information.most_common():
      lines_of_text.append(u'\tCounter: {0:s} = {1:d}'.format(key, value))

  def _AddHeader(self, lines_of_text):
    """Adds the lines of text that make up the header.

    Args:
      lines_of_text: A list containing the lines of text.
    """
    lines_of_text.append(u'-' * self._LINE_LENGTH)
    lines_of_text.append(u'\t\tPlaso Storage Information')
    lines_of_text.append(u'-' * self._LINE_LENGTH)

  def _AddStoreInformation(
      self, printer_object, lines_of_text, store_information):
    """Adds the lines of text that make up the store information.

    Args:
      printer_object: A pretty printer object (instance of PrettyPrinter).
      lines_of_text: A list containing the lines of text.
      store_information: The store information dict.
    """
    lines_of_text.append(u'')
    lines_of_text.append(u'Store information:')
    lines_of_text.append(u'\tNumber of available stores: {0:d}'.format(
        store_information[u'Number']))

    if not self._verbose:
      lines_of_text.append(
          u'\tStore information details omitted (to see use: --verbose)')
    else:
      for key, value in store_information.iteritems():
        if key not in ['Number']:
          lines_of_text.append(
              u'\t{0:s} =\n{1!s}'.format(key, printer_object.pformat(value)))

  def _FormatStorageInformation(self, info, storage_file, last_entry=False):
    """Formats the storage information.

    Args:
      info: The storage information object (instance of PreprocessObject).
      storage_file: The storage file (instance of StorageFile).
      last_entry: Optional boolean value to indicate this is the last
                  information entry. The default is False.

    Returns:
      A string containing the formatted storage information.
    """
    printer_object = pprint.PrettyPrinter(indent=self._INDENTATION_LEVEL)
    lines_of_text = []

    collection_information = getattr(info, u'collection_information', None)
    if collection_information:
      self._AddHeader(lines_of_text)
      self._AddCollectionInformation(lines_of_text, collection_information)
    else:
      lines_of_text.append(u'Missing collection information.')

    counter_information = getattr(info, u'counter', None)
    if counter_information:
      self._AddCounterInformation(
          lines_of_text, u'Parser counter information', counter_information)

    counter_information = getattr(info, u'plugin_counter', None)
    if counter_information:
      self._AddCounterInformation(
          lines_of_text, u'Plugin counter information', counter_information)

    store_information = getattr(info, u'stores', None)
    if store_information:
      self._AddStoreInformation(
          printer_object, lines_of_text, store_information)

    information = u'\n'.join(lines_of_text)

    if not self._verbose:
      preprocessing = (
          u'Preprocessing information omitted (to see use: --verbose).')
    else:
      preprocessing = u'Preprocessing information:\n'
      for key, value in info.__dict__.items():
        if key == u'collection_information':
          continue
        elif key in [u'counter', u'stores']:
          continue
        if isinstance(value, list):
          preprocessing += u'\t{0:s} =\n{1!s}\n'.format(
              key, printer_object.pformat(value))
        else:
          preprocessing += u'\t{0:s} = {1!s}\n'.format(key, value)

    if not last_entry:
      reports = u''
    elif storage_file.HasReports():
      reports = u'Reporting information omitted (to see use: --verbose).'
    else:
      reports = u'No reports stored.'

    if self._verbose and last_entry and storage_file.HasReports():
      report_list = []
      for report in storage_file.GetReports():
        report_list.append(report.GetString())
      reports = u'\n'.join(report_list)

    return u'\n'.join([
        information, u'', preprocessing, u'', reports, u'-+' * 40])

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      A boolean value indicating the arguments were successfully parsed.
    """
    logging.basicConfig(
        level=logging.INFO, format=u'[%(levelname)s] %(message)s')

    argument_parser = argparse.ArgumentParser(description=self.USAGE)

    self.AddStorageFileOptions(argument_parser)

    argument_parser.add_argument(
        u'-v', u'--verbose', dest=u'verbose', action=u'store_true',
        default=False, help=u'Print verbose output.')

    options = argument_parser.parse_args()

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      logging.error(u'{0:s}'.format(exception))

      self._output_writer.Write(u'')
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

  def PrintStorageInformation(self):
    """Prints the storage information."""
    # TODO: clean up arguments after front-end refactor.
    front_end = analysis_frontend.AnalysisFrontend(None, None)

    try:
      storage = front_end.OpenStorage(self._storage_file_path)
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    list_of_storage_information = storage.GetStorageInformation()
    if not list_of_storage_information:
      self._output_writer.Write(u'No storage information found.')
      return

    last_entry = False

    for index, info in enumerate(list_of_storage_information):
      if index + 1 == len(list_of_storage_information):
        last_entry = True
      storage_information = self._FormatStorageInformation(
          info, storage, last_entry=last_entry)

      self._output_writer.Write(storage_information)


def Main():
  """Start the tool."""
  tool = PinfoTool()

  if not tool.ParseArguments():
    return False

  # TODO: left over comment: To make YAML loading work.

  tool.PrintStorageInformation()
  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
