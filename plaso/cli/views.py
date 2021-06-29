# -*- coding: utf-8 -*-
"""View classes."""

import abc

try:
  import win32console
except ImportError:
  win32console = None


class BaseTableView(object):
  """Table view interface."""

  def __init__(self, column_names=None, title=None, title_level=3):
    """Initializes a table view.

    Args:
      column_names (Optional[list[str]]): column names.
      title (Optional[str]): title.
      title_level (Optional[int]): title heading level.
    """
    super(BaseTableView, self).__init__()
    self._columns = column_names or []
    self._number_of_columns = len(self._columns)
    self._rows = []
    self._title = title
    self._title_level = title_level

  def AddRow(self, values):
    """Adds a row of values.

    Args:
      values (list[object]): values.

    Raises:
      ValueError: if the number of values is out of bounds.
    """
    if self._number_of_columns and len(values) != self._number_of_columns:
      raise ValueError('Number of values is out of bounds.')

    self._rows.append(values)

    if not self._number_of_columns:
      self._number_of_columns = len(values)

  @abc.abstractmethod
  def Write(self, output_writer):
    """Writes the table to the output writer.

    Args:
      output_writer (OutputWriter): output writer.
    """


class CLITableView(BaseTableView):
  """Command line table view.

  Note that currently this table view does not support more than 2 columns.
  """

  # The maximum width of the table in number of characters.
  # The standard width of Windows cmd.exe is 80 characters.
  _MAXIMUM_WIDTH = 80

  _HEADER_FORMAT_STRING = '{{0:*^{0:d}}}\n'.format(_MAXIMUM_WIDTH)

  def __init__(self, column_names=None, title=None, title_level=3):
    """Initializes a command line table view.

    Args:
      column_names (Optional[list[str]]): column names.
      title (Optional[str]): title.
      title_level (Optional[int]): title heading level.
    """
    super(CLITableView, self).__init__(
        column_names=column_names, title=title, title_level=title_level)
    if self._columns:
      self._column_width = len(self._columns[0])
    else:
      self._column_width = 0

  def _WriteHeader(self, output_writer):
    """Writes a header.

    Args:
      output_writer (OutputWriter): output writer.
    """
    header_string = ''
    if self._title:
      header_string = ' {0:s} '.format(self._title)

    header_string = self._HEADER_FORMAT_STRING.format(header_string)
    output_writer.Write(header_string)

  def _WriteRow(self, output_writer, values):
    """Writes a row of values aligned to the column width.

    Args:
      output_writer (OutputWriter): output writer.
      values (list[object]): values.
    """
    maximum_row_width = self._MAXIMUM_WIDTH - self._column_width - 3

    # The format string of the first line of the column value.
    primary_format_string = '{{0:>{0:d}s}} : {{1:s}}\n'.format(
        self._column_width)

    # The format string of successive lines of the column value.
    secondary_format_string = '{{0:<{0:d}s}}{{1:s}}\n'.format(
        self._column_width + 3)

    if isinstance(values[1], str):
      value_string = values[1]
    else:
      value_string = '{0!s}'.format(values[1])

    if len(value_string) < maximum_row_width:
      output_writer.Write(primary_format_string.format(
          values[0], value_string))
      return

    # Split the column value in words.
    words = value_string.split()

    current = 0

    lines = []
    word_buffer = []
    for word in words:
      current += len(word) + 1
      if current >= maximum_row_width:
        current = len(word)
        lines.append(' '.join(word_buffer))
        word_buffer = [word]
      else:
        word_buffer.append(word)
    lines.append(' '.join(word_buffer))

    # Split the column value across multiple lines.
    output_writer.Write(
        primary_format_string.format(values[0], lines[0]))
    for line in lines[1:]:
      output_writer.Write(secondary_format_string.format('', line))

  def _WriteSeparatorLine(self, output_writer):
    """Writes a separator line.

    Args:
      output_writer (OutputWriter): output writer.
    """
    output_writer.Write('-' * self._MAXIMUM_WIDTH)
    output_writer.Write('\n')

  def AddRow(self, values):
    """Adds a row of values.

    Args:
      values (list[object]): values.

    Raises:
      ValueError: if the number of values is out of bounds.
    """
    super(CLITableView, self).AddRow(values)

    value_length = len(values[0])
    if value_length > self._column_width:
      self._column_width = value_length

  def Write(self, output_writer):
    """Writes the table to the output writer.

    Args:
      output_writer (OutputWriter): output writer.

    Raises:
      RuntimeError: if the title exceeds the maximum width or
          if the table has more than 2 columns or
          if the column width is out of bounds.
    """
    if self._title and len(self._title) > self._MAXIMUM_WIDTH:
      raise RuntimeError('Title length out of bounds.')

    if self._number_of_columns not in (0, 2):
      raise RuntimeError('Unsupported number of columns: {0:d}.'.format(
          self._number_of_columns))

    if self._column_width < 0 or self._column_width >= self._MAXIMUM_WIDTH:
      raise RuntimeError('Column width out of bounds.')

    output_writer.Write('\n')

    self._WriteHeader(output_writer)

    if self._columns:
      self._WriteRow(output_writer, self._columns)
      self._WriteSeparatorLine(output_writer)

    for values in self._rows:
      self._WriteRow(output_writer, values)

    self._WriteSeparatorLine(output_writer)


class CLITabularTableView(BaseTableView):
  """Command line tabular table view interface."""

  _NUMBER_OF_SPACES_IN_TAB = 8

  def __init__(self, column_names=None, column_sizes=None, title=None):
    """Initializes a command line table view.

    Args:
      column_names (Optional[list[str]]): column names.
      column_sizes (Optional[list[int]]): minimum column sizes, in number of
          characters. If a column name or row value is larger than the
          minimum column size the column will be enlarged. Note that the
          minimum columns size will be rounded up to the number of spaces
          of the next tab.
      title (Optional[str]): title.
    """
    super(CLITabularTableView, self).__init__(
        column_names=column_names, title=title)
    self._column_sizes = column_sizes or []

  def _WriteRow(self, output_writer, values, in_bold=False):
    """Writes a row of values aligned to the column width.

    Args:
      output_writer (OutputWriter): output writer.
      values (list[object]): values.
      in_bold (Optional[bool]): True if the row should be written in bold.
    """
    row_strings = []
    if self._column_sizes:
      for value_index, value_string in enumerate(values):
        padding_size = self._column_sizes[value_index] - len(value_string)
        padding_string = ' ' * padding_size

        row_strings.extend([value_string, padding_string])

      row_strings.pop()

    row_strings = ''.join(row_strings)

    if in_bold and not win32console:
      # TODO: for win32console get current color and set intensity,
      # write the header separately then reset intensity.
      row_strings = '\x1b[1m{0:s}\x1b[0m'.format(row_strings)

    row_strings = '{0:s}\n'.format(row_strings)
    output_writer.Write(row_strings)

  def AddRow(self, values):
    """Adds a row of values.

    Args:
      values (list[object]): values.

    Raises:
      ValueError: if the number of values is out of bounds.
    """
    if self._number_of_columns and len(values) != self._number_of_columns:
      raise ValueError('Number of values is out of bounds.')

    if not self._column_sizes and self._columns:
      self._column_sizes = [len(column) for column in self._columns]

    value_strings = []
    for value_index, value_string in enumerate(values):
      if not isinstance(value_string, str):
        value_string = '{0!s}'.format(value_string)
      value_strings.append(value_string)

      self._column_sizes[value_index] = max(
          self._column_sizes[value_index], len(value_string))

    self._rows.append(value_strings)

    if not self._number_of_columns:
      self._number_of_columns = len(value_strings)

  def Write(self, output_writer):
    """Writes the table to the output writer.

    Args:
      output_writer (OutputWriter): output writer.
    """
    # Round up the column sizes to the nearest tab.
    for column_index, column_size in enumerate(self._column_sizes):
      column_size, _ = divmod(column_size, self._NUMBER_OF_SPACES_IN_TAB)
      column_size = (column_size + 1) * self._NUMBER_OF_SPACES_IN_TAB
      self._column_sizes[column_index] = column_size

    # TODO: write title.

    if self._columns:
      self._WriteRow(output_writer, self._columns, in_bold=True)

    for values in self._rows:
      self._WriteRow(output_writer, values)


class MarkdownTableView(BaseTableView):
  """Markdown table view."""

  def _WriteHeader(self, output_writer):
    """Writes a header.

    Args:
      output_writer (OutputWriter): output writer.
    """
    if self._title:
      output_writer.Write('{0:s} {1:s}\n\n'.format(
          '#' * self._title_level, self._title))

    if self._columns:
      output_writer.Write(' | '.join(self._columns))
      output_writer.Write('\n')

      output_writer.Write(' | '.join(['---' for _ in self._columns]))
      output_writer.Write('\n')
    else:
      output_writer.Write('<table>\n')

  def _WriteRow(self, output_writer, values):
    """Writes a row of values aligned to the column width.

    Args:
      output_writer (OutputWriter): output writer.
      values (list[object]): values.
    """
    if self._columns:
      row_values = ['{0!s}'.format(value) for value in values]
      output_writer.Write(' | '.join(row_values))
      output_writer.Write('\n')
    else:
      row_values = ''.join([
         '<td>{0!s}</td>'.format(value) for value in values[1:]])
      output_writer.Write((
          '<tr><th nowrap style="text-align:left;vertical-align:top">{0!s}</th>'
          '{1:s}</tr>\n').format(values[0], row_values))

  def Write(self, output_writer):
    """Writes the table to the output writer.

    Args:
      output_writer (OutputWriter): output writer.
    """
    self._WriteHeader(output_writer)

    for values in self._rows:
      self._WriteRow(output_writer, values)

    if not self._columns:
      output_writer.Write('</table>\n')

    output_writer.Write('\n')


class ViewsFactory(object):
  """Views factory."""

  FORMAT_TYPE_CLI = 'cli'
  FORMAT_TYPE_MARKDOWN = 'markdown'

  _TABLE_VIEW_FORMAT_CLASSES = {
      FORMAT_TYPE_CLI: CLITableView,
      FORMAT_TYPE_MARKDOWN: MarkdownTableView
  }

  @classmethod
  def GetTableView(
      cls, format_type, column_names=None, title=None, title_level=3):
    """Retrieves a table view.

    Args:
      format_type (str): table view format type.
      column_names (Optional[list[str]]): column names.
      title (Optional[str]): title.
      title_level (Optional[int]): title heading level.

    Returns:
      BaseTableView: table view.

    Raises:
      ValueError: if the format type is not supported.
    """
    view_class = cls._TABLE_VIEW_FORMAT_CLASSES.get(format_type, None)
    if not view_class:
      raise ValueError('Unsupported format type: {0:s}'.format(format_type))

    return view_class(
        column_names=column_names, title=title, title_level=title_level)
