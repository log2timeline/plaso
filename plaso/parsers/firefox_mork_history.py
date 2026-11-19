"""Parser for Mozilla Firefox 1 and 2 history (history.dat) Mork files."""

import re

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class FirefoxMorkHistoryEventData(events.EventData):
    """Firefox Mork history entry event data.

    Attributes:
      first_visited_time (dfdatetime.DateTimeValues): date and time the URL was
          first visited.
      hidden (bool): True if the URL is hidden from the history.
      hostname (str): name of the visited host or domain.
      last_visited_time (dfdatetime.DateTimeValues): date and time the URL was
          last visited.
      referrer (str): URL of the referring page.
      title (str): title of the visited page.
      typed (bool): True if the URL was typed in.
      url (str): visited URL.
      visit_count (int): number of times the URL was visited.
    """

    DATA_TYPE = "firefox:mork:history_entry"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.first_visited_time = None
        self.hidden = None
        self.hostname = None
        self.last_visited_time = None
        self.referrer = None
        self.title = None
        self.typed = None
        self.url = None
        self.visit_count = None


class MorkReader:
    """Mork file reader.

    Mork is a text-based database format with dictionaries of columns and atoms,
    tables of rows and transaction groups that update rows.

    Attributes:
      meta_rows (dict[str, dict[str, bytes]]): cells of the rows in table meta
          data, per row identifier.
      rows (dict[str, dict[str, bytes]]): cells of the rows, per row identifier.
    """

    _COLUMN_NAME_RE = re.compile(r"[^\^=)]*")

    _COMMENT_START = "//"

    _GROUP_ABORT = "@$$}~~}@"

    _GROUP_END = "@$$}"

    _GROUP_START = "@$${"

    _HEXADECIMAL_RE = re.compile(r"[0-9A-Fa-f]{2}")

    _IDENTIFIER_RE = re.compile(r"[^\s()\[\]{}<>]*")

    _LITERAL_RE = re.compile(r"[^\\$)]+")

    _WHITESPACE = frozenset(" \t\r\n\f")

    def __init__(self):
        """Initializes a Mork file reader."""
        super().__init__()
        self._atoms = {}
        self._columns = {}
        self._text = ""
        self.meta_rows = {}
        self.rows = {}

    def _ReadDictionary(self, position):
        """Reads a dictionary.

        Args:
          position (int): offset of the dictionary start character.

        Returns:
          int: offset after the dictionary end character.

        Raises:
          ValueError: if the dictionary cannot be read.
        """
        values = self._atoms
        position += 1
        while True:
            position = self._SkipWhitespaceAndComments(position)
            character = self._text[position : position + 1]
            if character == ">":
                return position + 1

            if character == "<":
                position, is_column_scope = self._ReadDictionaryMetaData(position)
                if is_column_scope:
                    values = self._columns

            elif character == "(":
                position, identifier, value = self._ReadDictionaryCell(position)
                values[identifier] = value

            else:
                raise ValueError(
                    f"unsupported character: {character!r} in dictionary at "
                    f"offset: {position:d}"
                )

    def _ReadDictionaryCell(self, position):
        """Reads a dictionary cell, such as "(80=value)".

        Args:
          position (int): offset of the cell start character.

        Returns:
          tuple[int, str, bytes]: offset after the cell end character, identifier
              and value of the cell.

        Raises:
          ValueError: if the cell cannot be read.
        """
        end_of_identifier = self._text.find("=", position)
        if end_of_identifier == -1:
            raise ValueError(f"unterminated cell at offset: {position:d}")

        identifier = self._text[position + 1 : end_of_identifier].strip().upper()
        position, value = self._ReadLiteral(end_of_identifier + 1)
        return position, identifier, value

    def _ReadDictionaryMetaData(self, position):
        """Reads dictionary meta data, such as "<(a=c)>".

        Args:
          position (int): offset of the meta data start character.

        Returns:
          tuple[int, bool]: offset after the meta data end character and True if
              the dictionary defines column names.

        Raises:
          ValueError: if the meta data cannot be read.
        """
        is_column_scope = False
        position += 1
        while True:
            position = self._SkipWhitespaceAndComments(position)
            character = self._text[position : position + 1]
            if character == ">":
                return position + 1, is_column_scope

            if character != "(":
                raise ValueError(
                    f"unsupported character: {character!r} in dictionary meta data "
                    f"at offset: {position:d}"
                )

            position, identifier, value = self._ReadDictionaryCell(position)
            if identifier == "A" and value == b"c":
                is_column_scope = True

    def _ReadGroupMarker(self, position):
        """Reads a transaction group marker.

        The content of a committed group is read as regular content, the content
        of an aborted group is skipped.

        Args:
          position (int): offset of the group marker.

        Returns:
          int: offset after the group marker or after the aborted group.

        Raises:
          ValueError: if the group marker cannot be read.
        """
        if self._text.startswith(self._GROUP_START, position):
            end_of_marker = self._text.find("{@", position + len(self._GROUP_START))
            if end_of_marker == -1:
                raise ValueError(f"unterminated group marker at offset: {position:d}")

            end_of_group = self._text.find(self._GROUP_END, end_of_marker)
            if end_of_group != -1 and self._text.startswith(
                self._GROUP_ABORT, end_of_group
            ):
                return end_of_group + len(self._GROUP_ABORT)

            return end_of_marker + 2

        if self._text.startswith(self._GROUP_END, position):
            end_of_marker = self._text.find("}@", position + len(self._GROUP_END))
            if end_of_marker == -1:
                raise ValueError(f"unterminated group marker at offset: {position:d}")

            return end_of_marker + 2

        raise ValueError(f"unsupported group marker at offset: {position:d}")

    def _ReadIdentifier(self, position):
        """Reads an identifier, such as a row or table identifier.

        Args:
          position (int): offset of the identifier.

        Returns:
          tuple[int, str]: offset after the identifier and the identifier without
              scope.
        """
        match = self._IDENTIFIER_RE.match(self._text, position)
        identifier, _, _ = match.group(0).partition(":")
        return match.end(), identifier.upper()

    def _ReadLiteral(self, position):
        """Reads a literal value up to and including the closing parenthesis.

        Args:
          position (int): offset of the literal value.

        Returns:
          tuple[int, bytes]: offset after the closing parenthesis and the value.

        Raises:
          ValueError: if the literal value cannot be read.
        """
        value = bytearray()
        text_size = len(self._text)
        while position < text_size:
            match = self._LITERAL_RE.match(self._text, position)
            if match:
                value.extend(match.group(0).encode("latin-1"))
                position = match.end()
                continue

            character = self._text[position]
            if character == ")":
                return position + 1, bytes(value)

            if character == "$":
                hexadecimal_text = self._text[position + 1 : position + 3]
                if not self._HEXADECIMAL_RE.fullmatch(hexadecimal_text):
                    raise ValueError(
                        f"invalid hexadecimal escape at offset: {position:d}"
                    )

                value.append(int(hexadecimal_text, 16))
                position += 3

            else:
                # A backslash escapes the next character, or continues the value
                # on the next line.
                escaped_text = self._text[position + 1 : position + 3]
                if escaped_text.startswith("\n"):
                    position += 2
                elif escaped_text == "\r\n":
                    position += 3
                elif escaped_text:
                    value.extend(escaped_text[0].encode("latin-1"))
                    position += 2
                else:
                    break

        raise ValueError("unterminated literal value")

    def _ReadRow(self, position, rows, is_meta_data=False):
        """Reads a row.

        Args:
          position (int): offset of the row start character.
          rows (dict[str, dict[str, bytes]]): rows to add the cells to.
          is_meta_data (Optional[bool]): True if the row is row meta data.

        Returns:
          int: offset after the row end character.

        Raises:
          ValueError: if the row cannot be read.
        """
        position = self._SkipWhitespaceAndComments(position + 1)
        is_cut = self._text.startswith("-", position)
        if is_cut:
            position += 1

        position, identifier = self._ReadIdentifier(position)
        if not identifier:
            raise ValueError(f"missing row identifier at offset: {position:d}")

        cells = rows.setdefault(identifier, {})
        if is_cut:
            cells.clear()

        while True:
            position = self._SkipWhitespaceAndComments(position)
            character = self._text[position : position + 1]
            if character == "]":
                return position + 1

            if character == "[" and not is_meta_data:
                # Skip the row meta data.
                position = self._ReadRow(position, {}, is_meta_data=True)

            elif character == "(":
                position, column_name, value = self._ReadRowCell(position)
                cells[column_name] = value

            elif character == "-":
                position += 1

            else:
                raise ValueError(
                    f"unsupported character: {character!r} in row at offset: "
                    f"{position:d}"
                )

    def _ReadRowCell(self, position):
        """Reads a row cell, such as "(^82^8C)" or "(^82=value)".

        Args:
          position (int): offset of the cell start character.

        Returns:
          tuple[int, str, bytes]: offset after the cell end character, column name
              and value of the cell.

        Raises:
          ValueError: if the cell cannot be read.
        """
        position += 1
        is_column_reference = self._text.startswith("^", position)
        if is_column_reference:
            position += 1

        end_of_column = self._COLUMN_NAME_RE.match(self._text, position).end()
        column_name = self._text[position:end_of_column].strip()
        if is_column_reference:
            column_name = self._columns.get(column_name.upper(), b"").decode(
                "utf-8", errors="backslashreplace"
            )

        character = self._text[end_of_column : end_of_column + 1]
        if character == "=":
            position, value = self._ReadLiteral(end_of_column + 1)

        elif character == "^":
            end_of_cell = self._text.find(")", end_of_column)
            if end_of_cell == -1:
                raise ValueError(f"unterminated cell at offset: {position:d}")

            atom_identifier = self._text[end_of_column + 1 : end_of_cell]
            value = self._atoms.get(atom_identifier.strip().upper(), b"")
            position = end_of_cell + 1

        elif character == ")":
            position = end_of_column + 1
            value = b""

        else:
            raise ValueError(f"unterminated cell at offset: {position:d}")

        return position, column_name, value

    def _ReadTable(self, position):
        """Reads a table.

        Args:
          position (int): offset of the table start character.

        Returns:
          int: offset after the table end character.

        Raises:
          ValueError: if the table cannot be read.
        """
        position = self._SkipWhitespaceAndComments(position + 1)
        if self._text.startswith("-", position):
            position += 1

        position, _ = self._ReadIdentifier(position)

        while True:
            position = self._SkipWhitespaceAndComments(position)
            character = self._text[position : position + 1]
            if character == "}":
                return position + 1

            if character == "{":
                position = self._ReadTableMetaData(position)

            elif character == "[":
                position = self._ReadRow(position, self.rows)

            elif character == "@":
                position = self._ReadGroupMarker(position)

            elif character == "-":
                position += 1

            elif character and character not in "()<>]":
                # Skip a reference to an existing row.
                position, _ = self._ReadIdentifier(position)

            else:
                raise ValueError(
                    f"unsupported character: {character!r} in table at offset: "
                    f"{position:d}"
                )

    def _ReadTableMetaData(self, position):
        """Reads table meta data, such as "{(k^81:c)(s=9)[1(^B7^80)]}".

        Args:
          position (int): offset of the meta data start character.

        Returns:
          int: offset after the meta data end character.

        Raises:
          ValueError: if the meta data cannot be read.
        """
        position += 1
        while True:
            position = self._SkipWhitespaceAndComments(position)
            character = self._text[position : position + 1]
            if character == "}":
                return position + 1

            if character == "(":
                position, _, _ = self._ReadRowCell(position)

            elif character == "[":
                position = self._ReadRow(position, self.meta_rows)

            else:
                raise ValueError(
                    f"unsupported character: {character!r} in table meta data at "
                    f"offset: {position:d}"
                )

    def _SkipWhitespaceAndComments(self, position):
        """Skips whitespace and comments.

        Args:
          position (int): offset to start skipping from.

        Returns:
          int: offset of the next character that is not whitespace or part of a
              comment.
        """
        text_size = len(self._text)
        while position < text_size:
            if self._text[position] in self._WHITESPACE:
                position += 1

            elif self._text.startswith(self._COMMENT_START, position):
                end_of_line = self._text.find("\n", position)
                if end_of_line == -1:
                    return text_size

                position = end_of_line + 1

            else:
                break

        return position

    def ReadData(self, data):
        """Reads Mork data.

        Args:
          data (bytes): Mork data.

        Raises:
          ValueError: if the data cannot be read.
        """
        # Mork is byte oriented, the ISO 8859-1 codec maps each byte to a character.
        self._text = data.decode("latin-1")

        position = 0
        text_size = len(self._text)
        while position < text_size:
            position = self._SkipWhitespaceAndComments(position)
            character = self._text[position : position + 1]
            if not character:
                break

            if character == "<":
                position = self._ReadDictionary(position)

            elif character == "{":
                position = self._ReadTable(position)

            elif character == "[":
                position = self._ReadRow(position, self.rows)

            elif character == "@":
                position = self._ReadGroupMarker(position)

            else:
                raise ValueError(
                    f"unsupported character: {character!r} at offset: {position:d}"
                )


class FirefoxMorkHistoryParser(interface.FileObjectParser):
    """Parser for Mozilla Firefox 1 and 2 history (history.dat) Mork files."""

    NAME = "firefox_mork_history"
    DATA_FORMAT = "Mozilla Firefox 1 and 2 history (history.dat) Mork file"

    _HEADER = b'// <!-- <mdb:mork:z v="1.4"/> -->'

    _MAXIMUM_FILE_SIZE = 64 * 1024 * 1024

    def _GetDateTimeValue(self, parser_mediator, cells, column_name):
        """Retrieves a date and time value from a cell.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          cells (dict[str, bytes]): cells of the row.
          column_name (str): name of the column.

        Returns:
          tuple[dfdatetime.PosixTimeInMicroseconds, bool]: date and time value or
              None if not available and True if the value could not be parsed.
        """
        value = cells.get(column_name, None)
        if not value:
            return None, False

        try:
            timestamp = int(value, 10)
        except ValueError:
            parser_mediator.ProduceWarning(
                f"unable to parse {column_name:s} value: {value!r}"
            )
            return None, True

        return dfdatetime_posix_time.PosixTimeInMicroseconds(timestamp=timestamp), False

    def _GetStringValue(self, cells, column_name, byte_order=None):
        """Retrieves a string value from a cell.

        Args:
          cells (dict[str, bytes]): cells of the row.
          column_name (str): name of the column.
          byte_order (Optional[str]): byte order of UTF-16 encoded values, either
              "BE" or "LE", or None to only decode values that contain NUL bytes
              as little-endian UTF-16.

        Returns:
          str: string value or None if not available.
        """
        value = cells.get(column_name, None)
        if not value:
            return None

        if len(value) % 2 == 0 and (byte_order or b"\x00" in value):
            encoding = "utf-16-be" if byte_order == "BE" else "utf-16-le"
            return value.decode(encoding, errors="backslashreplace")

        return value.decode("utf-8", errors="backslashreplace")

    @classmethod
    def GetFormatSpecification(cls):
        """Retrieves the format specification.

        Returns:
          FormatSpecification: format specification.
        """
        format_specification = specification.FormatSpecification(cls.NAME)
        format_specification.AddNewSignature(cls._HEADER, offset=0)
        return format_specification

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a Mozilla Firefox history Mork file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        header = file_object.read(len(self._HEADER))
        if header != self._HEADER:
            raise errors.WrongParser("Not a Mork file [unsupported header]")

        file_size = file_object.get_size()
        if file_size > self._MAXIMUM_FILE_SIZE:
            parser_mediator.ProduceWarning(
                f"file size: {file_size:d} exceeds maximum supported size"
            )
            return

        mork_reader = MorkReader()
        try:
            mork_reader.ReadData(file_object.read(file_size - len(self._HEADER)))
        except ValueError as exception:
            parser_mediator.ProduceWarning(
                f"unable to read Mork data with error: {exception!s}"
            )

        byte_order = None
        for cells in mork_reader.meta_rows.values():
            byte_order = self._GetStringValue(cells, "ByteOrder") or byte_order

        for cells in mork_reader.rows.values():
            if "URL" not in cells:
                continue

            first_visited_time, first_visited_corrupted = self._GetDateTimeValue(
                parser_mediator, cells, "FirstVisitDate"
            )
            last_visited_time, last_visited_corrupted = self._GetDateTimeValue(
                parser_mediator, cells, "LastVisitDate"
            )
            visit_count = self._GetStringValue(cells, "VisitCount")

            event_data = FirefoxMorkHistoryEventData()
            event_data.first_visited_time = first_visited_time
            event_data.hidden = cells.get("Hidden", None) == b"1"
            event_data.hostname = self._GetStringValue(cells, "Hostname")
            event_data.last_visited_time = last_visited_time
            event_data.referrer = self._GetStringValue(cells, "Referrer")
            event_data.title = self._GetStringValue(
                cells, "Name", byte_order=byte_order
            )
            event_data.typed = cells.get("Typed", None) == b"1"
            event_data.url = self._GetStringValue(cells, "URL")

            if visit_count and visit_count.isdigit():
                event_data.visit_count = int(visit_count, 10)

            parser_mediator.ProduceEventData(
                event_data,
                corrupted=first_visited_corrupted or last_visited_corrupted,
            )


manager.ParsersManager.RegisterParser(FirefoxMorkHistoryParser)
