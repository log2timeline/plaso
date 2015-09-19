# -*- coding: utf-8 -*-
"""The CLI view classes."""


class CLITableView(object):
  """Class that implements a 2 column command line table view."""

  # The maximum width of the table in number of characters.
  _MAXIMUM_WIDTH = 80

  _HEADER_FORMAT_STRING = u'{{0:*^{0:d}}}\n'.format(_MAXIMUM_WIDTH)

  def __init__(self, output_writer, column_width=25):
    """Initializes the command line table view object.

    Args:
      output_writer: the output writer (instance of OutputWriter).
                     The default is None which indicates the use of the stdout
                     output writer.
      column_width: optional column width, which cannot be smaller than 0 or
                    larger than the maximum width.

    Raises:
      ValueError: if the column width is out of bounds.
    """
    if column_width < 0 or column_width > self._MAXIMUM_WIDTH:
      raise ValueError(u'Column width value out of bounds.')

    super(CLITableView, self).__init__()
    self._column_width = column_width
    self._output_writer = output_writer

  def PrintFooter(self):
    """Prints the footer."""
    self._output_writer.Write(u'-' * self._MAXIMUM_WIDTH)
    self._output_writer.Write(u'\n')

  def PrintHeader(self, text):
    """Prints the header as a line with centered text.

    Args:
      text: The header text.
    """
    self._output_writer.Write(u'\n')

    text = u' {0:s} '.format(text)
    header_string = self._HEADER_FORMAT_STRING.format(text)
    self._output_writer.Write(header_string)

  def PrintRow(self, first_column, second_column):
    """Prints a row of 2 column values aligned to the column width.

    Args:
      first_column: the first column value.
      second_column: the second column value.
    """
    maximum_row_width = self._MAXIMUM_WIDTH - self._column_width - 3

    # The format string of the first line of the column value.
    primary_format_string = u'{{0:>{0:d}s}} : {{1:s}}\n'.format(
        self._column_width)

    # The format string of successive lines of the column value.
    secondary_format_string = u'{{0:<{0:d}s}}{{1:s}}\n'.format(
        self._column_width + 3)

    if len(second_column) < maximum_row_width:
      self._output_writer.Write(primary_format_string.format(
          first_column, second_column))
      return

    # Split the column value in words.
    words = second_column.split()

    current = 0

    lines = []
    word_buffer = []
    for word in words:
      current += len(word) + 1
      if current >= maximum_row_width:
        current = len(word)
        lines.append(u' '.join(word_buffer))
        word_buffer = [word]
      else:
        word_buffer.append(word)
    lines.append(u' '.join(word_buffer))

    # Print the column value on multiple lines.
    self._output_writer.Write(primary_format_string.format(
        first_column, lines[0]))
    for line in lines[1:]:
      self._output_writer.Write(secondary_format_string.format(u'', line))
