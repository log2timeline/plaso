# -*- coding: utf-8 -*-
"""Interface for the CSV (Comma Separated Values) file parser plugins."""

import csv

from plaso.parsers import plugins

class CSVPlugin(plugins.BasePlugin):
  """CSV (Comma Separated Values) file parser plugin."""  

  NAME = 'csv_plugin'
  DATA_FORMAT = 'CSV (Comma Separated Values) file'

  # ENCODING -> encoding of file, default is utf-8
  ENCODING = "utf-8"

  # CSV_FIELDNAMES = None -> values in the first row of file will be
  # used as the fieldnames
  CSV_FIELDNAMES = None

  # CSV_DIALECT = 'excel' -> class defines the usual properties
  # of an Excel-generated CSV file
  # More details at documentation:
  # http://docs.python.org/3/library/csv.html#dialects-and-formatting-parameters
  CSV_DIALECT = csv.excel

  # This constant is used for checking columns at CSV.
  REQUESTED_COLUMNS = {}

  # This constant is used for checking if they are some keywords at CSV.
  REQUESTED_CONTENT = {}

  def _ParseCsvRow(self, parser_mediator, row):
    """Extracts events from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      row (dict[str]): row from CSV file.
    """

  def CheckRequiredColumns(self, headers):
    """Check if CSV file has the minimal columns required by the plugin.

    Args:
      headers (list[str]): headers of CSV file.

    Returns:
      bool: True if CSV file has the required columns defined by
          the plugin, or False if it does not or if the plugin does not define
          required columns. The CSV file can have more columns than 
          specified by the plugin and still return True.
    """
    if not self.REQUESTED_COLUMNS or self.REQUESTED_COLUMNS is None:
      return False

    if not headers or headers is None:
      return False

    search = [item.lower().strip() for item in self.REQUESTED_COLUMNS]
    data = [item.lower().strip() for item in headers]

    # All of them
    return 0 not in [c in data for c in search]

  def CheckRequiredContent(self, reader):
    """Check if CSV file has the minimal content required by the plugin.

    Args:
      reader (csv.DictReader): content of CSV file.

    Returns:
      bool: True if CSV file has the required content defined by
          the plugin, or False if it does not or if the plugin does not define
          required content. The CSV file can have more content than 
          specified by the plugin and still return True.
    """
    if not self.REQUESTED_CONTENT:
      return False

    if not isinstance(reader, csv.DictReader):
      return False

    has_requested_content = 0
    search = [item.lower().strip() for item in self.REQUESTED_CONTENT]

    for row in reader:
      data = [item.lower().strip() for item in row.values()]
       # At least one of them
      has_requested_content = 1 in [c in data for c in search]
      if has_requested_content:
        break

    return has_requested_content

  # pylint: disable=arguments-differ
  def Process(self, parser_mediator, reader=None, **unused_kwargs):
    """Extracts events from a CSV (Comma Separated Values) file.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      reader (Optional[csv.DictReader]): CSV file.

    Raises:
      ValueError: If the csv_file is missing.
    """
    if reader is None:
      raise ValueError('Missing reader value.')

    if not isinstance(reader, csv.DictReader):
      raise ValueError('Given argument is wrong type.')

    # This will raise if unhandled keyword arguments are passed.
    super(CSVPlugin, self).Process(parser_mediator)

    try:
      for row in reader:
        self._ParseCsvRow(parser_mediator, row)

    except (csv.Error) as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse file with error: {0!s}'.format(exception))
      return
