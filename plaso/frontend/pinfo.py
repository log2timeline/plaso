# -*- coding: utf-8 -*-
"""The pinfo front-end."""
# TODO: To make YAML loading work.

import logging
import pprint

from plaso.frontend import analysis_frontend
from plaso.frontend import frontend
from plaso.lib import timelib


class PinfoFrontend(analysis_frontend.AnalysisFrontend):
  """Class that implements the pinfo front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(PinfoFrontend, self).__init__(input_reader, output_writer)

    self._printer = pprint.PrettyPrinter(indent=8)
    self._verbose = False

  def _AddCollectionInformation(self, lines_of_text, collection_information):
    """Adds the lines of text that make up the collection information.

    Args:
      lines_of_text: A list containing the lines of text.
      collection_information: The collection information dict.
    """
    filename = collection_information.get('file_processed', 'N/A')
    time_of_run = collection_information.get('time_of_run', 0)
    time_of_run = timelib.Timestamp.CopyToIsoFormat(time_of_run)

    lines_of_text.append(u'Storage file:\t\t{0:s}'.format(
        self._storage_file_path))
    lines_of_text.append(u'Source processed:\t{0:s}'.format(filename))
    lines_of_text.append(u'Time of processing:\t{0:s}'.format(time_of_run))

    lines_of_text.append(u'')
    lines_of_text.append(u'Collection information:')

    for key, value in collection_information.items():
      if key not in ['file_processed', 'time_of_run']:
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

  def _AddStoreInformation(self, lines_of_text, store_information):
    """Adds the lines of text that make up the store information.

    Args:
      lines_of_text: A list containing the lines of text.
      store_information: The store information dict.
    """
    lines_of_text.append(u'')
    lines_of_text.append(u'Store information:')
    lines_of_text.append(u'\tNumber of available stores: {0:d}'.format(
        store_information['Number']))

    if not self._verbose:
      lines_of_text.append(
          u'\tStore information details omitted (to see use: --verbose)')
    else:
      for key, value in store_information.iteritems():
        if key not in ['Number']:
          lines_of_text.append(
              u'\t{0:s} =\n{1!s}'.format(key, self._printer.pformat(value)))

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
    lines_of_text = []

    collection_information = getattr(info, 'collection_information', None)
    if collection_information:
      self._AddHeader(lines_of_text)
      self._AddCollectionInformation(lines_of_text, collection_information)
    else:
      lines_of_text.append(u'Missing collection information.')

    counter_information = getattr(info, 'counter', None)
    if counter_information:
      self._AddCounterInformation(
          lines_of_text, u'Parser counter information', counter_information)

    counter_information = getattr(info, 'plugin_counter', None)
    if counter_information:
      self._AddCounterInformation(
          lines_of_text, u'Plugin counter information', counter_information)

    store_information = getattr(info, 'stores', None)
    if store_information:
      self._AddStoreInformation(lines_of_text, store_information)

    information = u'\n'.join(lines_of_text)

    if not self._verbose:
      preprocessing = (
          u'Preprocessing information omitted (to see use: --verbose).')
    else:
      preprocessing = u'Preprocessing information:\n'
      for key, value in info.__dict__.items():
        if key == 'collection_information':
          continue
        elif key == 'counter' or key == 'stores':
          continue
        if isinstance(value, list):
          preprocessing += u'\t{0:s} =\n{1!s}\n'.format(
              key, self._printer.pformat(value))
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

  def GetStorageInformation(self):
    """Returns a formatted storage information generator."""
    try:
      storage_file = self.OpenStorageFile()
    except IOError as exception:
      logging.error(
          u'Unable to open storage file: {0:s} with error: {1:s}'.format(
              self._storage_file_path, exception))
      return

    list_of_storage_information = storage_file.GetStorageInformation()
    if not list_of_storage_information:
      yield ''
      return

    last_entry = False

    for index, info in enumerate(list_of_storage_information):
      if index + 1 == len(list_of_storage_information):
        last_entry = True
      yield self._FormatStorageInformation(
          info, storage_file, last_entry=last_entry)

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options: the command line arguments (instance of argparse.Namespace).

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PinfoFrontend, self).ParseOptions(options)

    self._verbose = getattr(options, 'verbose', False)
