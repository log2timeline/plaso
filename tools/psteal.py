#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Psteal (Plaso SýndarheimsTímalína sem Er ALgjörlega sjálfvirk).

Psteal Combines the log2timeline and psort tools into a single tool.
Currently doesn't support any of the two tools flags.

Sample Usage:
  psteal.py --source=/tmp/mystorage.dump --write=/tmp/mystorage_timeline.csv

See additional details here:
  https://github.com/log2timeline/plaso/wiki/Using-psteal
"""

import argparse
import collections
import multiprocessing
import logging
import os
import sys
import textwrap

from dfvfs.lib import definitions as dfvfs_definitions

# The following import makes sure the filters are registered.
from plaso.cli import extract_analyze_tool
from plaso.cli import tools as cli_tools
from plaso.cli import views as cli_views
from plaso.cli.helpers import manager as helpers_manager
from plaso.frontend import log2timeline
from plaso.frontend import psort
from plaso.engine import configurations
from plaso.output import interface as output_interface
from plaso.lib import errors


class PstealTool(extract_analyze_tool.ExtractionAndAnalysisTool):
  """Implements the psteal CLI tool.

  Psteal extract events from the provided source and stores them in an
  intermediate storage file. After extraction an output log file is created.
  This mimics the behaviour of the log2timeline.pl.
  The tool currently doesn't support any of the log2timeline or psort tools'
  flags.

  Attributes:
    dependencies_check (bool): True if the availability and versions of
        dependencies should be checked.
    list_output_modules (bool): True if information about the output modules
        should be shown.
  """

  NAME = u'psteal'

  DESCRIPTION = textwrap.dedent(u'\n'.join([
      u'',
      (u'psteal is a command line tool to extract events from individual '),
      u'files, recursing a directory (e.g. mount point) or storage media ',
      u'image or device. The output events will be stored in a storage file.',
      u'This tool will then read the output and process the events into a CSV ',
      u'file.',
      u'',
      u'More information can be gathered from here:',
      u'    https://github.com/log2timeline/plaso/wiki/Using-log2timeline',
      u'']))

  EPILOG = textwrap.dedent(u'\n'.join([
      u'',
      u'Example usage:',
      u'',
      u'Run the tool against a storage media image (full kitchen sink)',
      u'    psteal.py --source ímynd.dd -w imynd.timeline.txt',
      u'',
      u'And that is how you build a timeline using psteal...',
      u'']))

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(PstealTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._analysis_front_end = psort.PsortFrontend()
    self._command_line_arguments = None
    self._deduplicate_events = True
    self._enable_sigsegv_handler = False
    self._extraction_front_end = log2timeline.Log2TimelineFrontend()
    self._force_preprocessing = False
    self._hasher_names_string = None
    self._number_of_extraction_workers = 0
    self._options = None
    self._output_format = u'dynamic'
    self._output_filename = None
    self._output_module = None
    self._parser_filter_expression = None
    self._preferred_year = None
    self._single_process_mode = False
    self._source_type = None
    self._status_view_mode = u'window'
    self._time_slice = None
    self._use_time_slicer = False
    self._yara_rules_string = None

  def _DetermineSourceType(self):
    """Determines the source type."""
    scan_context = self.ScanSource()
    self._source_type = scan_context.source_type

    if self._source_type == dfvfs_definitions.SOURCE_TYPE_DIRECTORY:
      self._source_type_string = u'directory'

    elif self._source_type == dfvfs_definitions.SOURCE_TYPE_FILE:
      self._source_type_string = u'single file'

    elif self._source_type == (
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_DEVICE):
      self._source_type_string = u'storage media device'

    elif self._source_type == (
        dfvfs_definitions.SOURCE_TYPE_STORAGE_MEDIA_IMAGE):
      self._source_type_string = u'storage media image'

    else:
      self._source_type_string = u'UNKNOWN'

  def _GetStatusUpdateCallback(self):
    """Retrieves the status update callback function.

    Returns:
      function: status update callback function or None.
    """
    if self._status_view_mode == u'linear':
      return self._PrintStatusUpdateStream
    elif self._status_view_mode == u'window':
      return self._PrintStatusUpdate

  def ExtractEventsFromSources(self):
    """Processes the sources and extract events.

    This is a stripped down copy of tools/log2timeline.py that doesn't support
    the full set of flags. The defaults for these are hard coded in the
    constructor of this class.

    Raises:
      SourceScannerError: if the source scanner could not find a supported
          file system.
      UserAbort: if the user initiated an abort.
    """
    self._DetermineSourceType()

    self._output_writer.Write(u'\n')
    self._PrintStatusHeader()

    self._output_writer.Write(u'Processing started.\n')

    status_update_callback = self._GetStatusUpdateCallback()

    session = self._extraction_front_end.CreateSession(
        command_line_arguments=self._command_line_arguments,
        filter_file=self._filter_file,
        preferred_encoding=self.preferred_encoding,
        preferred_time_zone=self._preferred_time_zone,
        preferred_year=self._preferred_year)

    storage_writer = self._extraction_front_end.CreateStorageWriter(
        session, self._storage_file_path)
    # TODO: handle errors.BadConfigOption

    # TODO: pass preferred_encoding.
    configuration = configurations.ProcessingConfiguration()
    configuration.credentials = self._credential_configurations
    configuration.debug_output = self._debug_mode
    configuration.extraction.hasher_names_string = self._hasher_names_string
    configuration.extraction.yara_rules_string = self._yara_rules_string
    configuration.filter_file = self._filter_file
    configuration.parser_filter_expression = self._parser_filter_expression
    configuration.preferred_year = self._preferred_year

    processing_status = self._extraction_front_end.ProcessSources(
        session, storage_writer, self._source_path_specs, self._source_type,
        configuration, enable_sigsegv_handler=self._enable_sigsegv_handler,
        force_preprocessing=self._force_preprocessing,
        number_of_extraction_workers=self._number_of_extraction_workers,
        single_process_mode=self._single_process_mode,
        status_update_callback=status_update_callback)

    if not processing_status:
      self._output_writer.Write(
          u'WARNING: missing processing status information.\n')

    elif not processing_status.aborted:
      if processing_status.error_path_specs:
        self._output_writer.Write(u'Processing completed with errors.\n')
      else:
        self._output_writer.Write(u'Processing completed.\n')

      number_of_errors = (
          processing_status.foreman_status.number_of_produced_errors)
      if number_of_errors:
        output_text = u'\n'.join([
            u'',
            (u'Number of errors encountered while extracting events: '
             u'{0:d}.').format(number_of_errors),
            u'',
            u'Use pinfo to inspect errors in more detail.',
            u''])
        self._output_writer.Write(output_text)

      if processing_status.error_path_specs:
        output_text = u'\n'.join([
            u'',
            u'Path specifications that could not be processed:',
            u''])
        self._output_writer.Write(output_text)
        for path_spec in processing_status.error_path_specs:
          self._output_writer.Write(path_spec.comparable)
          self._output_writer.Write(u'\n')

    self._output_writer.Write(u'\n')

  def _CreateOutputModule(self):
    """Creates a default output module

    Raises:
      BadConfigOption: when the output_filename already exists or hasn't been
          set.
    """
    self._output_module = self._analysis_front_end.CreateOutputModule(
        self._output_format, preferred_encoding=self.preferred_encoding,
        timezone=self._preferred_time_zone)

    if isinstance(self._output_module, output_interface.LinearOutputModule):
      if not self._output_filename:
        raise errors.BadConfigOption(
            u'Output format: {0:s} requires an output file.'.format(
                self._output_format))

      if self._output_filename and os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            u'Output file already exists: {0:s}. Aborting.'.format(
                self._output_filename))

      output_file_object = open(self._output_filename, u'wb')
      output_writer = cli_tools.FileObjectOutputWriter(output_file_object)

      self._output_module.SetOutputWriter(output_writer)

  def AnalyzeEvents(self):
    """Analyzes events from a plaso storage file and generate a report.

    Raises:
      BadConfigOption: when a configuration parameter fails validation.
      RuntimeError: if a non-recoverable situation is encountered.
    """
    helpers_manager.ArgumentHelperManager.ParseOptions(
        self._options, self._output_module)

    # No analysis plugin

    session = self._analysis_front_end.CreateSession(
        command_line_arguments=self._command_line_arguments,
        preferred_encoding=self.preferred_encoding)

    storage_reader = self._analysis_front_end.CreateStorageReader(
        self._storage_file_path)
    self._number_of_analysis_reports = (
        storage_reader.GetNumberOfAnalysisReports())
    storage_reader.Close()

    configuration = configurations.ProcessingConfiguration()

    counter = collections.Counter()
    if self._output_format != u'null':
      storage_reader = self._analysis_front_end.CreateStorageReader(
          self._storage_file_path)

      events_counter = self._analysis_front_end.ExportEvents(
          storage_reader, self._output_module, configuration,
          deduplicate_events=self._deduplicate_events,
          time_slice=self._time_slice, use_time_slicer=self._use_time_slicer)

      counter += events_counter

    for item, value in iter(session.analysis_reports_counter.items()):
      counter[item] = value

    if self._quiet_mode:
      return

    self._output_writer.Write(u'Processing completed.\n')

    table_view = cli_views.ViewsFactory.GetTableView(
        self._views_format_type, title=u'Counter')
    for element, count in counter.most_common():
      if not element:
        element = u'N/A'
      table_view.AddRow([element, count])
    table_view.Write(self._output_writer)

    storage_reader = self._analysis_front_end.CreateStorageReader(
        self._storage_file_path)
    self._PrintAnalysisReportsDetails(storage_reader)

    self._output_writer.Write(u'Storage file is {0:s}\n'.format(
        self._storage_file_path))

  def ParseArguments(self):
    """Parses the command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, epilog=self.EPILOG, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddStorageFileOptions(argument_parser)

    extraction_group = argument_parser.add_argument_group(
        u'Extraction Arguments')

    self.AddCredentialOptions(extraction_group)

    input_group = argument_parser.add_argument_group(u'Input Arguments')
    input_group.add_argument(
        u'--source', dest=u'source', action=u'store',
        type=str, help=u'The source to process')

    output_group = argument_parser.add_argument_group(u'Output Arguments')
    output_group.add_argument(
        u'-w', u'--write', dest=u'analysis_output_file', action=u'store',
        type=str, default=None, help=(
            u'The destination file, storing the output of analysis'))

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
      self._output_writer.Write(u'ERROR: {0:s}'.format(exception))
      self._output_writer.Write(u'\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    return True

  def ParseOptions(self, options):
    """Parses tool specific options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    super(PstealTool, self).ParseOptions(options)

    # These arguments are parsed from argparse.Namespace, so we can make
    # tests consistents with the log2timeline/psort ones.
    self._single_process_mode = getattr(options, u'single_process', False)
    self._status_view_mode = getattr(options, u'status_view_mode', u'window')

    self.SetSourcePath(getattr(options, u'source', None))
    self._output_filename = getattr(options, u'analysis_output_file', None)
    self._ParseStorageFileOptions(options)

    self._options = options

    self._CreateOutputModule()


def Main():
  """The main function."""
  multiprocessing.freeze_support()

  tool = PstealTool()
  if not tool.ParseArguments():
    return False

  try:
    tool.ExtractEventsFromSources()
    tool.AnalyzeEvents()

  except (KeyboardInterrupt, errors.UserAbort):
    logging.warning(u'Aborted by user.')
    return False

  except errors.SourceScannerError as exception:
    logging.warning(exception)
    return False

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
