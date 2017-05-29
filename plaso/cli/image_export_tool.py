# -*- coding: utf-8 -*-
"""The image export CLI tool."""

import argparse
import logging
import os
import textwrap

from plaso.cli import storage_media_tool
from plaso.frontend import image_export
from plaso.lib import errors


class ImageExportTool(storage_media_tool.StorageMediaTool):
  """Class that implements the image export CLI tool.

  Attributes:
    has_filters (bool): True if filters have been specified via the options.
    list_signature_identifiers (bool): True if information about the signature
        identifiers should be shown.
  """

  NAME = u'image_export'
  DESCRIPTION = (
      u'This is a simple collector designed to export files inside an '
      u'image, both within a regular RAW image as well as inside a VSS. '
      u'The tool uses a collection filter that uses the same syntax as a '
      u'targeted plaso filter.')

  EPILOG = u'And that is how you export files, plaso style.'

  _SOURCE_OPTION = u'image'

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(ImageExportTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._destination_path = None
    self._filter_file = None
    self._front_end = image_export.ImageExportFrontend()
    self._skip_duplicates = True
    self.has_filters = False
    self.list_signature_identifiers = False

  def ListSignatureIdentifiers(self):
    """Lists the signature identifier.

    Raises:
      BadConfigOption: if the data location is invalid.
    """
    if not self._data_location:
      raise errors.BadConfigOption(u'Missing data location.')

    path = os.path.join(self._data_location, u'signatures.conf')
    if not os.path.exists(path):
      raise errors.BadConfigOption(
          u'No such format specification file: {0:s}'.format(path))

    try:
      specification_store = self._front_end.ReadSpecificationFile(path)
    except IOError as exception:
      raise errors.BadConfigOption((
          u'Unable to read format specification file: {0:s} with error: '
          u'{1:s}').format(path, exception))

    identifiers = []
    for format_specification in specification_store.specifications:
      identifiers.append(format_specification.identifier)

    self._output_writer.Write(u'Available signature identifiers:\n')
    self._output_writer.Write(
        u'\n'.join(textwrap.wrap(u', '.join(sorted(identifiers)), 79)))
    self._output_writer.Write(u'\n\n')

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    self._ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddInformationalOptions(argument_parser)
    self.AddDataLocationOption(argument_parser)
    self.AddLogFileOptions(argument_parser)

    argument_parser.add_argument(
        u'-w', u'--write', action=u'store', dest=u'path', type=str,
        metavar=u'PATH', default=u'export', help=(
            u'The directory in which extracted files should be stored.'))

    self.AddFilterOptions(argument_parser)
    argument_parser.add_argument(
        u'--date-filter', u'--date_filter', action=u'append', type=str,
        dest=u'date_filters', metavar=u'TYPE_START_END', default=[], help=(
            u'Filter based on file entry date and time ranges. This parameter '
            u'is formatted as "TIME_VALUE,START_DATE_TIME,END_DATE_TIME" where '
            u'TIME_VALUE defines which file entry timestamp the filter applies '
            u'to e.g. atime, ctime, crtime, bkup, etc. START_DATE_TIME and '
            u'END_DATE_TIME define respectively the start and end of the date '
            u'time range. A date time range requires at minimum start or end '
            u'to time of the boundary and END defines the end time. Both '
            u'timestamps be set. The date time values are formatted as: '
            u'YYYY-MM-DD hh:mm:ss.######[+-]##:## Where # are numeric digits '
            u'ranging from 0 to 9 and the seconds fraction can be either 3 '
            u'or 6 digits. The time of day, seconds fraction and timezone '
            u'offset are optional. The default timezone is UTC. E.g. "atime, '
            u'2013-01-01 23:12:14, 2013-02-23". This parameter can be repeated '
            u'as needed to add additional date date boundaries, e.g. once for '
            u'atime, once for crtime, etc.'))

    argument_parser.add_argument(
        u'-x', u'--extensions', dest=u'extensions_string', action=u'store',
        type=str, metavar=u'EXTENSIONS', help=(
            u'Filter based on file name extensions. This option accepts '
            u'multiple multiple comma separated values e.g. "csv,docx,pst".'))

    argument_parser.add_argument(
        u'--names', dest=u'names_string', action=u'store',
        type=str, metavar=u'NAMES', help=(
            u'If the purpose is to find all files given a certain names '
            u'this options should be used. This option accepts a comma '
            u'separated string denoting all file names, e.g. -x '
            u'"NTUSER.DAT,UsrClass.dat".'))

    argument_parser.add_argument(
        u'--signatures', dest=u'signature_identifiers', action=u'store',
        type=str, metavar=u'IDENTIFIERS', help=(
            u'Filter based on file format signature identifiers. This option '
            u'accepts multiple comma separated values e.g. "esedb,lnk". '
            u'Use "list" to show an overview of the supported file format '
            u'signatures.'))

    argument_parser.add_argument(
        u'--include_duplicates', dest=u'include_duplicates',
        action=u'store_true', default=False, help=(
            u'If extraction from VSS is enabled, by default a digest hash '
            u'is calculated for each file. These hashes are compared to the '
            u'previously exported files and duplicates are skipped. Use '
            u'this option to include duplicate files in the export.'))

    self.AddStorageMediaImageOptions(argument_parser)
    self.AddVSSProcessingOptions(argument_parser)

    argument_parser.add_argument(
        self._SOURCE_OPTION, nargs='?', action=u'store', metavar=u'IMAGE',
        default=None, type=str, help=(
            u'The full path to the image file that we are about to extract '
            u'files from, it should be a raw image or another image that '
            u'plaso supports.'))

    try:
      options = argument_parser.parse_args()
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write(u'')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write(u'ERROR: {0:s}'.format(exception))
      self._output_writer.Write(u'')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    return True

  def ParseOptions(self, options):
    """Parses the options and initializes the front-end.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    # The data location is required to list signatures.
    self._ParseDataLocationOption(options)

    # Check the list options first otherwise required options will raise.
    signature_identifiers = self.ParseStringOption(
        options, u'signature_identifiers')
    if signature_identifiers == u'list':
      self.list_signature_identifiers = True

    if self.list_signature_identifiers:
      return

    super(ImageExportTool, self).ParseOptions(options)

    format_string = (
        u'%(asctime)s [%(levelname)s] (%(processName)-10s) PID:%(process)d '
        u'<%(module)s> %(message)s')

    if self._debug_mode:
      logging_level = logging.DEBUG
    elif self._quiet_mode:
      logging_level = logging.WARNING
    else:
      logging_level = logging.INFO

    self.ParseLogFileOptions(options)
    self._ConfigureLogging(
        filename=self._log_file, format_string=format_string,
        log_level=logging_level)

    self._destination_path = self.ParseStringOption(
        options, u'path', default_value=u'export')

    self._ParseFilterOptions(options)

    if (getattr(options, u'no_vss', False) or
        getattr(options, u'include_duplicates', False)):
      self._skip_duplicates = False

    date_filters = getattr(options, u'date_filters', None)
    try:
      self._front_end.ParseDateFilters(date_filters)
    except ValueError as exception:
      raise errors.BadConfigOption(exception)

    extensions_string = self.ParseStringOption(options, u'extensions_string')
    self._front_end.ParseExtensionsString(extensions_string)

    names_string = getattr(options, u'names_string', None)
    self._front_end.ParseNamesString(names_string)

    if not self._data_location:
      logging.warning(u'Unable to automatically determine data location.')

    signature_identifiers = getattr(options, u'signature_identifiers', None)
    try:
      self._front_end.ParseSignatureIdentifiers(
          self._data_location, signature_identifiers)
    except (IOError, ValueError) as exception:
      raise errors.BadConfigOption(exception)

    if self._filter_file:
      self.has_filters = True
    else:
      self.has_filters = self._front_end.HasFilters()

  def PrintFilterCollection(self):
    """Prints the filter collection."""
    self._front_end.PrintFilterCollection(self._output_writer)

  def ProcessSources(self):
    """Processes the sources.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
                          file system.
      UserAbort: if the user initiated an abort.
    """
    self.ScanSource()

    self._output_writer.Write(u'Export started.\n')

    self._front_end.ProcessSources(
        self._source_path_specs, self._destination_path, self._output_writer,
        filter_file=self._filter_file, skip_duplicates=self._skip_duplicates)

    self._output_writer.Write(u'Export completed.\n')
    self._output_writer.Write(u'\n')
