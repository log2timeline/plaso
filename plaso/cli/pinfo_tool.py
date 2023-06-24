# -*- coding: utf-8 -*-
"""The pinfo CLI tool."""

import argparse
import collections
import json
import os
import uuid

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.cli import logger
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.containers import events
from plaso.containers import event_sources
from plaso.containers import reports
from plaso.containers import warnings
from plaso.engine import path_helper
from plaso.lib import errors
from plaso.lib import loggers
from plaso.serializer import json_serializer
from plaso.storage import factory as storage_factory


class PinfoTool(tools.CLITool, tool_options.StorageFileOptions):
  """Pinfo CLI tool.

  Attributes:
    compare_storage_information (bool): True if the tool is used to compare
        stores.
    generate_report (bool): True if a predefined report type should be
        generated.
    list_reports (bool): True if the report types should be listed.
    list_sections (bool): True if the section types should be listed.
  """

  NAME = 'pinfo'
  DESCRIPTION = (
      'Shows information about a Plaso storage file, for example how it was '
      'collected, what information was extracted from a source, etc.')

  _DEFAULT_HASH_TYPE = 'sha256'
  _HASH_CHOICES = ('md5', 'sha1', 'sha256')

  _REPORTS = {
      'browser_search': (
          'Report browser searches determined by the browser_search '
          'analysis plugin.'),
      'chrome_extension': (
          'Report Chrome extensions determined by the chrome_extension '
          'analysis plugin.'),
      'environment_variables': (
          'Report environment variables extracted during processing.'),
      'file_hashes': 'Report file hashes calculated during processing.',
      'windows_services': (
          'Report Windows services and drivers extracted during processing.'),
      'winevt_providers': (
          'Report Windows EventLog providers extracted during processing.')}

  _DEFAULT_REPORT_TYPE = 'none'
  _REPORT_CHOICES = sorted(list(_REPORTS.keys()) + ['list', 'none'])

  _SECTIONS = {
      'events': 'Show information about events.',
      'reports': 'Show information about analysis reports.',
      'sessions': 'Show information about sessions.',
      'sources': 'Show information about event sources.',
      'warnings': 'Show information about warnings during processing.'}

  _DEFAULT_OUTPUT_FORMAT = 'text'
  _SUPPORTED_OUTPUT_FORMATS = ('json', 'markdown', 'text')

  _CONTAINER_TYPE_ANALYSIS_REPORT = reports.AnalysisReport.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_DATA_STREAM = events.EventDataStream.CONTAINER_TYPE
  _CONTAINER_TYPE_EVENT_SOURCE = event_sources.EventSource.CONTAINER_TYPE
  _CONTAINER_TYPE_EXTRACTION_WARNING = warnings.ExtractionWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_PREPROCESSING_WARNING = (
      warnings.PreprocessingWarning.CONTAINER_TYPE)
  _CONTAINER_TYPE_RECOVERY_WARNING = warnings.RecoveryWarning.CONTAINER_TYPE
  _CONTAINER_TYPE_TIMELINING_WARNING = warnings.TimeliningWarning.CONTAINER_TYPE

  def __init__(self, input_reader=None, output_writer=None):
    """Initializes the CLI tool object.

    Args:
      input_reader (Optional[InputReader]): input reader, where None indicates
          that the stdin input reader should be used.
      output_writer (Optional[OutputWriter]): output writer, where None
          indicates that the stdout output writer should be used.
    """
    super(PinfoTool, self).__init__(
        input_reader=input_reader, output_writer=output_writer)
    self._compare_storage_file_path = None
    self._output_filename = None
    self._output_format = 'text'
    self._hash_type = self._DEFAULT_HASH_TYPE
    self._process_memory_limit = None
    self._report_type = self._DEFAULT_REPORT_TYPE
    self._sections = None
    self._storage_file_path = None
    self._verbose = False

    self.compare_storage_information = False
    self.generate_report = False
    self.list_reports = False
    self.list_sections = False

  def _CalculateStorageCounters(self, storage_reader):
    """Calculates the counters of the entire storage.

    Args:
      storage_reader (StorageReader): storage reader.

    Returns:
      dict[str, collections.Counter]: storage counters.
    """
    # TODO: determine analysis report counter from actual stored analysis
    # reports or remove.
    analysis_reports_counter = collections.Counter()
    analysis_reports_counter_error = False

    event_labels_counter = {}
    if storage_reader.HasAttributeContainers('event_label_count'):
      event_labels_counter = {
          event_label_count.label: event_label_count.number_of_events
          for event_label_count in storage_reader.GetAttributeContainers(
              'event_label_count')}

    event_labels_counter = collections.Counter(event_labels_counter)
    event_labels_counter_error = False

    parsers_counter = {}
    if storage_reader.HasAttributeContainers('parser_count'):
      parsers_counter = {
          parser_count.name: parser_count.number_of_events
          for parser_count in storage_reader.GetAttributeContainers(
              'parser_count')}

    parsers_counter = collections.Counter(parsers_counter)
    parsers_counter_error = False

    storage_counters = {}

    extraction_warnings_by_path_spec = collections.Counter()
    extraction_warnings_by_parser_chain = collections.Counter()

    for warning in storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_EXTRACTION_WARNING):
      path_spec_string = self._GetPathSpecificationString(warning.path_spec)

      extraction_warnings_by_path_spec[path_spec_string] += 1
      extraction_warnings_by_parser_chain[warning.parser_chain] += 1

    storage_counters['extraction_warnings_by_path_spec'] = (
        extraction_warnings_by_path_spec)
    storage_counters['extraction_warnings_by_parser_chain'] = (
        extraction_warnings_by_parser_chain)

    recovery_warnings_by_path_spec = collections.Counter()
    recovery_warnings_by_parser_chain = collections.Counter()

    for warning in storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_RECOVERY_WARNING):
      path_spec_string = self._GetPathSpecificationString(warning.path_spec)

      recovery_warnings_by_path_spec[path_spec_string] += 1
      recovery_warnings_by_parser_chain[warning.parser_chain] += 1

    storage_counters['recovery_warnings_by_path_spec'] = (
        recovery_warnings_by_path_spec)
    storage_counters['recovery_warnings_by_parser_chain'] = (
        recovery_warnings_by_parser_chain)

    timelining_warnings_by_path_spec = collections.Counter()
    timelining_warnings_by_parser_chain = collections.Counter()

    if storage_reader.HasAttributeContainers(
        self._CONTAINER_TYPE_TIMELINING_WARNING):
      for warning in storage_reader.GetAttributeContainers(
          self._CONTAINER_TYPE_TIMELINING_WARNING):
        path_spec_string = self._GetPathSpecificationString(warning.path_spec)

        timelining_warnings_by_path_spec[path_spec_string] += 1
        timelining_warnings_by_parser_chain[warning.parser_chain] += 1

    storage_counters['timelining_warnings_by_path_spec'] = (
        timelining_warnings_by_path_spec)
    storage_counters['timelining_warnings_by_parser_chain'] = (
        timelining_warnings_by_parser_chain)

    if not analysis_reports_counter_error:
      storage_counters['analysis_reports'] = analysis_reports_counter

    if not event_labels_counter_error:
      storage_counters['event_labels'] = event_labels_counter

    if not parsers_counter_error:
      storage_counters['parsers'] = parsers_counter

    return storage_counters

  def _CheckStorageFile(self, storage_file_path, warn_about_existing=False):
    """Checks if the storage file path is valid.

    Args:
      storage_file_path (str): path of the storage file.
      warn_about_existing (bool): True if the user should be warned about
          the storage file already existing.

    Raises:
      BadConfigOption: if the storage file path is invalid.
    """
    if os.path.exists(storage_file_path):
      if not os.path.isfile(storage_file_path):
        raise errors.BadConfigOption(
            'Storage file: {0:s} already exists and is not a file.'.format(
                storage_file_path))

      if warn_about_existing:
        logger.warning('Appending to an already existing storage file.')

    dirname = os.path.dirname(storage_file_path)
    if not dirname:
      dirname = '.'

    # TODO: add a more thorough check to see if the storage file really is
    # a plaso storage file.

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          'Unable to write to storage file: {0:s}'.format(storage_file_path))

  def _CompareCounter(self, counter, compare_counter):
    """Compares two counters.

    Args:
      counter (collections.Counter): counter.
      compare_counter (collections.Counter): counter to compare against.

    Returns:
      dict[str, tuple[int, int]]: mismatching results per key.
    """
    keys = set(counter.keys())
    keys.union(compare_counter.keys())

    differences = {}
    for key in keys:
      value = counter.get(key, 0)
      compare_value = compare_counter.get(key, 0)
      if value != compare_value:
        differences[key] = (value, compare_value)

    return differences

  def _CompareStores(self, storage_reader, compare_storage_reader):
    """Compares the contents of two stores.

    Args:
      storage_reader (StorageReader): storage reader.
      compare_storage_reader (StorageReader): storage to compare against.

    Returns:
      bool: True if the content of the stores is identical.
    """
    stores_are_identical = True

    storage_counters = self._CalculateStorageCounters(storage_reader)
    compare_storage_counters = self._CalculateStorageCounters(
        compare_storage_reader)

    # Compare number of events.
    parsers_counter = storage_counters.get('parsers', collections.Counter())
    compare_parsers_counter = compare_storage_counters.get(
        'parsers', collections.Counter())
    differences = self._CompareCounter(parsers_counter, compare_parsers_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences,
          column_names=['Parser (plugin) name', 'Number of events'],
          title='Events generated per parser')

    # Compare extraction warnings by parser chain.
    warnings_counter = storage_counters.get(
        'extraction_warnings_by_parser_chain', collections.Counter())
    compare_warnings_counter = compare_storage_counters.get(
        'extraction_warnings_by_parser_chain', collections.Counter())
    differences = self._CompareCounter(
        warnings_counter, compare_warnings_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences,
          column_names=['Parser (plugin) name', 'Number of warnings'],
          title='Extraction warnings generated per parser')

    # Compare extraction warnings by path specification
    warnings_counter = storage_counters.get(
        'extraction_warnings_by_path_spec', collections.Counter())
    compare_warnings_counter = compare_storage_counters.get(
        'extraction_warnings_by_path_spec', collections.Counter())
    differences = self._CompareCounter(
        warnings_counter, compare_warnings_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences, column_names=['Number of warnings', 'Pathspec'],
          reverse=True, title='Pathspecs with most extraction warnings')

    # Compare recovery warnings by parser chain.
    warnings_counter = storage_counters.get(
        'recovery_warnings_by_parser_chain', collections.Counter())
    compare_warnings_counter = compare_storage_counters.get(
        'recovery_warnings_by_parser_chain', collections.Counter())
    differences = self._CompareCounter(
        warnings_counter, compare_warnings_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences,
          column_names=['Parser (plugin) name', 'Number of warnings'],
          title='Recovery warnings generated per parser')

    # Compare recovery warnings by path specification
    warnings_counter = storage_counters.get(
        'recovery_warnings_by_path_spec', collections.Counter())
    compare_warnings_counter = compare_storage_counters.get(
        'recovery_warnings_by_path_spec', collections.Counter())
    differences = self._CompareCounter(
        warnings_counter, compare_warnings_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences, column_names=['Number of warnings', 'Pathspec'],
          reverse=True, title='Pathspecs with most recovery warnings')

    # Compare timelining warnings by parser chain.
    warnings_counter = storage_counters.get(
        'timelining_warnings_by_parser_chain', collections.Counter())
    compare_warnings_counter = compare_storage_counters.get(
        'timelining_warnings_by_parser_chain', collections.Counter())
    differences = self._CompareCounter(
        warnings_counter, compare_warnings_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences,
          column_names=['Parser (plugin) name', 'Number of warnings'],
          title='Timelining warnings generated per parser')

    # Compare timelining warnings by path specification.
    warnings_counter = storage_counters.get(
        'timelining_warnings_by_path_spec', collections.Counter())
    compare_warnings_counter = compare_storage_counters.get(
        'timelining_warnings_by_path_spec', collections.Counter())
    differences = self._CompareCounter(
        warnings_counter, compare_warnings_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences, column_names=['Number of warnings', 'Pathspec'],
          reverse=True, title='Pathspecs with most timelining warnings')

    # Compare event labels.
    labels_counter = storage_counters.get('event_labels', collections.Counter())
    compare_labels_counter = compare_storage_counters.get(
        'event_labels', collections.Counter())
    differences = self._CompareCounter(labels_counter, compare_labels_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences, column_names=['Label', 'Number of event tags'],
          title='Event tags generated per label')

    # Compare analysis reports.
    reports_counter = storage_counters.get(
        'analysis_reports', collections.Counter())
    compare_reports_counter = compare_storage_counters.get(
        'analysis_reports', collections.Counter())
    differences = self._CompareCounter(reports_counter, compare_reports_counter)

    if differences:
      stores_are_identical = False

      self._PrintCounterDifferences(
          differences, column_names=['Plugin name', 'Number of reports'],
          title='Reports generated per plugin')

    return stores_are_identical

  def _GenerateAnalysisResultsReport(
      self, storage_reader, json_base_type, column_titles, container_type,
      attribute_names, attribute_mappings):
    """Generates an analysis results report.

    Args:
      storage_reader (StorageReader): storage reader.
      json_base_type (str): JSON base type.
      column_titles (list[str]): column titles of the Markdown and tab
          separated tables.
      container_type (str): attribute container type.
      attribute_names (list[str]): names of the attributes to report.
      attribute_mappings (dict[str, dict[st, str]]): mappings of attribute
          values to human readable strings.
    """
    self._GenerateReportHeader(json_base_type, column_titles)

    entry_format_string = self._GenerateReportEntryFormatString(attribute_names)

    if storage_reader.HasAttributeContainers(container_type):
      generator = storage_reader.GetAttributeContainers(container_type)

      for artifact_index, analysis_result in enumerate(generator):
        if self._output_format == 'json':
          if artifact_index > 0:
            self._output_writer.Write(',\n')

        attribute_values = analysis_result.CopyToDict()
        for key in attribute_names:
          value = attribute_values.get(key, None)
          if value is None:
            value = ''
          elif isinstance(value, int):
            value = attribute_mappings.get(key, {}).get(value, value)
          elif self._output_format == 'json':
            value = value.replace('\\', '\\\\')
          attribute_values[key] = value

        self._output_writer.Write(entry_format_string.format(
            **attribute_values))

    self._GenerateReportFooter()

  def _GenerateFileHashesReport(self, storage_reader):
    """Generates a file hashes report.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    column_titles = [
        '{0:s} hash'.format(self._hash_type.upper()),
        'Display name']
    self._GenerateReportHeader('file_hashes', column_titles)

    hash_attribute_name = '{0:s}_hash'.format(self._hash_type)
    attribute_names = [hash_attribute_name, 'display_name']
    entry_format_string = self._GenerateReportEntryFormatString(attribute_names)

    generator = storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_DATA_STREAM)

    for event_data_stream_index, event_data_stream in enumerate(generator):
      if self._output_format == 'json':
        if event_data_stream_index > 0:
          self._output_writer.Write(',\n')

      hash_value = getattr(
          event_data_stream, hash_attribute_name, None) or 'N/A'

      display_name = 'N/A'
      if event_data_stream.path_spec:
        display_name = path_helper.PathHelper.GetDisplayNameForPathSpec(
           event_data_stream.path_spec)

      attribute_values = {
          'display_name': display_name, hash_attribute_name: hash_value}

      self._output_writer.Write(entry_format_string.format(
          **attribute_values))

    self._GenerateReportFooter()

  def _GenerateReportEntryFormatString(self, attribute_names):
    """Generates a report entry format string.

    Args:
      attribute_names (list[str]): names of the attributes to report.

    Returns:
      str: entry format string.
    """
    if self._output_format == 'json':
      return '    {{{{{0:s}}}}}'.format(', '.join([
          '"{0:s}": "{{{0:s}!s}}"'.format(name) for name in attribute_names]))

    if self._output_format == 'markdown':
      return '{0:s}\n'.format(' | '.join([
          '{{{0:s}!s}}'.format(name) for name in attribute_names]))

    if self._output_format == 'text':
      return '{0:s}\n'.format('\t'.join([
          '{{{0:s}!s}}'.format(name) for name in attribute_names]))

    return ''

  def _GenerateReportFooter(self):
    """Generates a report footer."""
    if self._output_format == 'json':
      self._output_writer.Write('\n]}\n')

  def _GenerateReportHeader(self, json_base_type, column_titles):
    """Generates a report header.

    Args:
      json_base_type (str): JSON base type.
      column_titles (list[str]): column titles of the Markdown and tab
          separated tables.
    """
    if self._output_format == 'json':
      self._output_writer.Write('{{"{0:s}": [\n'.format(json_base_type))

    elif self._output_format == 'markdown':
      self._output_writer.Write('{0:s}\n'.format(' | '.join(column_titles)))
      self._output_writer.Write(
          '{0:s}\n'.format(' | '.join(['---'] * len(column_titles))))

    elif self._output_format == 'text':
      self._output_writer.Write('{0:s}\n'.format('\t'.join(column_titles)))

  def _GenerateWinEvtProvidersReport(self, storage_reader):
    """Generates a Windows Event Log providers report.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    column_titles = [
        'Identifier', 'Log source(s)', 'Log type(s)', 'Event message file(s)']
    self._GenerateReportHeader('winevt_providers', column_titles)

    attribute_names = [
        'identifier', 'log_sources', 'log_types', 'event_message_files']
    entry_format_string = self._GenerateReportEntryFormatString(attribute_names)

    if storage_reader.HasAttributeContainers('windows_eventlog_provider'):
      generator = storage_reader.GetAttributeContainers(
          'windows_eventlog_provider')

      for artifact_index, artifact in enumerate(generator):
        if self._output_format == 'json':
          if artifact_index > 0:
            self._output_writer.Write(',\n')

        attribute_values = {
            'identifier': artifact.identifier or '',
            'event_message_files': artifact.event_message_files or [],
            'log_sources': artifact.log_sources or [],
            'log_types': artifact.log_types or []}

        self._output_writer.Write(entry_format_string.format(
            **attribute_values))

    self._GenerateReportFooter()

  def _GetStorageReader(self, path):
    """Retrieves a storage reader.

    Args:
      path (str): path of the storage file.

    Returns:
      StorageReader: storage reader or None if the storage file format
          is not supported.

    Raises:
      BadConfigOption: if the storage file format is not supported.
    """
    storage_reader = (
        storage_factory.StorageFactory.CreateStorageReaderForFile(path))
    if not storage_reader:
      raise errors.BadConfigOption(
          'Format of storage file: {0:s} not supported'.format(path))

    return storage_reader

  def _PrintAnalysisReportCounter(
      self, analysis_reports_counter, session_identifier=None):
    """Prints the analysis reports counter.

    Args:
      analysis_reports_counter (collections.Counter): number of analysis
          reports per analysis plugin.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    if self._output_format == 'json':
      json_string = json.dumps(analysis_reports_counter)
      self._output_writer.Write(
          '"analysis_reports": {0:s}'.format(json_string))

    elif (self._output_format in ('markdown', 'text') and
          analysis_reports_counter):
      title = 'Reports generated per plugin'
      if session_identifier:
        title = '{0:s}: {1:s}'.format(title, session_identifier)

      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type,
          column_names=['Plugin name', 'Number of reports'], title=title)

      for key, value in sorted(analysis_reports_counter.items()):
        if key != 'total':
          table_view.AddRow([key, value])

      try:
        total = analysis_reports_counter['total']
      except KeyError:
        total = 'N/A'

      table_view.AddRow(['Total', total])

      table_view.Write(self._output_writer)

  def _PrintAnalysisReportsDetails(self, storage_reader):
    """Prints the details of the analysis reports.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    has_analysis_reports = storage_reader.HasAttributeContainers(
        self._CONTAINER_TYPE_ANALYSIS_REPORT)

    if self._output_format == 'text' and not has_analysis_reports:
      self._output_writer.Write('\nNo analysis reports stored.\n')

    else:
      generator = storage_reader.GetAttributeContainers(
          self._CONTAINER_TYPE_ANALYSIS_REPORT)

      for index, analysis_report in enumerate(generator):
        date_time_string = None
        if analysis_report.time_compiled is not None:
          date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
              timestamp=analysis_report.time_compiled)
          date_time_string = date_time.CopyToDateTimeStringISO8601()

        title = 'Analysis report: {0:d}'.format(index)
        table_view = views.ViewsFactory.GetTableView(
            self._views_format_type, title=title)

        table_view.AddRow(['Name plugin', analysis_report.plugin_name or 'N/A'])
        table_view.AddRow(['Date and time', date_time_string or 'N/A'])
        table_view.AddRow([
            'Event filter', analysis_report.event_filter or 'N/A'])

        if not analysis_report.analysis_counter:
          table_view.AddRow(['Text', analysis_report.text or ''])
        else:
          table_view.AddRow(['Results', ''])
          for key, value in sorted(analysis_report.analysis_counter.items()):
            table_view.AddRow([key, value])

        table_view.Write(self._output_writer)

  def _PrintAnalysisReportSection(
      self, storage_reader, analysis_reports_counter):
    """Prints the analysis reports section.

    Args:
      storage_reader (StorageReader): storage reader.
      analysis_reports_counter (collections.Counter): number of analysis
          reports per analysis plugin.
    """
    self._PrintAnalysisReportCounter(analysis_reports_counter)

    if self._output_format in ('markdown', 'text'):
      self._PrintAnalysisReportsDetails(storage_reader)

  def _PrintCounterDifferences(
      self, differences, column_names=None, reverse=False, title=None):
    """Prints the counter differences.

    Args:
      differences (dict[str, tuple[int, int]]): mismatching results per key.
      column_names (Optional[list[str]]): column names.
      reverse (Optional[bool]): True if the key and values of differences
          should be printed in reverse order.
      title (Optional[str]): title.
    """
    # TODO: add support for 3 column table?
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=column_names, title=title)

    for key, value in sorted(differences.items()):
      value_string = '{0:d} ({1:d})'.format(value[0], value[1])
      if reverse:
        table_view.AddRow([value_string, key])
      else:
        table_view.AddRow([key, value_string])

    table_view.Write(self._output_writer)
    self._output_writer.Write('\n')

  def _PrintEventLabelsCounter(
      self, event_labels_counter, session_identifier=None):
    """Prints the event labels counter.

    Args:
      event_labels_counter (collections.Counter): number of event tags per
          label.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    if self._output_format == 'json':
      json_string = json.dumps(event_labels_counter)
      self._output_writer.Write('"event_labels": {0:s}'.format(json_string))

    elif self._output_format in ('markdown', 'text'):
      if self._output_format == 'text' and not event_labels_counter:
        if not session_identifier:
          self._output_writer.Write('\nNo events labels stored.\n')
      else:
        title = 'Event tags generated per label'

        if session_identifier:
          title = '{0:s}: {1:s}'.format(title, session_identifier)
          title_level = 4
        else:
          title_level = 2

        if not event_labels_counter:
          if not session_identifier:
            self._output_writer.Write('{0:s} {1:s}\n\nN/A\n\n'.format(
                '#' * title_level, title))
        else:
          table_view = views.ViewsFactory.GetTableView(
              self._views_format_type,
              column_names=['Label', 'Number of event tags'], title=title,
              title_level=title_level)

          for key, value in sorted(event_labels_counter.items()):
            if key != 'total':
              table_view.AddRow([key, value])

          try:
            total = event_labels_counter['total']
          except KeyError:
            total = 'N/A'

          table_view.AddRow(['Total', total])

          table_view.Write(self._output_writer)

  def _PrintParsersCounter(self, parsers_counter, session_identifier=None):
    """Prints the parsers counter

    Args:
      parsers_counter (collections.Counter): number of events per parser or
          parser plugin.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    if self._output_format == 'json':
      if session_identifier:
        self._output_writer.Write(', ')

      json_string = json.dumps(parsers_counter)
      self._output_writer.Write('"parsers": {0:s}'.format(json_string))

    elif self._output_format in ('markdown', 'text'):
      if self._output_format == 'text' and not parsers_counter:
        if not session_identifier:
          self._output_writer.Write('\nNo events stored.\n')

      else:
        title = 'Events generated per parser'
        if session_identifier:
          title = '{0:s}: {1:s}'.format(title, session_identifier)
          title_level = 4
        else:
          title_level = 2

        if not parsers_counter:
          if not session_identifier:
            self._output_writer.Write('{0:s} {1:s}\n\nN/A\n\n'.format(
                '#' * title_level, title))
        else:
          table_view = views.ViewsFactory.GetTableView(
              self._views_format_type,
              column_names=['Parser (plugin) name', 'Number of events'],
              title=title, title_level=title_level)

          for key, value in sorted(parsers_counter.items()):
            if key != 'total':
              table_view.AddRow([key, value])

          table_view.AddRow(['Total', parsers_counter['total']])

          table_view.Write(self._output_writer)

  def _PrintPreprocessingWarningsDetails(self, storage_reader):
    """Prints the details of the preprocessing warnings.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    generator = storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_PREPROCESSING_WARNING)

    for index, warning in enumerate(generator):
      title = 'Preprocessing warning: {0:d}'.format(index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['Message', warning.message])
      table_view.AddRow(['Plugin name', warning.plugin_name])

      if warning.path_spec:
        # TODO: add helper method to format path spec as row.
        path_spec_string = self._GetPathSpecificationString(warning.path_spec)

        for path_index, line in enumerate(path_spec_string.split('\n')):
          if not line:
            continue

          if path_index == 0:
            table_view.AddRow(['Path specification', line])
          else:
            table_view.AddRow(['', line])

      table_view.Write(self._output_writer)

  def _PrintWarningsDetails(self, storage_reader, container_type, warning_type):
    """Prints the details of warnings.

    Args:
      storage_reader (StorageReader): storage reader.
      container_type (str): attribute container type.
      warning_type (str): warning type.
    """
    generator = storage_reader.GetAttributeContainers(container_type)

    for index, warning in enumerate(generator):
      title = '{0:s} warning: {1:d}'.format(warning_type, index)
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title=title)

      table_view.AddRow(['Message', warning.message])
      table_view.AddRow(['Parser chain', warning.parser_chain])

      path_spec_string = self._GetPathSpecificationString(warning.path_spec)

      for path_index, line in enumerate(path_spec_string.split('\n')):
        if not line:
          continue

        if path_index == 0:
          table_view.AddRow(['Path specification', line])
        else:
          table_view.AddRow(['', line])

      table_view.Write(self._output_writer)

  def _PrintSessionDetailsAsJSON(self, session):
    """Prints the details of a session as JSON.

    Args:
      session (Session): session.
    """
    json_string = (
        json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
            session))
    self._output_writer.Write('"session": {0:s}'.format(json_string))

  def _PrintSessionDetailsAsTable(self, session, session_identifier):
    """Prints the details of a session as a table.

    Args:
      session (Session): session.
      session_identifier (str): session identifier, formatted as a UUID.
    """
    start_time = 'N/A'
    if session.start_time is not None:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=session.start_time)
      start_time = date_time.CopyToDateTimeStringISO8601()

    completion_time = 'N/A'
    if session.completion_time is not None:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=session.completion_time)
      completion_time = date_time.CopyToDateTimeStringISO8601()

    enabled_parser_names = 'N/A'
    if session.enabled_parser_names:
      enabled_parser_names = ', '.join(sorted(session.enabled_parser_names))

    command_line_arguments = session.command_line_arguments or 'N/A'
    parser_filter_expression = session.parser_filter_expression or 'N/A'
    preferred_encoding = session.preferred_encoding or 'N/A'
    preferred_time_zone = session.preferred_time_zone or 'N/A'

    if session.artifact_filters:
      artifact_filters_string = ', '.join(session.artifact_filters)
    else:
      artifact_filters_string = 'N/A'
    filter_file = session.filter_file or 'N/A'

    title = 'Session: {0:s}'.format(session_identifier)
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title=title)

    table_view.AddRow(['Start time', start_time])
    table_view.AddRow(['Completion time', completion_time])
    table_view.AddRow(['Product name', session.product_name])
    table_view.AddRow(['Product version', session.product_version])
    table_view.AddRow(['Command line arguments', command_line_arguments])
    table_view.AddRow(['Parser filter expression', parser_filter_expression])
    table_view.AddRow(['Enabled parser and plugins', enabled_parser_names])
    table_view.AddRow(['Preferred encoding', preferred_encoding])
    table_view.AddRow(['Preferred time zone', preferred_time_zone])
    table_view.AddRow(['Debug mode', session.debug_mode])
    table_view.AddRow(['Artifact filters', artifact_filters_string])
    table_view.AddRow(['Filter file', filter_file])

    table_view.Write(self._output_writer)

  def _PrintSessionsDetails(self, storage_reader):
    """Prints the details of the sessions.

    Args:
      storage_reader (BaseStore): storage.
    """
    if self._output_format == 'json':
      self._output_writer.Write('"sessions": {')

    for session_index, session in enumerate(storage_reader.GetSessions()):
      session_identifier = uuid.UUID(hex=session.identifier)
      session_identifier = '{0!s}'.format(session_identifier)

      if self._output_format == 'json':
        if session_index != 0:
          self._output_writer.Write(', ')

        self._PrintSessionDetailsAsJSON(session)

      elif self._output_format in ('markdown', 'text'):
        self._PrintSessionDetailsAsTable(session, session_identifier)

      if self._verbose:
        system_configuration = storage_reader.GetAttributeContainerByIndex(
            'system_configuration', session_index)
        if system_configuration:
          self._PrintSystemConfigurations(
              storage_reader, [system_configuration],
              session_identifier=session_identifier)

    if self._output_format == 'json':
      self._output_writer.Write('}')

  def _PrintSessionsOverview(self, storage_reader):
    """Prints a sessions overview.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Sessions', title_level=2)

    for session in storage_reader.GetSessions():
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=session.start_time)
      start_time = date_time.CopyToDateTimeStringISO8601()

      session_identifier = uuid.UUID(hex=session.identifier)
      session_identifier = '{0!s}'.format(session_identifier)
      table_view.AddRow([session_identifier, start_time])

    table_view.Write(self._output_writer)

  def _PrintSessionsSection(self, storage_reader):
    """Prints the session section.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    if self._output_format in ('markdown', 'text'):
      self._PrintSessionsOverview(storage_reader)

    if (self._output_format == 'json' or self._verbose or
        'sessions' in self._sections):
      self._PrintSessionsDetails(storage_reader)

  def _PrintSystemConfiguration(
      self, storage_reader, system_configuration, session_identifier=None):
    """Prints the details of a system configuration.

    Args:
      storage_reader (StorageReader): storage reader.
      system_configuration (SystemConfiguration): system configuration.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    if not system_configuration:
      return

    title = 'System configuration'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title=title)

    hostname = 'N/A'
    if system_configuration.hostname:
      hostname = system_configuration.hostname.name

    operating_system = system_configuration.operating_system or 'N/A'
    operating_system_product = (
        system_configuration.operating_system_product or 'N/A')
    operating_system_version = (
        system_configuration.operating_system_version or 'N/A')
    language = system_configuration.language or 'N/A'
    code_page = system_configuration.code_page or 'N/A'
    keyboard_layout = system_configuration.keyboard_layout or 'N/A'
    time_zone = system_configuration.time_zone or 'N/A'

    table_view.AddRow(['Hostname', hostname])
    table_view.AddRow(['Operating system', operating_system])
    table_view.AddRow(['Operating system product', operating_system_product])
    table_view.AddRow(['Operating system version', operating_system_version])
    table_view.AddRow(['Language', language])
    table_view.AddRow(['Code page', code_page])
    table_view.AddRow(['Keyboard layout', keyboard_layout])
    table_view.AddRow(['Time zone', time_zone])

    table_view.Write(self._output_writer)

    title = 'Available time zones'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Name', 'Offset from UTC'], title=title)

    # TODO: filter time zones on specific system configuration.
    for time_zone in storage_reader.GetAttributeContainers('time_zone'):
      hours_from_utc, minutes_from_utc = divmod(time_zone.offset, 60)
      if hours_from_utc < 0:
        sign = '+'
        hours_from_utc *= -1
      else:
        sign = '-'

      time_zone_offset = '{0:s}{1:02d}:{2:02d}'.format(
          sign, hours_from_utc, minutes_from_utc)
      table_view.AddRow([time_zone.name, time_zone_offset])

    table_view.Write(self._output_writer)

    title = 'User accounts'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Username', 'User directory'], title=title)

    # TODO: filter user accounts on specific system configuration.
    for user_account in storage_reader.GetAttributeContainers('user_account'):
      table_view.AddRow([user_account.username, user_account.user_directory])

    table_view.Write(self._output_writer)

  def _PrintSystemConfigurations(
      self, storage_reader, system_configurations, session_identifier=None):
    """Prints the details of system configurations.

    Args:
      storage_reader (StorageReader): storage reader.
      system_configurations (list[SystemConfiguration]): system configurations.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    if self._output_format == 'json':
      self._output_writer.Write(', "system_configurations": {')

    for configuration_index, configuration in enumerate(system_configurations):
      if self._output_format == 'json':
        if configuration_index != 0:
          self._output_writer.Write(', ')

        json_string = (
            json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
                configuration.system_configuration))
        self._output_writer.Write(
            '"system_configuration": {0:s}'.format(json_string))

      elif self._output_format in ('markdown', 'text'):
        self._PrintSystemConfiguration(
            storage_reader, configuration,
            session_identifier=session_identifier)

    if self._output_format == 'json':
      self._output_writer.Write('}')

  def _PrintStorageInformation(self, storage_reader):
    """Prints information about the store.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    if self._output_format == 'json':
      self._output_writer.Write('{')
    elif self._output_format in ('markdown', 'text'):
      self._PrintStorageOverviewAsTable(storage_reader)

    section_written = False

    if self._sections == 'all' or 'sessions' in self._sections:
      self._PrintSessionsSection(storage_reader)
      section_written = True

    if self._sections == 'all' or 'sources' in self._sections:
      if self._output_format == 'json' and section_written:
        self._output_writer.Write(', ')

      self._PrintSourcesOverview(storage_reader)
      section_written = True

    if self._output_format == 'json' and section_written:
      self._output_writer.Write(', ')

    storage_counters = self._CalculateStorageCounters(storage_reader)

    if self._output_format == 'json':
      self._output_writer.Write('"storage_counters": {')

    section_written = False

    if self._sections == 'all' or 'events' in self._sections:
      parsers = storage_counters.get('parsers', collections.Counter())

      self._PrintParsersCounter(parsers)
      section_written = True

      event_labels = storage_counters.get(
          'event_labels', collections.Counter())

      if self._output_format == 'json' and section_written:
        self._output_writer.Write(', ')

      self._PrintEventLabelsCounter(event_labels)

    if self._sections == 'all' or 'warnings' in self._sections:
      if self._output_format == 'json' and section_written:
        self._output_writer.Write(', ')

      self._PrintWarningsSection(storage_reader, storage_counters)
      section_written = True

    if self._sections == 'all' or 'reports' in self._sections:
      if self._output_format == 'json' and section_written:
        self._output_writer.Write(', ')

      analysis_reports = storage_counters.get(
          'analysis_reports', collections.Counter())

      self._PrintAnalysisReportSection(storage_reader, analysis_reports)

    if self._output_format == 'json':
      self._output_writer.Write('}')

    if self._output_format == 'json':
      self._output_writer.Write('}')
    elif self._output_format in ('markdown', 'text'):
      self._output_writer.Write('\n')

  def _PrintSourcesOverview(self, storage_reader):
    """Prints a sources overview.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    if self._output_format == 'json':
      self._output_writer.Write('"event_sources": {')

    elif self._output_format in ('markdown', 'text'):
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title='Event sources', title_level=2)

    generator = storage_reader.GetAttributeContainers(
        self._CONTAINER_TYPE_EVENT_SOURCE)

    number_of_event_sources = 0
    for source_index, source in enumerate(generator):
      if self._output_format == 'json':
        if source_index != 0:
          self._output_writer.Write(', ')

        json_string = (
            json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
                source))
        self._output_writer.Write('"source": {0:s}'.format(json_string))

      elif self._output_format in ('markdown', 'text'):
        if self._verbose or 'sources' in self._sections:
          path_spec_string = self._GetPathSpecificationString(source.path_spec)

          for path_index, line in enumerate(path_spec_string.split('\n')):
            if not line:
              continue

            if path_index == 0:
              table_view.AddRow(['{0:d}'.format(source_index), line])
            else:
              table_view.AddRow(['', line])

      number_of_event_sources += 1

    if self._output_format == 'json':
      self._output_writer.Write('}')
    elif self._output_format in ('markdown', 'text'):
      if not (self._verbose or 'sources' in self._sections):
        table_view.AddRow(['Total', '{0:d}'.format(number_of_event_sources)])
      table_view.Write(self._output_writer)

  def _PrintStorageOverviewAsTable(self, storage_reader):
    """Prints a storage overview as a table.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    format_version = storage_reader.GetFormatVersion()
    serialization_format = storage_reader.GetSerializationFormat()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Plaso Storage Information',
        title_level=1)
    table_view.AddRow(['Filename', os.path.basename(self._storage_file_path)])
    table_view.AddRow(['Format version', format_version])
    table_view.AddRow(['Serialization format', serialization_format])
    table_view.Write(self._output_writer)

  def _PrintWarningCountersJSON(
      self, warnings_by_path_spec, warnings_by_parser_chain):
    """Prints JSON containing a summary of the number of warnings.

    Args:
      warnings_by_path_spec (collections.Counter): number of warnings per
          path specification.
      warnings_by_parser_chain (collections.Counter): number of warnings per
          parser chain.
    """
    json_string = json.dumps(warnings_by_parser_chain)
    self._output_writer.Write(
        '"warnings_by_parser": {0:s}'.format(json_string))

    json_string = json.dumps(warnings_by_path_spec)
    self._output_writer.Write(
        ', "warnings_by_path_spec": {0:s}'.format(json_string))

  def _PrintWarningCountersTable(
      self, description, warnings_by_path_spec, warnings_by_parser_chain):
    """Prints a table containing a summary of the number of warnings.

    Args:
      description (str): description of the type of warning.
      warnings_by_path_spec (collections.Counter): number of warnings per
          path specification.
      warnings_by_parser_chain (collections.Counter): number of warnings per
          parser chain.
    """
    if warnings_by_parser_chain:
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type,
          column_names=['Parser (plugin) name', 'Number of warnings'],
          title='{0:s} warnings generated per parser'.format(
              description.title()))
      for parser_chain, count in warnings_by_parser_chain.items():
        parser_chain = parser_chain or '<No parser>'
        table_view.AddRow([parser_chain, '{0:d}'.format(count)])
      table_view.Write(self._output_writer)

    if warnings_by_path_spec:
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type,
          column_names=['Number of warnings', 'Pathspec'],
          title='Path specifications with most {0:s} warnings'.format(
              description))

      for path_spec, count in warnings_by_path_spec.most_common(10):
        for path_index, line in enumerate(path_spec.split('\n')):
          if not line:
            continue

          if path_index == 0:
            table_view.AddRow(['{0:d}'.format(count), line])
          else:
            table_view.AddRow(['', line])

      table_view.Write(self._output_writer)

  def _PrintWarningsSection(self, storage_reader, storage_counters):
    """Prints the warnings section.

    Args:
      storage_reader (StorageReader): storage reader.
      storage_counters (dict[str, collections.Counter]): storage counters.
    """
    has_extraction_warnings = storage_reader.HasAttributeContainers(
        self._CONTAINER_TYPE_EXTRACTION_WARNING)

    has_preprocessing_warnings = storage_reader.HasAttributeContainers(
        self._CONTAINER_TYPE_PREPROCESSING_WARNING)

    has_recovery_warnings = storage_reader.HasAttributeContainers(
        self._CONTAINER_TYPE_RECOVERY_WARNING)

    if (self._output_format == 'text' and not has_extraction_warnings and
        not has_preprocessing_warnings and not has_recovery_warnings):
      self._output_writer.Write('\nNo warnings stored.\n')

    else:
      warnings_by_path_spec = storage_counters.get(
          'extraction_warnings_by_path_spec', collections.Counter())
      warnings_by_parser_chain = storage_counters.get(
          'extraction_warnings_by_parser_chain', collections.Counter())

      if self._output_format == 'json':
        self._PrintWarningCountersJSON(
            warnings_by_path_spec, warnings_by_parser_chain)

      elif self._output_format in ('markdown', 'text'):
        self._PrintWarningCountersTable(
            'extraction', warnings_by_path_spec, warnings_by_parser_chain)

        if self._verbose or 'warnings' in self._sections:
          self._PrintWarningsDetails(
              storage_reader, self._CONTAINER_TYPE_EXTRACTION_WARNING,
              'Extraction')

      warnings_by_path_spec = storage_counters.get(
          'preprocessing_warnings_by_path_spec', collections.Counter())
      warnings_by_parser_chain = storage_counters.get(
          'preprocessing_warnings_by_parser_chain', collections.Counter())

      # TODO: print preprocessing warnings as part of JSON output format.

      if self._output_format in ('markdown', 'text'):
        self._PrintWarningCountersTable(
            'preprocessing', warnings_by_path_spec, warnings_by_parser_chain)

        if self._verbose or 'warnings' in self._sections:
          self._PrintPreprocessingWarningsDetails(storage_reader)

      warnings_by_path_spec = storage_counters.get(
          'recovery_warnings_by_path_spec', collections.Counter())
      warnings_by_parser_chain = storage_counters.get(
          'recovery_warnings_by_parser_chain', collections.Counter())

      # TODO: print recovery warnings as part of JSON output format.

      if self._output_format in ('markdown', 'text'):
        self._PrintWarningCountersTable(
            'recovery', warnings_by_path_spec, warnings_by_parser_chain)

        if self._verbose or 'warnings' in self._sections:
          self._PrintWarningsDetails(
              storage_reader, self._CONTAINER_TYPE_RECOVERY_WARNING,
              'Recovery')

      warnings_by_path_spec = storage_counters.get(
          'timelining_warnings_by_path_spec', collections.Counter())
      warnings_by_parser_chain = storage_counters.get(
          'timelining_warnings_by_parser_chain', collections.Counter())

      # TODO: print timelining warnings as part of JSON output format.

      if self._output_format in ('markdown', 'text'):
        self._PrintWarningCountersTable(
            'timelining', warnings_by_path_spec, warnings_by_parser_chain)

        if self._verbose or 'warnings' in self._sections:
          self._PrintWarningsDetails(
              storage_reader, self._CONTAINER_TYPE_TIMELINING_WARNING,
              'Timelining')

  def CompareStores(self):
    """Compares the contents of two stores.

    Returns:
      bool: True if the content of the stores is identical.

    Raises:
      BadConfigOption: if the storage file format is not supported.
    """
    storage_reader = self._GetStorageReader(self._storage_file_path)
    compare_storage_reader = self._GetStorageReader(
        self._compare_storage_file_path)

    try:
      result = self._CompareStores(storage_reader, compare_storage_reader)

    finally:
      compare_storage_reader.Close()
      storage_reader.Close()

    if result:
      self._output_writer.Write('Storage files are identical.\n')
    else:
      self._output_writer.Write('Storage files are different.\n')

    return result

  def GenerateReport(self):
    """Generates a report.

    Raises:
      BadConfigOption: if the storage file format is not supported.
    """
    storage_reader = self._GetStorageReader(self._storage_file_path)

    try:
      if self._report_type == 'browser_search':
        column_titles = ['Search engine', 'Search term', 'Number of queries']
        attribute_names = ['search_engine', 'search_term', 'number_of_queries']
        attribute_mappings = {}
        self._GenerateAnalysisResultsReport(
            storage_reader, 'browser_searches', column_titles,
            'browser_search_analysis_result', attribute_names,
            attribute_mappings)

      elif self._report_type == 'chrome_extension':
        column_titles = ['Username', 'Extension identifier', 'Extension']
        attribute_names = ['username', 'extension_identifier', 'extension']
        attribute_mappings = {}
        self._GenerateAnalysisResultsReport(
            storage_reader, 'chrome_extensions', column_titles,
            'chrome_extension_analysis_result', attribute_names,
            attribute_mappings)

      elif self._report_type == 'environment_variables':
        column_titles = ['Name', 'Value']
        attribute_names = ['name', 'value']
        attribute_mappings = {}
        self._GenerateAnalysisResultsReport(
            storage_reader, 'environment_variables', column_titles,
            'environment_variable', attribute_names, attribute_mappings)

      elif self._report_type == 'file_hashes':
        self._GenerateFileHashesReport(storage_reader)

      elif self._report_type == 'windows_services':
        column_titles = ['Name', 'Service type', 'Start type', 'Image path']
        attribute_names = ['name', 'service_type', 'start_type', 'image_path']
        # TODO: consider using message formatting helpers?
        attribute_mappings = {
            'service_type': {
                0x01: 'Kernel device driver (0x01)',
                0x02: 'File system driver (0x02)',
                0x04: 'Adapter (0x04)',
                0x10: 'Stand-alone service (0x10)',
                0x20: 'Shared service (0x20)'},
            'start_type': {
                0: 'Boot (0)',
                1: 'System (1)',
                2: 'Automatic (2)',
                3: 'On demand (3)',
                4: 'Disabled (4)'}
        }
        self._GenerateAnalysisResultsReport(
            storage_reader, 'windows_services', column_titles,
            'windows_service_configuration', attribute_names,
            attribute_mappings)

      elif self._report_type == 'winevt_providers':
        self._GenerateWinEvtProvidersReport(storage_reader)

    finally:
      storage_reader.Close()

  def ListReports(self):
    """Lists information about the available report types."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Reports')

    for name, description in sorted(self._REPORTS.items()):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ListSections(self):
    """Lists information about the available sections."""
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, column_names=['Name', 'Description'],
        title='Sections')

    for name, description in sorted(self._SECTIONS.items()):
      table_view.AddRow([name, description])
    table_view.Write(self._output_writer)

  def ParseArguments(self, arguments):
    """Parses the command line arguments.

    Args:
      arguments (list[str]): command line arguments.

    Returns:
      bool: True if the arguments were successfully parsed.
    """
    loggers.ConfigureLogging()

    argument_parser = argparse.ArgumentParser(
        description=self.DESCRIPTION, add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    self.AddBasicOptions(argument_parser)
    self.AddStorageOptions(argument_parser)

    if self._CanEnforceProcessMemoryLimit():
      helpers_manager.ArgumentHelperManager.AddCommandLineArguments(
          argument_parser, names=['process_resources'])

    argument_parser.add_argument(
        '--compare', dest='compare_storage_file', type=str,
        action='store', default='', metavar='STORAGE_FILE', help=(
            'The path of the storage file to compare against.'))

    argument_parser.add_argument(
        '--output_format', '--output-format', dest='output_format', type=str,
        choices=self._SUPPORTED_OUTPUT_FORMATS, action='store',
        default=self._DEFAULT_OUTPUT_FORMAT, metavar='FORMAT', help=(
            'Format of the output, the default is: {0:s}. Supported options: '
            '{1:s}.').format(self._DEFAULT_OUTPUT_FORMAT, ', '.join(
                sorted(self._SUPPORTED_OUTPUT_FORMATS))))

    argument_parser.add_argument(
        '--hash', dest='hash', choices=self._HASH_CHOICES, action='store',
        metavar='TYPE', default=self._DEFAULT_HASH_TYPE, help=(
            'Type of hash to output in file_hashes report. Supported options: '
            '{0:s}').format(', '.join(self._HASH_CHOICES)))

    argument_parser.add_argument(
        '--report', dest='report', choices=self._REPORT_CHOICES, action='store',
        metavar='TYPE', default=self._DEFAULT_REPORT_TYPE, help=(
            'Report on specific information. Supported options: {0:s}'.format(
                ', '.join(self._REPORT_CHOICES))))

    argument_parser.add_argument(
        '--sections', dest='sections', type=str, action='store', default='all',
        metavar='SECTIONS_LIST', help=(
            'List of sections to output. This is a comma separated list where '
            'each entry is the name of a section. Use "--sections list" to '
            'list the available sections and "--sections all" to show all '
            'available sections.'))

    argument_parser.add_argument(
        '-v', '--verbose', dest='verbose', action='store_true',
        default=False, help='Print verbose output.')

    argument_parser.add_argument(
        '-w', '--write', metavar='OUTPUTFILE', dest='write',
        help='Output filename.')

    try:
      options = argument_parser.parse_args(arguments)
    except UnicodeEncodeError:
      # If we get here we are attempting to print help in a non-Unicode
      # terminal.
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_help())
      return False

    try:
      self.ParseOptions(options)
    except errors.BadConfigOption as exception:
      self._output_writer.Write('ERROR: {0!s}\n'.format(exception))
      self._output_writer.Write('\n')
      self._output_writer.Write(argument_parser.format_usage())
      return False

    self._WaitUserWarning()

    loggers.ConfigureLogging(
        debug_output=self._debug_mode, filename=self._log_file,
        quiet_mode=self._quiet_mode)

    return True

  def ParseOptions(self, options):
    """Parses the options.

    Args:
      options (argparse.Namespace): command line arguments.

    Raises:
      BadConfigOption: if the options are invalid.
    """
    self._ParseInformationalOptions(options)

    self._verbose = getattr(options, 'verbose', False)

    self._report_type = getattr(
        options, 'report', self._DEFAULT_REPORT_TYPE)
    self._sections = getattr(options, 'sections', '')

    self.list_reports = self._report_type == 'list'
    self.list_sections = self._sections == 'list'

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)
    if self.list_reports or self.list_sections or self.show_troubleshooting:
      return

    if self._report_type != 'none':
      if self._report_type not in self._REPORTS:
        raise errors.BadConfigOption('Unsupported report type: {0:s}.'.format(
            self._report_type))

      self.generate_report = True

    if self._sections != 'all':
      self._sections = self._sections.split(',')

    self._hash_type = getattr(options, 'hash', self._DEFAULT_HASH_TYPE)
    self._output_filename = getattr(options, 'write', None)

    helpers_manager.ArgumentHelperManager.ParseOptions(
        options, self, names=['process_resources'])

    # TODO: move check into _CheckStorageFile.
    self._storage_file_path = self.ParseStringOption(options, 'storage_file')
    if not self._storage_file_path:
      raise errors.BadConfigOption('Missing storage file option.')

    if not os.path.isfile(self._storage_file_path):
      raise errors.BadConfigOption(
          'No such storage file: {0:s}.'.format(self._storage_file_path))

    compare_storage_file_path = self.ParseStringOption(
        options, 'compare_storage_file')
    if compare_storage_file_path:
      if not os.path.isfile(compare_storage_file_path):
        raise errors.BadConfigOption(
            'No such storage file: {0:s}.'.format(compare_storage_file_path))

      self._compare_storage_file_path = compare_storage_file_path
      self.compare_storage_information = True

    self._output_format = self.ParseStringOption(options, 'output_format')

    if self._output_filename:
      if os.path.exists(self._output_filename):
        raise errors.BadConfigOption(
            'Output file already exists: {0:s}.'.format(self._output_filename))
      output_file_object = open(self._output_filename, 'wb')  # pylint: disable=consider-using-with
      self._output_writer = tools.FileObjectOutputWriter(output_file_object)

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

  def PrintStorageInformation(self):
    """Prints the storage information.

    Raises:
      BadConfigOption: if the storage file format is not supported.
    """
    if self._output_format == 'markdown':
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_MARKDOWN
    elif self._output_format == 'text':
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_CLI

    storage_reader = self._GetStorageReader(self._storage_file_path)

    try:
      self._PrintStorageInformation(storage_reader)
    finally:
      storage_reader.Close()
