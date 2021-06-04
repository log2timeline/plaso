# -*- coding: utf-8 -*-
"""The pinfo CLI tool."""

import argparse
import collections
import json
import os
import re
import uuid

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.cli import logger
from plaso.cli import tool_options
from plaso.cli import tools
from plaso.cli import views
from plaso.cli.helpers import manager as helpers_manager
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import loggers
from plaso.serializer import json_serializer
from plaso.storage import factory as storage_factory


class PinfoTool(tools.CLITool, tool_options.StorageFileOptions):
  """Pinfo CLI tool.

  Attributes:
    compare_storage_information (bool): True if the tool is used to compare
        stores.
    list_sections (bool): True if the sections should be listed.
  """

  NAME = 'pinfo'
  DESCRIPTION = (
      'Shows information about a Plaso storage file, for example how it was '
      'collected, what information was extracted from a source, etc.')

  _SECTIONS = {
      'events': 'Show information about events.',
      'reports': 'Show information about analysis reports.',
      'sessions': 'Show information about sessions.',
      'sources': 'Show information about event sources.',
      'warnings': 'Show information about warnings during processing.'}

  _DEFAULT_OUTPUT_FORMAT = 'text'
  _SUPPORTED_OUTPUT_FORMATS = ['json', 'markdown', 'text']

  _UNICODE_SURROGATES_RE = re.compile('[\ud800-\udfff]')

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
    self._output_format = None
    self._process_memory_limit = None
    self._sections = None
    self._storage_file_path = None
    self._verbose = False

    self.compare_storage_information = False
    self.list_sections = False

  def _CalculateStorageCounters(self, storage_reader):
    """Calculates the counters of the entire storage.

    Args:
      storage_reader (StorageReader): storage reader.

    Returns:
      dict[str, collections.Counter]: storage counters.
    """
    analysis_reports_counter = collections.Counter()
    analysis_reports_counter_error = False
    event_labels_counter = collections.Counter()
    event_labels_counter_error = False
    parsers_counter = collections.Counter()
    parsers_counter_error = False

    for session in storage_reader.GetSessions():
      if isinstance(session.analysis_reports_counter, collections.Counter):
        analysis_reports_counter += session.analysis_reports_counter
      else:
        analysis_reports_counter_error = True

      if isinstance(session.event_labels_counter, collections.Counter):
        event_labels_counter += session.event_labels_counter
      else:
        event_labels_counter_error = True

      if isinstance(session.parsers_counter, collections.Counter):
        parsers_counter += session.parsers_counter
      else:
        parsers_counter_error = True

    storage_counters = {}

    extraction_warnings_by_path_spec = collections.Counter()
    extraction_warnings_by_parser_chain = collections.Counter()

    if storage_reader.HasExtractionWarnings():
      for warning in list(storage_reader.GetExtractionWarnings()):
        path_spec_string = self._GetPathSpecificationString(warning.path_spec)

        extraction_warnings_by_path_spec[path_spec_string] += 1
        extraction_warnings_by_parser_chain[warning.parser_chain] += 1

    storage_counters['extraction_warnings_by_path_spec'] = (
        extraction_warnings_by_path_spec)
    storage_counters['extraction_warnings_by_parser_chain'] = (
        extraction_warnings_by_parser_chain)

    # TODO: kept for backwards compatibility.
    storage_counters['warnings_by_path_spec'] = extraction_warnings_by_path_spec
    storage_counters['warnings_by_parser_chain'] = (
        extraction_warnings_by_parser_chain)

    recovery_warnings_by_path_spec = collections.Counter()
    recovery_warnings_by_parser_chain = collections.Counter()

    if storage_reader.HasRecoveryWarnings():
      for warning in list(storage_reader.GetRecoveryWarnings()):
        path_spec_string = self._GetPathSpecificationString(warning.path_spec)

        recovery_warnings_by_path_spec[path_spec_string] += 1
        recovery_warnings_by_parser_chain[warning.parser_chain] += 1

    storage_counters['recovery_warnings_by_path_spec'] = (
        recovery_warnings_by_path_spec)
    storage_counters['recovery_warnings_by_parser_chain'] = (
        recovery_warnings_by_parser_chain)

    if not analysis_reports_counter_error:
      storage_counters['analysis_reports'] = analysis_reports_counter

    if not event_labels_counter_error:
      storage_counters['event_labels'] = event_labels_counter

    if not parsers_counter_error:
      storage_counters['parsers'] = parsers_counter

    return storage_counters

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

  def _GetPathSpecificationString(self, path_spec):
    """Retrieves a printable string representation of the path specification.

    Args:
      path_spec (dfvfs.PathSpec): path specification.

    Returns:
      str: printable string representation of the path specification.
    """
    path_spec_string = path_spec.comparable

    if self._UNICODE_SURROGATES_RE.search(path_spec_string):
      path_spec_string = path_spec_string.encode(
          'utf-8', errors='surrogateescape')
      path_spec_string = path_spec_string.decode(
          'utf-8', errors='backslashreplace')

    return path_spec_string

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
          ', "analysis_reports": {0:s}'.format(json_string))

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
    if (self._output_format == 'text' and
        not storage_reader.HasAnalysisReports()):
      self._output_writer.Write('\nNo analysis reports stored.\n')

    else:
      for index, analysis_report in enumerate(
          storage_reader.GetAnalysisReports()):
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

  def _PrintExtractionWarningsDetails(self, storage_reader):
    """Prints the details of the extraction warnings.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    for index, warning in enumerate(storage_reader.GetExtractionWarnings()):
      title = 'Extraction warning: {0:d}'.format(index)
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
      self._output_writer.Write(', "event_labels": {0:s}'.format(json_string))

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
    for index, warning in enumerate(storage_reader.GetPreprocessingWarnings()):
      title = 'Preprocessing warning: {0:d}'.format(index)
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

  def _PrintRecoveryWarningsDetails(self, storage_reader):
    """Prints the details of the recovery warnings.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    for index, warning in enumerate(storage_reader.GetRecoveryWarnings()):
      title = 'Recovery warning: {0:d}'.format(index)
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
        if session.source_configurations:
          self._PrintSourceConfigurations(
              session.source_configurations,
              session_identifier=session_identifier)

        self._PrintParsersCounter(
            session.parsers_counter, session_identifier=session_identifier)

        self._PrintAnalysisReportCounter(
            session.analysis_reports_counter,
            session_identifier=session_identifier)

        self._PrintEventLabelsCounter(
            session.event_labels_counter,
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

  def _PrintSourceConfiguration(
      self, source_configuration, session_identifier=None):
    """Prints the details of a source configuration.

    Args:
      source_configuration (SourceConfiguration): source configuration.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    system_configuration = source_configuration.system_configuration
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
    code_page = system_configuration.code_page or 'N/A'
    keyboard_layout = system_configuration.keyboard_layout or 'N/A'
    time_zone = system_configuration.time_zone or 'N/A'

    table_view.AddRow(['Hostname', hostname])
    table_view.AddRow(['Operating system', operating_system])
    table_view.AddRow(['Operating system product', operating_system_product])
    table_view.AddRow(['Operating system version', operating_system_version])
    table_view.AddRow(['Code page', code_page])
    table_view.AddRow(['Keyboard layout', keyboard_layout])
    table_view.AddRow(['Time zone', time_zone])

    table_view.Write(self._output_writer)

    title = 'Available time zones'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Name', ''], title=title)

    for time_zone in system_configuration.available_time_zones:
      table_view.AddRow([time_zone.name, ''])

    table_view.Write(self._output_writer)

    title = 'User accounts'
    if session_identifier:
      title = '{0:s}: {1:s}'.format(title, session_identifier)

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type,
        column_names=['Username', 'User directory'], title=title)

    for user_account in system_configuration.user_accounts:
      table_view.AddRow([
          user_account.username, user_account.user_directory])

    table_view.Write(self._output_writer)

  def _PrintSourceConfigurations(
      self, source_configurations, session_identifier=None):
    """Prints the details of source configurations.

    Args:
      source_configurations (list[SourceConfiguration]): source configurations.
      session_identifier (Optional[str]): session identifier, formatted as
          a UUID.
    """
    if self._output_format == 'json':
      self._output_writer.Write(', "system_configurations": {')

    for configuration_index, configuration in enumerate(source_configurations):
      if self._output_format == 'json':
        if configuration_index != 0:
          self._output_writer.Write(', ')

        json_string = (
            json_serializer.JSONAttributeContainerSerializer.WriteSerialized(
                configuration.system_configuration))
        self._output_writer.Write(
            '"system_configuration": {0:s}'.format(json_string))

      elif self._output_format in ('markdown', 'text'):
        self._PrintSourceConfiguration(
            configuration, session_identifier=session_identifier)

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

    storage_type = storage_reader.GetStorageType()
    if storage_type == definitions.STORAGE_TYPE_SESSION:
      if self._sections == 'all' or 'sessions' in self._sections:
        self._PrintSessionsSection(storage_reader)

      if self._sections == 'all' or 'sources' in self._sections:
        self._PrintSourcesOverview(storage_reader)

      storage_counters = self._CalculateStorageCounters(storage_reader)

      if self._output_format == 'json':
        self._output_writer.Write(', "storage_counters": {')

      if self._sections == 'all' or 'events' in self._sections:
        parsers = storage_counters.get('parsers', collections.Counter())

        self._PrintParsersCounter(parsers)

        event_labels = storage_counters.get(
            'event_labels', collections.Counter())

        self._PrintEventLabelsCounter(event_labels)

      if self._sections == 'all' or 'warnings' in self._sections:
        self._PrintWarningsSection(storage_reader, storage_counters)

      if self._sections == 'all' or 'reports' in self._sections:
        analysis_reports = storage_counters.get(
            'analysis_reports', collections.Counter())

        self._PrintAnalysisReportSection(storage_reader, analysis_reports)

      if self._output_format == 'json':
        self._output_writer.Write('}')

    elif storage_type == definitions.STORAGE_TYPE_TASK:
      self._PrintTasksInformation(storage_reader)

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
      self._output_writer.Write(', "event_sources": {')

    elif self._output_format in ('markdown', 'text'):
      table_view = views.ViewsFactory.GetTableView(
          self._views_format_type, title='Event sources', title_level=2)

    number_of_event_sources = 0
    for source_index, source in enumerate(storage_reader.GetEventSources()):
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
    storage_type = storage_reader.GetStorageType()

    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Plaso Storage Information',
        title_level=1)
    table_view.AddRow(['Filename', os.path.basename(self._storage_file_path)])
    table_view.AddRow(['Format version', format_version])
    table_view.AddRow(['Storage type', storage_type])
    table_view.AddRow(['Serialization format', serialization_format])
    table_view.Write(self._output_writer)

  def _PrintTasksInformation(self, storage_reader):
    """Prints information about the tasks.

    Args:
      storage_reader (StorageReader): storage reader.
    """
    table_view = views.ViewsFactory.GetTableView(
        self._views_format_type, title='Tasks')

    for task_start, _ in storage_reader.GetSessions():
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=task_start.timestamp)
      start_time = date_time.CopyToDateTimeStringISO8601()

      task_identifier = uuid.UUID(hex=task_start.identifier)
      task_identifier = '{0!s}'.format(task_identifier)
      table_view.AddRow([task_identifier, start_time])

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
        ', "warnings_by_parser": {0:s}'.format(json_string))

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
    if (self._output_format == 'text' and
        not storage_reader.HasExtractionWarnings() and
        not storage_reader.HasPreprocessingWarnings() and
        not storage_reader.HasRecoveryWarnings()):
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
          self._PrintExtractionWarningsDetails(storage_reader)

      warnings_by_path_spec = storage_counters.get(
          'recovery_warnings_by_path_spec', collections.Counter())
      warnings_by_parser_chain = storage_counters.get(
          'recovery_warnings_by_parser_chain', collections.Counter())

      # TODO: print preprocessing warnings as part of JSON output format.

      if self._output_format in ('markdown', 'text'):
        self._PrintWarningCountersTable(
            'preprocessing', warnings_by_path_spec, warnings_by_parser_chain)

        if self._verbose or 'warnings' in self._sections:
          self._PrintPreprocessingWarningsDetails(storage_reader)

      # TODO: print recovery warnings as part of JSON output format.

      if self._output_format in ('markdown', 'text'):
        self._PrintWarningCountersTable(
            'recovery', warnings_by_path_spec, warnings_by_parser_chain)

        if self._verbose or 'warnings' in self._sections:
          self._PrintRecoveryWarningsDetails(storage_reader)

  def CompareStores(self):
    """Compares the contents of two stores.

    Returns:
      bool: True if the content of the stores is identical.
    """
    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    if not storage_reader:
      logger.error(
          'Format of storage file: {0:s} not supported'.format(
              self._storage_file_path))
      return False

    compare_storage_reader = (
        storage_factory.StorageFactory.CreateStorageReaderForFile(
            self._compare_storage_file_path))
    if not compare_storage_reader:
      logger.error(
          'Format of storage file: {0:s} not supported'.format(
              self._compare_storage_file_path))
      return False

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

    self._sections = getattr(options, 'sections', '')

    self.list_sections = self._sections == 'list'

    self.show_troubleshooting = getattr(options, 'show_troubleshooting', False)
    if self.list_sections or self.show_troubleshooting:
      return

    if self._sections != 'all':
      self._sections = self._sections.split(',')

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
      output_file_object = open(self._output_filename, 'wb')
      self._output_writer = tools.FileObjectOutputWriter(output_file_object)

    self._EnforceProcessMemoryLimit(self._process_memory_limit)

  def PrintStorageInformation(self):
    """Prints the storage information."""
    storage_reader = storage_factory.StorageFactory.CreateStorageReaderForFile(
        self._storage_file_path)
    if not storage_reader:
      logger.error('Format of storage file: {0:s} not supported'.format(
          self._storage_file_path))
      return

    if self._output_format in 'markdown':
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_MARKDOWN
    elif self._output_format in 'text':
      self._views_format_type = views.ViewsFactory.FORMAT_TYPE_CLI

    try:
      self._PrintStorageInformation(storage_reader)
    finally:
      storage_reader.Close()
