"""Delimiter separated values (DSV) parser interface."""

import abc
import csv
import os

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface


class _InsufficientSampleDataError(Exception):
    """Error that is raised when the sample data contains insufficient lines."""


class DSVParser(interface.FileObjectParser):
    """Delimiter separated values (DSV) parser interface."""

    # A list that contains the names of all the fields in the log file. This needs to
    # be defined by each DSV parser.
    COLUMNS = []

    # The default delimiter is a comma, but a tab, pipe or other character are known to
    # be used. Note the delimiter must be a byte string otherwise csv module can raise
    # a TypeError indicating that "delimiter" must be a single character string.
    DELIMITER = ","

    # If there is a header before the lines start it can be defined here, and the number
    # of header lines that need to be skipped before the parsing starts.
    NUMBER_OF_HEADER_LINES = 0

    # If there is a special escape character used inside the structured text it can be
    # defined here.
    ESCAPE_CHARACTER = ""

    # If there is a special quote character used inside the structured text it can be
    # defined here.
    QUOTE_CHAR = '"'

    # The maximum size of a single field in the parser
    FIELD_SIZE_LIMIT = csv.field_size_limit()

    # Value that should not appear inside the file, made to test the actual file to see
    # if it confirms to standards.
    _MAGIC_TEST_STRING = "RegnThvotturMeistarans"

    _ENCODING = None

    # Number of lines, after the header lines, of which the line length is checked.
    _NUMBER_OF_SAMPLE_LINES = 20

    # Size of the data at the start of the file that is used to check the line length
    # before falling back to reading data of the maximum line length.
    _SAMPLE_DATA_SIZE = 65536

    def __init__(self):
        """Initializes a delimiter separated values (DSV) parser."""
        super().__init__()
        self._encoding = self._ENCODING
        self._end_of_line = "\n"
        self._maximum_line_length = len(self._end_of_line) + len(self.COLUMNS) * (
            self.FIELD_SIZE_LIMIT + len(self.DELIMITER)
        )

    def _CreateDictReader(self, line_reader):
        """Returns a reader that processes each row and yields dictionaries.

        csv.DictReader does this job well for single-character delimiters; parsers
        that need multi-character delimiters need to override this method.

        Args:
          line_reader (iter): yields lines from a file-like object.

        Returns:
          iter: a reader of dictionaries, as returned by csv.DictReader().
        """
        # Note that doublequote overrules ESCAPE_CHARACTER and needs to be set
        # to False if an escape character is used.
        if self.ESCAPE_CHARACTER:
            csv_dict_reader = csv.DictReader(
                line_reader,
                delimiter=self.DELIMITER,
                doublequote=False,
                escapechar=self.ESCAPE_CHARACTER,
                fieldnames=self.COLUMNS,
                restkey=self._MAGIC_TEST_STRING,
                restval=self._MAGIC_TEST_STRING,
            )
        else:
            csv_dict_reader = csv.DictReader(
                line_reader,
                delimiter=self.DELIMITER,
                fieldnames=self.COLUMNS,
                quotechar=self.QUOTE_CHAR,
                restkey=self._MAGIC_TEST_STRING,
                restval=self._MAGIC_TEST_STRING,
            )

        return csv_dict_reader

    def _CreateLineReader(self, file_object, encoding=None):
        """Creates an object that reads lines from a text file.

        The line reader is advanced to the beginning of the DSV content, skipping
        any header lines.

        Args:
          file_object (dfvfs.FileIO): file-like object.
          encoding (Optional[str]): encoding used in the DSV file, where None
              indicates the code page of the parser mediator should be used.

        Returns:
          TextFile: an object that implements an iterator over lines in a text file.

        Raises:
          UnicodeDecodeError: if the file cannot be read with the specified
              encoding.
        """
        line_reader = text_file.TextFile(
            file_object, encoding=encoding, end_of_line=self._end_of_line
        )
        # pylint: disable=protected-access
        maximum_read_buffer_size = line_reader._MAXIMUM_READ_BUFFER_SIZE

        # Line length is one less than the maximum read buffer size so that we tell if
        # there's a line that doesn't end at the end before the end of the file.
        if self._maximum_line_length > maximum_read_buffer_size:
            self._maximum_line_length = maximum_read_buffer_size - 1

        # If we specifically define a number of lines we should skip, do that here.
        for _ in range(0, self.NUMBER_OF_HEADER_LINES):
            line_reader.readline(self._maximum_line_length)
        return line_reader

    def _HasExpectedLineLength(self, file_object, encoding=None):
        """Determines if a file begins with lines of the expected length.

        As we know the maximum length of valid lines in the DSV file, the presence of
        lines longer than this indicates that the file will not be parsed successfully,
        without reading excessive data from a large file.

        Args:
          file_object (dfvfs.FileIO): file-like object.
          encoding (Optional[str]): encoding used in the DSV file, where None indicates
              the code page of the parser mediator should be used.

        Returns:
          bool: True if the file has lines of the expected length.
        """
        original_file_position = file_object.tell()

        result = self._HasExpectedLineLengthInSampleData(file_object, encoding)
        if result is None:
            result = True

            # Attempt to read a line that is longer than any line that should be in
            # the file.
            line_reader = self._CreateLineReader(file_object, encoding=encoding)

            for _ in range(0, self._NUMBER_OF_SAMPLE_LINES):
                sample_line = line_reader.readline(self._maximum_line_length + 1)
                if len(sample_line) > self._maximum_line_length:
                    result = False
                    break

        file_object.seek(original_file_position, os.SEEK_SET)
        return result

    def _HasExpectedLineLengthInSampleData(self, file_object, encoding):
        """Determines if the sample data begins with lines of the expected length.

        Reading data of the maximum line length, which can be several MiB, is costly
        when most files are not DSV files. This function checks the same lines as
        the line reader would, but only the complete lines in the sample data at the
        start of the file.

        Args:
          file_object (dfvfs.FileIO): file-like object.
          encoding (str): encoding used in the DSV file.

        Returns:
          bool: True if the file has lines of the expected length or None if
              the sample data does not contain enough complete lines to determine
              this.

        Raises:
          UnicodeDecodeError: if a line cannot be read with the specified encoding.
        """
        # pylint: disable=protected-access
        maximum_read_buffer_size = text_file.TextFile._MAXIMUM_READ_BUFFER_SIZE

        if self._maximum_line_length > maximum_read_buffer_size:
            self._maximum_line_length = maximum_read_buffer_size - 1

        end_of_line = self._end_of_line.encode(encoding)
        number_of_lines = self.NUMBER_OF_HEADER_LINES + self._NUMBER_OF_SAMPLE_LINES

        # The sample data size must not exceed the maximum line length so that the
        # complete lines in the sample data are the lines the line reader returns.
        sample_data_size = min(self._SAMPLE_DATA_SIZE, self._maximum_line_length)

        # The line reader also reads from the start of the file.
        file_object.seek(0, os.SEEK_SET)
        sample_data = file_object.read(sample_data_size)

        # The last value contains the remaining data, which is not a complete line.
        lines = sample_data.split(end_of_line, number_of_lines)

        # A complete line in the sample data is not longer than the maximum line
        # length, but decoding it can fail as it would in the line reader.
        for line in lines[:-1]:
            b"".join([line, end_of_line]).decode(encoding)

        if len(lines) > number_of_lines:
            return True

        return None

    def _CheckFirstRow(self, parser_mediator, row):
        """Checks if the first row is in the expected format.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          row (dict[str, str]): fields of the first row, as specified in COLUMNS.

        Raises:
          WrongParser: when the first row is not in the expected format.
        """
        number_of_columns = len(self.COLUMNS)
        number_of_records = len(row)

        if number_of_records != number_of_columns:
            display_name = parser_mediator.GetDisplayName()
            raise errors.WrongParser(
                f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s}. Wrong "
                f"number of records (expected: {number_of_columns:d}, got: "
                f"{number_of_records:d})"
            )

        for key, value in row.items():
            if self._MAGIC_TEST_STRING in (key, value):
                display_name = parser_mediator.GetDisplayName()
                raise errors.WrongParser(
                    f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s}. "
                    f"Signature mismatch."
                )

        if not self.VerifyRow(parser_mediator, row):
            display_name = parser_mediator.GetDisplayName()
            raise errors.WrongParser(
                f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s}. "
                f"Verification failed."
            )

    def _CheckFirstRowInSampleData(self, parser_mediator, file_object, encoding):
        """Checks if the first row in the sample data is in the expected format.

        The line reader reads data of up to 16 MiB to return the first row, which is
        costly when most files are not DSV files. This function checks the first row
        of the same lines as the line reader would, but only the complete lines in
        the sample data at the start of the file. If the first row cannot be
        determined from these lines, the check is left to the line reader.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.
          encoding (str): encoding used in the DSV file.

        Raises:
          WrongParser: when the first row is not in the expected format.
        """
        # The sample data size must not exceed the maximum line length so that the
        # complete lines in the sample data are the lines the line reader returns.
        sample_data_size = min(self._SAMPLE_DATA_SIZE, self._maximum_line_length)

        original_file_position = file_object.tell()

        # The line reader also reads from the start of the file.
        file_object.seek(0, os.SEEK_SET)
        sample_data = file_object.read(sample_data_size)

        file_object.seek(original_file_position, os.SEEK_SET)

        sample_line_reader = self._ReadCompleteLinesInSampleData(sample_data, encoding)

        try:
            for _ in range(0, self.NUMBER_OF_HEADER_LINES):
                next(sample_line_reader)

            reader = self._CreateDictReader(sample_line_reader)
            row = next(reader)

        except _InsufficientSampleDataError:
            return

        except (StopIteration, UnicodeDecodeError, csv.Error) as exception:
            display_name = parser_mediator.GetDisplayName()
            raise errors.WrongParser(
                f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s} with "
                f"error: {exception!s}."
            )

        self._CheckFirstRow(parser_mediator, row)

    def _ReadCompleteLinesInSampleData(self, sample_data, encoding):
        """Reads the complete lines in the sample data.

        The lines are decoded and returned in the same way as by the line reader.

        Args:
          sample_data (bytes): sample data at the start of the file.
          encoding (str): encoding used in the DSV file.

        Yields:
          str: line of text, including the end-of-line.

        Raises:
          UnicodeDecodeError: if a line cannot be read with the specified encoding.
          _InsufficientSampleDataError: if all complete lines in the sample data
              have been read.
        """
        end_of_line = self._end_of_line.encode(encoding)

        # The last value contains the remaining data, which is not a complete line.
        lines = sample_data.split(end_of_line)

        for index, line in enumerate(lines[:-1]):
            decoded_line = b"".join([line, end_of_line]).decode(encoding)

            # Remove a byte-order mark at the start of the file.
            if index == 0 and decoded_line[0] == "\ufeff":
                decoded_line = decoded_line[1:]

            yield decoded_line

        # Note that ending the iteration here would cause the csv module to return
        # an incomplete row, which can differ from the row the line reader returns.
        raise _InsufficientSampleDataError()

    def _CheckForByteOrderMark(self, file_object):
        """Check if the file contains a byte-order-mark (BOM).

        Also see:
        https://en.wikipedia.org/wiki/Byte_order_mark#Byte_order_marks_by_encoding

        Args:
          file_object (dfvfs.FileIO): file-like object.

        Returns:
          tuple: containing:

            str: encoding determined based on BOM or None if no BOM was found.
            int: offset of the text after the BOM of 0 if no BOM was found.
        """
        file_object.seek(0, os.SEEK_SET)
        file_data = file_object.read(4)

        # Look the for a match with the longest byte-order-mark first.
        if file_data[0:4] == b"\x00\x00\xfe\xff":
            return "utf-32-be", 4

        if file_data[0:4] == b"\xff\xfe\x00\x00":
            return "utf-32-le", 4

        if file_data[0:3] == b"\xef\xbb\xbf":
            return "utf-8", 3

        if file_data[0:2] == b"\xfe\xff":
            return "utf-16-be", 2

        if file_data[0:2] == b"\xff\xfe":
            return "utf-16-le", 2

        return None, 0

    def _GetRowValue(self, row, value_name):
        """Retrieves a row value.

        Args:
          row (): row.
          value_name (str): name of the value to retrieve.

        Returns:
          str: value or None if empty.
        """
        return row.get(value_name) or None

    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification.

        Returns:
          FormatSpecification: format specification.
        """
        return specification.FormatSpecification(cls.NAME, text_format=True)

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a DSV text file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        encoding, text_offset = self._CheckForByteOrderMark(file_object)

        if encoding and self._encoding and encoding != self._encoding:
            display_name = parser_mediator.GetDisplayName()
            raise errors.WrongParser(
                f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s} encoding "
                f"does not match the one required by the parser."
            )

        encoding = self._encoding
        if not encoding:
            encoding = parser_mediator.GetCodePage()

        file_object.seek(text_offset, os.SEEK_SET)

        try:
            if not self._HasExpectedLineLength(file_object, encoding=encoding):
                display_name = parser_mediator.GetDisplayName()
                raise errors.WrongParser(
                    f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s} with "
                    f"error: unexpected line length."
                )

        except UnicodeDecodeError as exception:
            display_name = parser_mediator.GetDisplayName()
            raise errors.WrongParser(
                f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s} with "
                f"error: {exception!s}."
            )

        self._CheckFirstRowInSampleData(parser_mediator, file_object, encoding)

        try:
            line_reader = self._CreateLineReader(file_object, encoding=encoding)
            reader = self._CreateDictReader(line_reader)
            row_offset = line_reader.tell()
            row = next(reader)
        except (StopIteration, UnicodeDecodeError, csv.Error) as exception:
            display_name = parser_mediator.GetDisplayName()
            raise errors.WrongParser(
                f"[{self.NAME:s}] Unable to parse DSV file: {display_name:s} with "
                f"error: {exception!s}."
            )

        self._CheckFirstRow(parser_mediator, row)

        self.ParseRow(parser_mediator, row_offset, row)
        row_offset = line_reader.tell()
        line_number = 2

        while row:
            if parser_mediator.abort:
                break

            # next() is used here to be able to handle lines that the Python csv module
            # fails to parse.
            try:
                row = next(reader)

                self.ParseRow(parser_mediator, row_offset, row)
                row_offset = line_reader.tell()

            except StopIteration:
                break

            except csv.Error as exception:
                parser_mediator.ProduceWarning(
                    f"unable to parse line: {line_number:d} with error: {exception!s}"
                )
                break

    @abc.abstractmethod
    def ParseRow(self, parser_mediator, row_offset, row):
        """Parses a line of the log file and produces events.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          row_offset (int): offset of the line from which the row was extracted.
          row (dict[str, str]): fields of a single row, as specified in COLUMNS.
        """

    # pylint: disable=redundant-returns-doc
    @abc.abstractmethod
    def VerifyRow(self, parser_mediator, row):
        """Verifies if a line of the file is in the expected format.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          row (dict[str, str]): fields of a single row, as specified in COLUMNS.

        Returns:
          bool: True if this is the correct parser, False otherwise.
        """
