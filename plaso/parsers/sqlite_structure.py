"""Bounded pure-Python SQLite 3 REQUIRED_STRUCTURE pre-filter."""

import enum
import os
import struct

# SQLite 3 database header layout (bytes 0..100).
_SQLITE3_HEADER_MAGIC = b"SQLite format 3\x00"
_DATABASE_HEADER_SIZE = 100
# Offset 16: 16-bit big-endian page size (value 1 encodes 65536).
_PAGE_SIZE_OFFSET = 16
# Offset 18: 8-bit file format write version (1 or 2).
_WRITE_VERSION_OFFSET = 18
# Offset 19: 8-bit file format read version (1 or 2).
_READ_VERSION_OFFSET = 19
# Offset 20: 8-bit reserved space bytes at the end of each page.
_RESERVED_SPACE_OFFSET = 20
# Offsets 21..24: maximum=64, minimum=32, leaf=32 payload fractions.
_PAYLOAD_FRACTIONS_OFFSET = 21
_PAYLOAD_FRACTIONS = b"\x40\x20\x20"
# Offset 44: 32-bit big-endian schema format number (0..4).
_SCHEMA_FORMAT_OFFSET = 44
# Offset 56: 32-bit big-endian text encoding (0|1=UTF-8, 2=UTF-16LE, 3=UTF-16BE).
_TEXT_ENCODING_OFFSET = 56

_MINIMUM_PAGE_SIZE = 512
_MAXIMUM_PAGE_SIZE = 65536
_MINIMUM_USABLE_PAGE_SIZE = 480

# Table B-tree page types and headers.
_BTREE_INTERIOR_TABLE = 0x05  # Table B-tree interior page (12-byte header)
_BTREE_LEAF_TABLE = 0x0D  # Table B-tree leaf page (8-byte header)
_BTREE_LEAF_HEADER_SIZE = 8
_BTREE_INTERIOR_HEADER_SIZE = 12

# SQLite 3 Write-Ahead Log (WAL) binary header constants.
_WAL_MAGIC_LITTLE_ENDIAN = 0x377F0682
_WAL_MAGIC_BIG_ENDIAN = 0x377F0683
_WAL_FORMAT_VERSION = 3007000
_WAL_HEADER_SIZE = 32
_WAL_FRAME_HEADER_SIZE = 24

# Strict resource bounds to prevent excessive reads on malformed inputs.
_WINDOW_SIZE = 4096
_MAXIMUM_WINDOW_READS = 128  # 128 * 4 KiB = 512 KiB hard total I/O ceiling
_MAXIMUM_VISITED_PAGES = 64
_MAXIMUM_BTREE_DEPTH = 16
_MAXIMUM_STACK_SIZE = 128
_MAXIMUM_CELLS_PER_PAGE = 512
_MAXIMUM_CATALOG_ROWS = 1024
_MAXIMUM_OVERFLOW_HOPS = 16
_MAXIMUM_SQL_BYTES = 65536
_MAXIMUM_WAL_FRAMES = 4096
_MAXIMUM_WAL_PAGE1_COMPARE_BYTES = 131072
_CELL_PREFIX_READ_SIZE = 256

# Tables excluded by SQLiteDatabase.SCHEMA_QUERY.
_EXCLUDED_TABLES = frozenset(("xp_proc", "sqlite_sequence"))

# Reserved SQLite keywords that introduce table-level constraints (not columns)
# when unquoted inside CREATE TABLE (...).
_TABLE_CONSTRAINT_KEYWORDS = frozenset(
    ("CONSTRAINT", "PRIMARY", "UNIQUE", "CHECK", "FOREIGN")
)

# SQLite 3 serial type fixed payload lengths for codes 0..9.
_FIXED_SERIAL_LENGTHS = (0, 1, 2, 3, 4, 6, 8, 8, 0, 0)

_UNPACK_UINT16_BIG_ENDIAN = struct.Struct(">H").unpack_from
_UNPACK_UINT32_BIG_ENDIAN = struct.Struct(">I").unpack_from
_UNPACK_WAL_HEADER = struct.Struct(">8I").unpack_from
_UNPACK_WAL_FRAME_HEADER = struct.Struct(">4I").unpack_from


class StructureMatchStatus(enum.Enum):
    """Outcome of bounded REQUIRED_STRUCTURE pre-filtering."""

    MATCH = "match"
    NO_MATCH = "no_match"
    INVALID_HEADER = "invalid_header"
    FALLBACK = "fallback"


class StructureMatchResult:
    """Result of pre-filtering a SQLite database against enabled plugins.

    Attributes:
      bytes_read (int): total raw bytes read from file objects during pre-filtering.
      matched_plugins (list[SQLitePlugin]): enabled plugins whose required structure
          matched (or conservatively require full SQLite inspection).
      page_size (int): validated SQLite database page size, or 0 if invalid.
      read_calls (int): number of underlying read calls performed.
      status (StructureMatchStatus): pre-filter verdict.
      visited_pages (frozenset[int]): 1-based page numbers visited in sqlite_master.
    """

    __slots__ = (
        "bytes_read",
        "matched_plugins",
        "page_size",
        "read_calls",
        "status",
        "visited_pages",
    )

    def __init__(
        self,
        status,
        bytes_read=0,
        matched_plugins=None,
        page_size=0,
        read_calls=0,
        visited_pages=frozenset(),
    ):
        """Initializes a structure match result.

        Args:
          status (StructureMatchStatus): pre-filter verdict.
          bytes_read (Optional[int]): total raw bytes read during pre-filtering.
          matched_plugins (Optional[list[SQLitePlugin]]): candidate matching plugins.
          page_size (Optional[int]): validated SQLite page size in bytes.
          read_calls (Optional[int]): number of underlying read calls performed.
          visited_pages (Optional[frozenset[int]]): 1-based sqlite_master page numbers.
        """
        super().__init__()
        self.bytes_read = bytes_read
        self.matched_plugins = matched_plugins if matched_plugins is not None else []
        self.page_size = page_size
        self.read_calls = read_calls
        self.status = status
        self.visited_pages = visited_pages


class _TableSQLBookmark:
    """Location of a candidate table's CREATE TABLE SQL cell in sqlite_master."""

    __slots__ = (
        "cell_offset",
        "local_payload",
        "page_number",
        "payload_size",
        "record_start",
        "sql_length",
        "sql_offset_in_record",
    )

    def __init__(
        self,
        page_number,
        cell_offset,
        record_start,
        sql_offset_in_record,
        sql_length,
        payload_size,
        local_payload,
    ):
        """Initializes a table SQL bookmark.

        Args:
          page_number (int): 1-based page number of the leaf cell.
          cell_offset (int): byte offset of the cell within the page.
          record_start (int): byte offset of record start relative to cell_offset.
          sql_offset_in_record (int): byte offset of the SQL column within the record.
          sql_length (int): byte length of the SQL column.
          payload_size (int): total record payload size in bytes.
          local_payload (int): inline record payload bytes stored on the leaf page.
        """
        super().__init__()
        self.cell_offset = cell_offset
        self.local_payload = local_payload
        self.page_number = page_number
        self.payload_size = payload_size
        self.record_start = record_start
        self.sql_length = sql_length
        self.sql_offset_in_record = sql_offset_in_record


class _RollingWindowReader:
    """Bounded 4 KiB cached page reader over a SQLite file and optional WAL."""

    __slots__ = (
        "_cache",
        "_file_object",
        "_page_size",
        "_wal_file_object",
        "_wal_page_offsets",
        "_window_reads",
        "bytes_read",
        "reached_read_limit",
        "read_calls",
    )

    def __init__(
        self,
        file_object,
        page_size=0,
        wal_file_object=None,
        wal_page_offsets=None,
    ):
        """Initializes a bounded page reader.

        Args:
          file_object (file): binary file-like object of the main SQLite database.
          page_size (Optional[int]): database page size in bytes.
          wal_file_object (Optional[file]): binary file-like object of the WAL file.
          wal_page_offsets (Optional[dict[int, int]]): mapping of 1-based page number
              to page data offset inside wal_file_object.
        """
        super().__init__()
        self._cache = {}
        self._file_object = file_object
        self._page_size = page_size
        self._wal_file_object = wal_file_object
        self._wal_page_offsets = wal_page_offsets or {}
        self._window_reads = 0
        self.bytes_read = 0
        self.reached_read_limit = False
        self.read_calls = 0

    def SetPageSize(self, page_size):
        """Sets the validated database page size.

        Args:
          page_size (int): database page size in bytes.
        """
        self._page_size = page_size

    def _ReadRawAt(self, use_wal, file_offset, length):
        """Reads up to length bytes from main file or WAL using a bounded 4 KiB cache.

        Args:
          use_wal (bool): True to read from wal_file_object, False for main file.
          file_offset (int): byte offset in the target file.
          length (int): number of bytes to read.

        Returns:
          bytes: bytes read (may be shorter than length on EOF or I/O cap).
        """
        if length <= 0 or file_offset < 0:
            return b""

        target_file = self._wal_file_object if use_wal else self._file_object
        if target_file is None:
            return b""

        cache = self._cache
        aligned_offset = file_offset & ~(_WINDOW_SIZE - 1)
        relative_offset = file_offset - aligned_offset

        # Fast path: requested slice lies completely inside one 4 KiB block.
        if relative_offset + length <= _WINDOW_SIZE:
            cache_key = (use_wal, aligned_offset)
            data = cache.get(cache_key)
            if data is None:
                if self._window_reads >= _MAXIMUM_WINDOW_READS:
                    self.reached_read_limit = True
                    return b""
                target_file.seek(aligned_offset, os.SEEK_SET)
                data = target_file.read(_WINDOW_SIZE)
                self._window_reads += 1
                self.read_calls += 1
                self.bytes_read += len(data)
                cache[cache_key] = data
            if relative_offset >= len(data):
                return b""
            return data[relative_offset : relative_offset + length]

        chunks = []
        remaining = length
        cursor = file_offset
        while remaining > 0:
            aligned_offset = cursor & ~(_WINDOW_SIZE - 1)
            cache_key = (use_wal, aligned_offset)
            data = cache.get(cache_key)
            if data is None:
                if self._window_reads >= _MAXIMUM_WINDOW_READS:
                    self.reached_read_limit = True
                    break
                target_file.seek(aligned_offset, os.SEEK_SET)
                data = target_file.read(_WINDOW_SIZE)
                self._window_reads += 1
                self.read_calls += 1
                self.bytes_read += len(data)
                cache[cache_key] = data

            relative_offset = cursor - aligned_offset
            if relative_offset >= len(data):
                break
            available = len(data) - relative_offset
            take = min(available, remaining)
            chunks.append(data[relative_offset : relative_offset + take])
            cursor += take
            remaining -= take

        if not chunks:
            return b""
        if len(chunks) == 1:
            return chunks[0]
        return b"".join(chunks)

    def ReadPageSlice(self, page_number, relative_offset, length):
        """Reads up to length bytes from a 1-based SQLite page.

        Args:
          page_number (int): 1-based SQLite page number.
          relative_offset (int): byte offset within the page.
          length (int): number of bytes to read.

        Returns:
          bytes: bytes read (may be shorter than length on EOF or I/O cap).
        """
        if page_number <= 0 or relative_offset < 0 or length <= 0:
            return b""
        if self._page_size > 0 and relative_offset >= self._page_size:
            return b""
        if self._page_size > 0 and relative_offset + length > self._page_size:
            length = self._page_size - relative_offset

        wal_base_offset = self._wal_page_offsets.get(page_number)
        if wal_base_offset is not None:
            return self._ReadRawAt(True, wal_base_offset + relative_offset, length)

        if self._page_size == 0:
            if page_number != 1:
                return b""
            return self._ReadRawAt(False, relative_offset, length)

        page_file_offset = (page_number - 1) * self._page_size
        return self._ReadRawAt(False, page_file_offset + relative_offset, length)


def _ReadVarint(buffer, offset):
    """Decodes an SQLite 3 big-endian varint (1 to 9 bytes) at offset.

    Args:
      buffer (bytes): byte buffer.
      offset (int): start index inside buffer.

    Returns:
      tuple: containing:

        int: decoded integer value
        int: next byte offset after the varint
      or None if the buffer ends before the varint terminates.
    """
    buffer_length = len(buffer)
    if offset >= buffer_length:
        return None

    # Fast path for common 1-byte varints (0..127).
    first_byte = buffer[offset]
    if first_byte < 0x80:
        return first_byte, offset + 1

    value = first_byte & 0x7F
    limit = min(offset + 9, buffer_length)

    for index in range(offset + 1, limit):
        byte_value = buffer[index]
        if index == offset + 8:
            value = (value << 8) | byte_value
            return value, index + 1
        value = (value << 7) | (byte_value & 0x7F)
        if byte_value < 0x80:
            return value, index + 1

    return None


def _SerialTypeLength(serial_type):
    """Computes the byte length of an SQLite record column for serial_type.

    Args:
      serial_type (int): SQLite record serial type code.

    Returns:
      int: byte length, or None for reserved serial types (10, 11).
    """
    if serial_type < 10:
        return _FIXED_SERIAL_LENGTHS[serial_type]
    if serial_type >= 12:
        return (serial_type - 12) >> 1
    return None


def _TableLeafLocalPayload(payload_size, usable_size):
    """Computes local inline payload bytes for a table B-tree leaf cell.

    Args:
      payload_size (int): total record payload size in bytes.
      usable_size (int): usable page size (page_size - reserved_space).

    Returns:
      int: number of payload bytes stored locally on the leaf page.
    """
    maximum_local = usable_size - 35
    if payload_size <= maximum_local:
        return payload_size
    minimum_local = ((usable_size - 12) * 32 // 255) - 23
    split_payload = minimum_local + ((payload_size - minimum_local) % (usable_size - 4))
    return split_payload if split_payload <= maximum_local else minimum_local


def _DecodeSQLiteText(raw_bytes, encoding):
    """Decodes an SQLite TEXT payload according to the database text encoding.

    Args:
      raw_bytes (bytes): raw column bytes from sqlite_master.
      encoding (int): SQLite header encoding code (0|1=UTF-8, 2=UTF-16LE, 3=UTF-16BE).

    Returns:
      str: decoded string, or None if decoding fails.
    """
    try:
        if encoding in (0, 1):
            text = raw_bytes.decode("utf-8")
        elif encoding == 2:
            if len(raw_bytes) & 1:
                return None
            text = raw_bytes.decode("utf-16-le")
        elif encoding == 3:
            if len(raw_bytes) & 1:
                return None
            text = raw_bytes.decode("utf-16-be")
        else:
            return None
    except UnicodeDecodeError:
        return None

    # SQLite's C text API terminates at embedded NUL if present in tampered rows.
    null_byte_index = text.find("\x00")
    if null_byte_index != -1:
        text = text[:null_byte_index]
    return text


def _IsTableTypeBytes(raw_bytes, encoding):
    """Checks whether raw column 0 bytes decode to exact 'table'.

    Args:
      raw_bytes (bytes): raw bytes of sqlite_master.type column.
      encoding (int): SQLite header encoding code.

    Returns:
      bool: True if raw_bytes represents exact lowercase 'table'.
    """
    if encoding in (0, 1):
        return raw_bytes == b"table"
    if encoding == 2:
        return raw_bytes == b"t\x00a\x00b\x00l\x00e\x00"
    if encoding == 3:
        return raw_bytes == b"\x00t\x00a\x00b\x00l\x00e"
    return False


def _ReadCellPayloadRange(
    reader,
    usable_size,
    page_number,
    cell_offset,
    record_start,
    payload_size,
    local_payload,
    want_start,
    want_length,
):
    """Reads a byte slice from a leaf cell's record payload, following overflow pages.

    Args:
      reader (_RollingWindowReader): rolling page reader.
      usable_size (int): usable page size (page_size - reserved_space).
      page_number (int): 1-based page number of the leaf cell.
      cell_offset (int): byte offset of the cell on page_number.
      record_start (int): byte offset of record payload start relative to cell_offset.
      payload_size (int): total record payload length in bytes.
      local_payload (int): inline record payload bytes stored on page_number.
      want_start (int): byte offset within the record payload to begin reading.
      want_length (int): number of bytes to read.

    Returns:
      bytes: exact want_length bytes, or None on corruption, I/O cap, or EOF.
    """
    if want_length == 0:
        return b""
    if want_start < 0 or want_length < 0 or want_length > _MAXIMUM_SQL_BYTES:
        return None
    want_end = want_start + want_length
    if want_end > payload_size:
        return None

    chunks = []

    # 1. Read any portion stored inline on the leaf page.
    if want_start < local_payload:
        local_end = min(want_end, local_payload)
        local_length = local_end - want_start
        part = reader.ReadPageSlice(
            page_number, cell_offset + record_start + want_start, local_length
        )
        if len(part) != local_length:
            return None
        chunks.append(part)
        if local_end == want_end:
            return part

    # 2. Follow overflow page chain for bytes past local_payload.
    overflow_pointer_bytes = reader.ReadPageSlice(
        page_number, cell_offset + record_start + local_payload, 4
    )
    if len(overflow_pointer_bytes) != 4:
        return None
    overflow_page_number = _UNPACK_UINT32_BIG_ENDIAN(overflow_pointer_bytes, 0)[0]

    chunk_capacity = usable_size - 4
    if chunk_capacity <= 0:
        return None

    stream_offset = local_payload
    visited_overflow = set()
    hops = 0

    while stream_offset < want_end:
        if overflow_page_number == 0 or overflow_page_number in visited_overflow:
            return None
        hops += 1
        if hops > _MAXIMUM_OVERFLOW_HOPS:
            return None
        visited_overflow.add(overflow_page_number)

        next_pointer_bytes = reader.ReadPageSlice(overflow_page_number, 0, 4)
        if len(next_pointer_bytes) != 4:
            return None
        next_page_number = _UNPACK_UINT32_BIG_ENDIAN(next_pointer_bytes, 0)[0]

        chunk_end = stream_offset + chunk_capacity
        if chunk_end > want_start:
            read_from = max(want_start, stream_offset)
            read_to = min(want_end, chunk_end)
            relative_offset = 4 + (read_from - stream_offset)
            take = read_to - read_from
            part = reader.ReadPageSlice(overflow_page_number, relative_offset, take)
            if len(part) != take:
                return None
            chunks.append(part)

        stream_offset = chunk_end
        overflow_page_number = next_page_number

    result = chunks[0] if len(chunks) == 1 else b"".join(chunks)
    return result if len(result) == want_length else None


def _TokenizeSQL(sql):
    """Tokenizes an SQLite CREATE TABLE statement, stripping whitespace and comments.

    Args:
      sql (str): raw CREATE TABLE SQL string from sqlite_master.

    Returns:
      list[tuple[str, str]]: list of (kind, value) tokens, or None if
          unterminated quotes or comments are encountered.
    """
    tokens = []
    index = 0
    length = len(sql)

    while index < length:
        character = sql[index]

        # Whitespace.
        if character <= " ":
            index += 1
            continue

        # Line comment: -- ... \n
        if character == "-" and index + 1 < length and sql[index + 1] == "-":
            newline = sql.find("\n", index + 2)
            if newline == -1:
                break
            index = newline + 1
            continue

        # Block comment: /* ... */
        if character == "/" and index + 1 < length and sql[index + 1] == "*":
            end = sql.find("*/", index + 2)
            if end == -1:
                return None
            index = end + 2
            continue

        # Single-character punctuation.
        if character == "(":
            tokens.append(("LPAREN", "("))
            index += 1
            continue
        if character == ")":
            tokens.append(("RPAREN", ")"))
            index += 1
            continue
        if character == ",":
            tokens.append(("COMMA", ","))
            index += 1
            continue
        if character == ".":
            tokens.append(("DOT", "."))
            index += 1
            continue

        # Quoted identifiers and string literals: "...", `...`, '...'
        if character in ('"', "`", "'"):
            quote = character
            index += 1
            parts = []
            start = index
            closed = False
            while index < length:
                position = sql.find(quote, index)
                if position == -1:
                    return None
                parts.append(sql[start:position])
                if position + 1 < length and sql[position + 1] == quote:
                    parts.append(quote)
                    index = position + 2
                    start = index
                else:
                    index = position + 1
                    closed = True
                    break
            if not closed:
                return None
            tokens.append(("QUOTED", "".join(parts)))
            continue

        # Bracket-quoted identifier: [...]
        if character == "[":
            end = sql.find("]", index + 1)
            if end == -1:
                return None
            tokens.append(("QUOTED", sql[index + 1 : end]))
            index = end + 1
            continue

        # Unquoted identifier: starts with ASCII letter, '_', or non-ASCII codepoint.
        if character.isalpha() or character == "_" or ord(character) >= 0x80:
            start = index
            index += 1
            while index < length:
                next_character = sql[index]
                if (
                    next_character.isalnum()
                    or next_character in ("_", "$")
                    or ord(next_character) >= 0x80
                ):
                    index += 1
                else:
                    break
            tokens.append(("IDENT", sql[start:index]))
            continue

        # Numbers or other operators (relevant only after column name).
        start = index
        index += 1
        while index < length:
            next_character = sql[index]
            if next_character <= " " or next_character in (
                "(",
                ")",
                ",",
                ".",
                '"',
                "`",
                "'",
                "[",
                "-",
                "/",
            ):
                break
            index += 1
        tokens.append(("OTHER", sql[start:index]))

    return tokens


def ExtractColumnsFromCreateTableSQL(sql):
    """Extracts declared column names from a standard CREATE TABLE SQL statement.

    Conservatively returns None for CREATE VIRTUAL TABLE, malformed DDL, or any
    construct whose column list cannot be determined solely from the DDL text.

    Args:
      sql (str): SQL text from sqlite_master.sql.

    Returns:
      frozenset[str]: declared column names (exact case, unquoted), or None if
          the statement is not a standard parseable CREATE TABLE.
    """
    if not sql:
        return None

    tokens = _TokenizeSQL(sql)
    if not tokens:
        return None

    position = 0
    number_of_tokens = len(tokens)

    # Expect: CREATE [TEMP | TEMPORARY] TABLE [IF NOT EXISTS] [schema.]name (
    if tokens[position][0] != "IDENT" or tokens[position][1].upper() != "CREATE":
        return None
    position += 1

    if position < number_of_tokens and tokens[position][0] == "IDENT":
        if tokens[position][1].upper() in ("TEMP", "TEMPORARY"):
            position += 1

    if position >= number_of_tokens or tokens[position][0] != "IDENT":
        return None
    if tokens[position][1].upper() != "TABLE":
        # Rejects CREATE VIRTUAL TABLE and non-table statements conservatively.
        return None
    position += 1

    # Optional IF NOT EXISTS.
    if (
        position + 2 < number_of_tokens
        and tokens[position][0] == "IDENT"
        and tokens[position][1].upper() == "IF"
        and tokens[position + 1][0] == "IDENT"
        and tokens[position + 1][1].upper() == "NOT"
        and tokens[position + 2][0] == "IDENT"
        and tokens[position + 2][1].upper() == "EXISTS"
    ):
        position += 3

    # Table name: [schema .] table_name.
    if position >= number_of_tokens or tokens[position][0] not in ("IDENT", "QUOTED"):
        return None
    position += 1
    if position < number_of_tokens and tokens[position][0] == "DOT":
        position += 1
        if position >= number_of_tokens or tokens[position][0] not in (
            "IDENT",
            "QUOTED",
        ):
            return None
        position += 1

    # Must open column definition list with '('.
    if position >= number_of_tokens or tokens[position][0] != "LPAREN":
        return None
    position += 1

    columns = set()
    depth = 0
    at_element_start = True

    while position < number_of_tokens:
        kind, value = tokens[position]
        position += 1

        if depth == 0:
            if kind == "RPAREN":
                return frozenset(columns) if columns else None
            if kind == "COMMA":
                at_element_start = True
                continue
            if kind == "LPAREN":
                depth += 1
                at_element_start = False
                continue

            if at_element_start:
                at_element_start = False
                if kind == "QUOTED":
                    columns.add(value)
                elif kind == "IDENT":
                    if value.upper() not in _TABLE_CONSTRAINT_KEYWORDS:
                        columns.add(value)
                else:
                    return None
        else:
            if kind == "LPAREN":
                depth += 1
            elif kind == "RPAREN":
                depth -= 1

    return None


def _ValidateHeaderStatus(header_bytes):
    """Validates a 100-byte SQLite 3 header, distinguishing invalid vs fallback.

    Hard-invalid checks mirror the constraints SQLite's lockBtree() requires
    before a database can be opened read-only. Non-standard values that SQLite
    tolerates in read-only mode (for example write_version > 2 or unusual high
    bytes in schema_format or text_encoding) request conservative fallback.

    Args:
      header_bytes (bytes): first 100 bytes of the database file (page 1).

    Returns:
      tuple: containing:

        StructureMatchStatus: error or fallback status, or None if valid
        tuple[int, int, int]: (page_size, usable_size, encoding) or None on error
    """
    if len(header_bytes) < _DATABASE_HEADER_SIZE:
        return StructureMatchStatus.INVALID_HEADER, None
    if not header_bytes.startswith(_SQLITE3_HEADER_MAGIC):
        return StructureMatchStatus.INVALID_HEADER, None

    page_raw = _UNPACK_UINT16_BIG_ENDIAN(header_bytes, _PAGE_SIZE_OFFSET)[0]
    page_size = 65536 if page_raw == 1 else page_raw
    if (
        page_size < _MINIMUM_PAGE_SIZE
        or page_size > _MAXIMUM_PAGE_SIZE
        or (page_size & (page_size - 1)) != 0
    ):
        return StructureMatchStatus.INVALID_HEADER, None

    read_version = header_bytes[_READ_VERSION_OFFSET]
    if read_version > 2:
        return StructureMatchStatus.INVALID_HEADER, None

    reserved_space = header_bytes[_RESERVED_SPACE_OFFSET]
    usable_size = page_size - reserved_space
    if usable_size < _MINIMUM_USABLE_PAGE_SIZE:
        return StructureMatchStatus.INVALID_HEADER, None

    if (
        header_bytes[_PAYLOAD_FRACTIONS_OFFSET : _PAYLOAD_FRACTIONS_OFFSET + 3]
        != _PAYLOAD_FRACTIONS
    ):
        return StructureMatchStatus.INVALID_HEADER, None

    write_version = header_bytes[_WRITE_VERSION_OFFSET]
    schema_format = _UNPACK_UINT32_BIG_ENDIAN(header_bytes, _SCHEMA_FORMAT_OFFSET)[0]
    encoding = _UNPACK_UINT32_BIG_ENDIAN(header_bytes, _TEXT_ENCODING_OFFSET)[0]
    if (
        write_version not in (1, 2)
        or read_version not in (1, 2)
        or schema_format > 4
        or encoding > 3
    ):
        return StructureMatchStatus.FALLBACK, None

    return None, (page_size, usable_size, encoding)


def ValidateHeader(header_bytes):
    """Validates a 100-byte SQLite 3 database header.

    Args:
      header_bytes (bytes): first 100 bytes of the database file (page 1).

    Returns:
      tuple[int, int, int]: (page_size, usable_size, text_encoding) if valid,
          or None if the header is not a valid standard SQLite 3 header.
    """
    error_status, validated = _ValidateHeaderStatus(header_bytes)
    if error_status is not None:
        return None
    return validated


def _BuildWALPageIndex(wal_file_object, expected_page_size):
    """Scans WAL frame headers only (never user page payloads) to map committed pages.

    Args:
      wal_file_object (file): binary file-like object of the WAL file.
      expected_page_size (int): page size of the main SQLite database.

    Returns:
      tuple: containing:

        dict[int, int]: committed page offsets keyed by 1-based page number, or
            None when the WAL header is malformed or frame limit is exceeded
        dict[int, set[int]]: commit indices per 1-based page number
        list[int]: committed WAL payload offsets for page 1
        int: total bytes read from wal_file_object
        int: number of read calls performed
    """
    wal_file_object.seek(0, os.SEEK_SET)
    wal_header = wal_file_object.read(_WAL_HEADER_SIZE)
    bytes_read = len(wal_header)
    read_calls = 1

    # An empty or sub-header WAL file has no valid committed frames.
    if not wal_header:
        return {}, {}, [], bytes_read, read_calls
    if len(wal_header) < _WAL_HEADER_SIZE:
        return None, {}, [], bytes_read, read_calls

    magic, format_version, wal_page_size, _, salt1, salt2, _, _ = _UNPACK_WAL_HEADER(
        wal_header, 0
    )
    if (
        magic not in (_WAL_MAGIC_LITTLE_ENDIAN, _WAL_MAGIC_BIG_ENDIAN)
        or format_version != _WAL_FORMAT_VERSION
        or wal_page_size != expected_page_size
    ):
        return None, {}, [], bytes_read, read_calls

    committed = {}
    pending = {}
    page_commit_indices = {}
    page1_offsets = []
    commit_index = 0
    frame_stride = _WAL_FRAME_HEADER_SIZE + expected_page_size
    offset = _WAL_HEADER_SIZE
    completed_scan = False

    for _ in range(_MAXIMUM_WAL_FRAMES):
        wal_file_object.seek(offset, os.SEEK_SET)
        frame_header = wal_file_object.read(_WAL_FRAME_HEADER_SIZE)
        read_calls += 1
        bytes_read += len(frame_header)
        if len(frame_header) < _WAL_FRAME_HEADER_SIZE:
            completed_scan = True
            break

        (
            page_number,
            database_size_after_commit,
            frame_salt1,
            frame_salt2,
        ) = _UNPACK_WAL_FRAME_HEADER(frame_header, 0)
        if frame_salt1 != salt1 or frame_salt2 != salt2:
            completed_scan = True
            break
        if page_number == 0:
            return None, {}, [], bytes_read, read_calls

        pending[page_number] = offset + _WAL_FRAME_HEADER_SIZE
        if database_size_after_commit != 0:
            commit_index += 1
            for committed_page_number in pending:
                page_commit_indices.setdefault(committed_page_number, set()).add(
                    commit_index
                )
            if 1 in pending:
                page1_offsets.append(pending[1])
            committed.update(pending)
            pending.clear()

        offset += frame_stride

    if not completed_scan:
        # More frames than _MAXIMUM_WAL_FRAMES; conservatively fall back.
        return None, {}, [], bytes_read, read_calls

    return committed, page_commit_indices, page1_offsets, bytes_read, read_calls


def _WALOnlyUpdatesPage1Header(file_object, wal_file_object, page_size, page1_offsets):
    """Checks whether every committed WAL copy of page 1 preserves sqlite_master.

    Growing WAL databases routinely update page 1's 100-byte database header
    (change counter, database page count, freelist pointers) during data-only
    commits without altering the sqlite_master catalog B-tree stored at bytes
    100 through page_size.

    Args:
      file_object (file): main database file-like object.
      wal_file_object (file): WAL file-like object.
      page_size (int): validated database page size in bytes.
      page1_offsets (list[int]): committed WAL payload offsets for page 1.

    Returns:
      tuple: containing:

        bool: True if sqlite_master on page 1 is unchanged across all commits
        int: total bytes read during comparison
        int: number of read calls performed
    """
    if (
        not page1_offsets
        or (len(page1_offsets) + 1) * page_size > _MAXIMUM_WAL_PAGE1_COMPARE_BYTES
    ):
        return False, 0, 0

    file_object.seek(0, os.SEEK_SET)
    main_page1 = file_object.read(page_size)
    bytes_read = len(main_page1)
    read_calls = 1
    if len(main_page1) != page_size:
        return False, bytes_read, read_calls

    main_header_prefix = main_page1[:24]
    main_header_middle = main_page1[44:92]
    main_btree = main_page1[_DATABASE_HEADER_SIZE:]

    for frame_offset in page1_offsets:
        wal_file_object.seek(frame_offset, os.SEEK_SET)
        wal_page1 = wal_file_object.read(page_size)
        bytes_read += len(wal_page1)
        read_calls += 1
        if (
            len(wal_page1) != page_size
            or wal_page1[:24] != main_header_prefix
            or wal_page1[44:92] != main_header_middle
            or wal_page1[_DATABASE_HEADER_SIZE:] != main_btree
        ):
            return False, bytes_read, read_calls

    return True, bytes_read, read_calls


def _OverridesRequiredStructureCheck(plugin, default_check_function=None):
    """Determines whether a plugin overrides CheckRequiredTablesAndColumns.

    Args:
      plugin (SQLitePlugin): SQLite parser plugin instance.
      default_check_function (Optional[Callable]): base class method to compare
          against when provided explicitly.

    Returns:
      bool: True if the plugin overrides CheckRequiredTablesAndColumns.
    """
    if "CheckRequiredTablesAndColumns" in getattr(plugin, "__dict__", ()):
        return True

    if default_check_function is not None:
        plugin_check = getattr(type(plugin), "CheckRequiredTablesAndColumns", None)
        return plugin_check is not default_check_function

    for cls in type(plugin).__mro__:
        if "CheckRequiredTablesAndColumns" in cls.__dict__:
            return (
                cls.__module__ != "plaso.parsers.sqlite_plugins.interface"
                or cls.__name__ != "SQLitePlugin"
            )
    return False


class SQLitePluginStructureMatcher:
    """Matches SQLite databases against enabled Plaso plugins via sqlite_master."""

    def __init__(self, plugins, default_check_function=None):
        """Initializes the matcher from the currently enabled SQLite plugins.

        Args:
          plugins (Iterable[SQLitePlugin]): enabled SQLite parser plugins.
          default_check_function (Optional[Callable]): base class
              CheckRequiredTablesAndColumns method; if any enabled plugin
              overrides it, pre-filtering falls back conservatively.
        """
        super().__init__()
        self._all_required_tables = frozenset()
        self._force_fallback = False
        self._plugin_entries = []
        self._plugins_by_trigger = {}
        self._trigger_table_set = frozenset()

        all_required_tables = set()
        trigger_tables = {}

        for plugin in plugins:
            if _OverridesRequiredStructureCheck(
                plugin, default_check_function=default_check_function
            ):
                self._force_fallback = True

            required_structure = getattr(plugin, "REQUIRED_STRUCTURE", None)
            if not required_structure:
                # If a plugin defines no REQUIRED_STRUCTURE (or overrides the
                # check), fall back conservatively to full database opening.
                self._force_fallback = True
                continue
            required_tables = frozenset(required_structure.keys())
            required_items = tuple(
                (table_name, frozenset(columns))
                for table_name, columns in required_structure.items()
            )
            entry = (plugin, required_tables, required_items)
            self._plugin_entries.append(entry)
            all_required_tables.update(required_tables)

            # Index plugin under its longest (typically most specific) required table.
            trigger = max(required_tables, key=len)
            trigger_tables.setdefault(trigger, []).append(entry)

        self._all_required_tables = frozenset(all_required_tables)
        self._plugins_by_trigger = trigger_tables
        self._trigger_table_set = frozenset(trigger_tables.keys())

    def _WalkMasterCatalog(self, reader, usable_size, encoding):
        """Walks the sqlite_master catalog B-tree (page 1 root) with strict bounds.

        Args:
          reader (_RollingWindowReader): rolling page reader.
          usable_size (int): usable page size (page_size - reserved_space).
          encoding (int): database text encoding code.

        Returns:
          tuple: containing:

            bool: True if the entire catalog B-tree was walked cleanly
            set[str]: table names present in sqlite_master
            dict[str, list[_TableSQLBookmark]]: SQL cell bookmarks per table
            set[int]: 1-based page numbers visited in sqlite_master
        """
        visited_pages = set()
        stack = [(1, 0)]
        table_names = set()
        candidate_bookmarks = {}
        rows_inspected = 0
        catalog_complete = True
        required_tables = self._all_required_tables

        while stack:
            page_number, depth = stack.pop()
            if page_number == 0 or page_number in visited_pages:
                catalog_complete = False
                continue
            if (
                len(visited_pages) >= _MAXIMUM_VISITED_PAGES
                or depth >= _MAXIMUM_BTREE_DEPTH
            ):
                catalog_complete = False
                break
            visited_pages.add(page_number)

            header_offset = _DATABASE_HEADER_SIZE if page_number == 1 else 0
            page_header = reader.ReadPageSlice(
                page_number, header_offset, _BTREE_LEAF_HEADER_SIZE
            )
            if len(page_header) != _BTREE_LEAF_HEADER_SIZE:
                catalog_complete = False
                continue

            page_type = page_header[0]
            cell_count = _UNPACK_UINT16_BIG_ENDIAN(page_header, 3)[0]
            if cell_count > _MAXIMUM_CELLS_PER_PAGE:
                catalog_complete = False
                break

            if page_type == _BTREE_INTERIOR_TABLE:
                right_bytes = reader.ReadPageSlice(
                    page_number, header_offset + _BTREE_LEAF_HEADER_SIZE, 4
                )
                if len(right_bytes) != 4:
                    catalog_complete = False
                    continue
                right_child = _UNPACK_UINT32_BIG_ENDIAN(right_bytes, 0)[0]
                if right_child != 0:
                    if len(stack) < _MAXIMUM_STACK_SIZE:
                        stack.append((right_child, depth + 1))
                    else:
                        catalog_complete = False
                        break

                pointer_array_offset = header_offset + _BTREE_INTERIOR_HEADER_SIZE
                pointer_bytes_length = cell_count * 2
                pointer_bytes = reader.ReadPageSlice(
                    page_number, pointer_array_offset, pointer_bytes_length
                )
                if len(pointer_bytes) != pointer_bytes_length:
                    catalog_complete = False
                    continue

                minimum_cell_offset = pointer_array_offset + pointer_bytes_length
                # Sort interior cell pointers for sequential window access.
                interior_offsets = []
                for index in range(cell_count):
                    cell_offset = _UNPACK_UINT16_BIG_ENDIAN(pointer_bytes, index * 2)[0]
                    if (
                        cell_offset < minimum_cell_offset
                        or cell_offset + 4 > usable_size
                    ):
                        catalog_complete = False
                        continue
                    interior_offsets.append(cell_offset)

                interior_offsets.sort()
                children = []
                for cell_offset in interior_offsets:
                    child_bytes = reader.ReadPageSlice(page_number, cell_offset, 4)
                    if len(child_bytes) != 4:
                        catalog_complete = False
                        continue
                    child_page_number = _UNPACK_UINT32_BIG_ENDIAN(child_bytes, 0)[0]
                    if child_page_number != 0:
                        children.append(child_page_number)

                for child_page_number in reversed(children):
                    if len(stack) < _MAXIMUM_STACK_SIZE:
                        stack.append((child_page_number, depth + 1))
                    else:
                        catalog_complete = False
                        break

            elif page_type == _BTREE_LEAF_TABLE:
                pointer_array_offset = header_offset + _BTREE_LEAF_HEADER_SIZE
                pointer_bytes_length = cell_count * 2
                pointer_bytes = reader.ReadPageSlice(
                    page_number, pointer_array_offset, pointer_bytes_length
                )
                if len(pointer_bytes) != pointer_bytes_length:
                    catalog_complete = False
                    continue

                minimum_cell_offset = pointer_array_offset + pointer_bytes_length
                cell_offsets = []
                for index in range(cell_count):
                    cell_offset = _UNPACK_UINT16_BIG_ENDIAN(pointer_bytes, index * 2)[0]
                    if cell_offset < minimum_cell_offset or cell_offset >= usable_size:
                        catalog_complete = False
                        continue
                    cell_offsets.append(cell_offset)

                # Visit cells in ascending offset order to avoid 4 KiB window thrashing.
                cell_offsets.sort()

                for cell_offset in cell_offsets:
                    if rows_inspected >= _MAXIMUM_CATALOG_ROWS:
                        catalog_complete = False
                        break
                    rows_inspected += 1

                    maximum_prefix_length = min(
                        usable_size - cell_offset, _CELL_PREFIX_READ_SIZE
                    )
                    cell = reader.ReadPageSlice(
                        page_number, cell_offset, maximum_prefix_length
                    )
                    if len(cell) < 6:
                        catalog_complete = False
                        continue

                    parsed = _ReadVarint(cell, 0)
                    if parsed is None:
                        catalog_complete = False
                        continue
                    payload_size, rowid_offset = parsed

                    parsed = _ReadVarint(cell, rowid_offset)
                    if parsed is None:
                        catalog_complete = False
                        continue
                    _, record_start = parsed

                    local_payload = _TableLeafLocalPayload(payload_size, usable_size)
                    if (
                        local_payload == 0
                        or record_start + local_payload > usable_size - cell_offset
                    ):
                        catalog_complete = False
                        continue
                    # Bytes belonging to this cell end strictly at local_end;
                    # any bytes beyond record_start + local_payload are the overflow
                    # page pointer or adjacent cells and must be read via overflow.
                    local_end = min(len(cell), record_start + local_payload)
                    if record_start >= local_end:
                        catalog_complete = False
                        continue

                    parsed = _ReadVarint(cell, record_start)
                    if parsed is None:
                        catalog_complete = False
                        continue
                    header_size, header_position = parsed
                    if header_size < 2 or header_size > payload_size:
                        catalog_complete = False
                        continue

                    # Standard 5-column sqlite_master record headers are <= 46 bytes.
                    if record_start + header_size > local_end:
                        catalog_complete = False
                        continue

                    header_end = record_start + header_size
                    column_lengths = []
                    column_types = []
                    is_valid_header = True
                    while header_position < header_end and len(column_lengths) < 5:
                        parsed = _ReadVarint(cell, header_position)
                        if parsed is None:
                            is_valid_header = False
                            break
                        serial_type, header_position = parsed
                        if header_position > header_end:
                            is_valid_header = False
                            break
                        column_length = _SerialTypeLength(serial_type)
                        if column_length is None:
                            is_valid_header = False
                            break
                        column_types.append(serial_type)
                        column_lengths.append(column_length)

                    if not is_valid_header or len(column_lengths) < 3:
                        catalog_complete = False
                        continue

                    # Column 0: type (must be TEXT == 'table').
                    type_serial_type = column_types[0]
                    if type_serial_type < 13 or (type_serial_type & 1) == 0:
                        continue
                    type_record_start = header_size
                    type_record_end = type_record_start + column_lengths[0]
                    if record_start + type_record_end <= local_end:
                        type_raw = cell[
                            record_start
                            + type_record_start : record_start
                            + type_record_end
                        ]
                    else:
                        type_raw = _ReadCellPayloadRange(
                            reader,
                            usable_size,
                            page_number,
                            cell_offset,
                            record_start,
                            payload_size,
                            local_payload,
                            type_record_start,
                            column_lengths[0],
                        )
                        if type_raw is None:
                            catalog_complete = False
                            continue

                    if not _IsTableTypeBytes(type_raw, encoding):
                        continue

                    # Column 2: tbl_name (matches SQLiteDatabase.SCHEMA_QUERY).
                    table_serial_type = column_types[2]
                    if table_serial_type < 13 or (table_serial_type & 1) == 0:
                        catalog_complete = False
                        continue
                    table_record_start = type_record_end + column_lengths[1]
                    table_record_end = table_record_start + column_lengths[2]
                    if record_start + table_record_end <= local_end:
                        table_raw = cell[
                            record_start
                            + table_record_start : record_start
                            + table_record_end
                        ]
                    else:
                        table_raw = _ReadCellPayloadRange(
                            reader,
                            usable_size,
                            page_number,
                            cell_offset,
                            record_start,
                            payload_size,
                            local_payload,
                            table_record_start,
                            column_lengths[2],
                        )
                        if table_raw is None:
                            catalog_complete = False
                            continue

                    table_name = _DecodeSQLiteText(table_raw, encoding)
                    if table_name is None:
                        catalog_complete = False
                        continue

                    if table_name in _EXCLUDED_TABLES:
                        continue

                    table_names.add(table_name)

                    # Bookmark column 4 (sql) only for required tables.
                    if table_name in required_tables:
                        if (
                            len(column_lengths) == 5
                            and column_types[4] >= 13
                            and (column_types[4] & 1) == 1
                            and column_lengths[4] > 0
                        ):
                            sql_offset_in_record = table_record_end + column_lengths[3]
                            bookmark = _TableSQLBookmark(
                                page_number,
                                cell_offset,
                                record_start,
                                sql_offset_in_record,
                                column_lengths[4],
                                payload_size,
                                local_payload,
                            )
                            candidate_bookmarks.setdefault(table_name, []).append(
                                bookmark
                            )
                        else:
                            # Missing or NULL sql for a required table: mark uncertain.
                            candidate_bookmarks.setdefault(table_name, []).append(None)

                if not catalog_complete and rows_inspected >= _MAXIMUM_CATALOG_ROWS:
                    break

            else:
                catalog_complete = False
                break

        if reader.reached_read_limit:
            catalog_complete = False

        return catalog_complete, table_names, candidate_bookmarks, visited_pages

    def _EvaluateCandidates(
        self, reader, usable_size, encoding, table_names, candidate_bookmarks
    ):
        """Evaluates enabled plugins against extracted table names and lazy DDL columns.

        Args:
          reader (_RollingWindowReader): rolling page reader for lazy SQL reads.
          usable_size (int): usable page size.
          encoding (int): database text encoding code.
          table_names (set[str]): table names present in sqlite_master.
          candidate_bookmarks (dict[str, list[_TableSQLBookmark]]): bookmarks
              for required tables present in sqlite_master.

        Returns:
          list[SQLitePlugin]: plugins whose required tables and columns match (or
              whose DDL could not be statically parsed, conservatively included).
        """
        # Step 1: fast trigger-table rejection (O(1) set disjoint check).
        hit_triggers = table_names & self._trigger_table_set
        if not hit_triggers:
            return []

        table_candidates = []
        for trigger in hit_triggers:
            for entry in self._plugins_by_trigger[trigger]:
                _, required_tables, _ = entry
                if required_tables <= table_names:
                    table_candidates.append(entry)

        if not table_candidates:
            return []

        # Step 2: lazy CREATE TABLE DDL column parsing only for matched tables.
        parsed_columns_cache = {}
        matched_plugins = []

        for plugin, _, required_items in table_candidates:
            plugin_matches = True
            for table_name, required_columns in required_items:
                if not required_columns:
                    continue

                if table_name not in parsed_columns_cache:
                    parsed_columns_cache[table_name] = self._ParseColumnsForTable(
                        reader,
                        usable_size,
                        encoding,
                        candidate_bookmarks.get(table_name),
                    )

                columns = parsed_columns_cache[table_name]
                # columns is None for VIRTUAL TABLE or unparsable DDL: keep the
                # plugin as a candidate so sqlite3 checks it conservatively.
                if columns is not None and not required_columns.issubset(columns):
                    plugin_matches = False
                    break

            if plugin_matches:
                matched_plugins.append(plugin)

        return matched_plugins

    def _ParseColumnsForTable(self, reader, usable_size, encoding, bookmarks):
        """Reads and parses CREATE TABLE column names for a candidate table.

        Args:
          reader (_RollingWindowReader): rolling page reader.
          usable_size (int): usable page size.
          encoding (int): database text encoding code.
          bookmarks (list[_TableSQLBookmark]): SQL cell bookmarks, or None.

        Returns:
          frozenset[str]: column names, or None if uncertain or unparsable.
        """
        if not bookmarks:
            return None

        combined_columns = set()
        for bookmark in bookmarks:
            if bookmark is None:
                return None
            sql_raw = _ReadCellPayloadRange(
                reader,
                usable_size,
                bookmark.page_number,
                bookmark.cell_offset,
                bookmark.record_start,
                bookmark.payload_size,
                bookmark.local_payload,
                bookmark.sql_offset_in_record,
                bookmark.sql_length,
            )
            if sql_raw is None:
                return None
            sql_text = _DecodeSQLiteText(sql_raw, encoding)
            if sql_text is None:
                return None
            columns = ExtractColumnsFromCreateTableSQL(sql_text)
            if columns is None:
                return None
            combined_columns.update(columns)

        return frozenset(combined_columns)

    def MatchFileObject(
        self,
        file_object,
        wal_file_object=None,
        wal_page_offsets=None,
    ):
        """Pre-filters a SQLite database file-like object without full-file copy.

        Args:
          file_object (file): binary file-like object of the SQLite database.
          wal_file_object (Optional[file]): optional WAL file-like object.
          wal_page_offsets (Optional[dict[int, int]]): optional committed WAL page
              offsets keyed by 1-based page number.

        Returns:
          StructureMatchResult: pre-filter verdict, candidate plugins, and metadata.
        """
        if not self._plugin_entries and not self._force_fallback:
            return StructureMatchResult(StructureMatchStatus.NO_MATCH)

        reader = _RollingWindowReader(
            file_object,
            wal_file_object=wal_file_object,
            wal_page_offsets=wal_page_offsets,
        )

        # Read the 100-byte SQLite header (page 1, offset 0).
        header = reader.ReadPageSlice(1, 0, _DATABASE_HEADER_SIZE)
        if not header:
            if self._force_fallback:
                return StructureMatchResult(
                    StructureMatchStatus.FALLBACK,
                    bytes_read=reader.bytes_read,
                    read_calls=reader.read_calls,
                )
            # An empty 0-byte file is a valid empty SQLite database with 0 tables.
            return StructureMatchResult(
                StructureMatchStatus.NO_MATCH,
                bytes_read=reader.bytes_read,
                read_calls=reader.read_calls,
            )

        error_status, validated = _ValidateHeaderStatus(header)
        if error_status is not None:
            return StructureMatchResult(
                error_status,
                bytes_read=reader.bytes_read,
                read_calls=reader.read_calls,
            )

        page_size, usable_size, encoding = validated
        if self._force_fallback:
            return StructureMatchResult(
                StructureMatchStatus.FALLBACK,
                bytes_read=reader.bytes_read,
                page_size=page_size,
                read_calls=reader.read_calls,
            )

        reader.SetPageSize(page_size)

        (
            catalog_complete,
            table_names,
            candidate_bookmarks,
            visited_pages,
        ) = self._WalkMasterCatalog(reader, usable_size, encoding)

        if not catalog_complete:
            return StructureMatchResult(
                StructureMatchStatus.FALLBACK,
                bytes_read=reader.bytes_read,
                page_size=page_size,
                read_calls=reader.read_calls,
                visited_pages=frozenset(visited_pages),
            )

        matched_plugins = self._EvaluateCandidates(
            reader, usable_size, encoding, table_names, candidate_bookmarks
        )
        if reader.reached_read_limit:
            return StructureMatchResult(
                StructureMatchStatus.FALLBACK,
                bytes_read=reader.bytes_read,
                page_size=page_size,
                read_calls=reader.read_calls,
                visited_pages=frozenset(visited_pages),
            )

        status = (
            StructureMatchStatus.MATCH
            if matched_plugins
            else StructureMatchStatus.NO_MATCH
        )
        return StructureMatchResult(
            status,
            bytes_read=reader.bytes_read,
            matched_plugins=matched_plugins,
            page_size=page_size,
            read_calls=reader.read_calls,
            visited_pages=frozenset(visited_pages),
        )

    def MatchFileObjectWithWAL(self, file_object, wal_file_object, main_result):
        """Pre-filters a SQLite database with an accompanying WAL file.

        Scans only 24-byte WAL frame headers (never user-table page payloads) and
        re-walks sqlite_master only when a committed WAL frame touches a page in
        main_result.visited_pages.

        Args:
          file_object (file): binary file-like object of the main SQLite database.
          wal_file_object (file): binary file-like object of the WAL file.
          main_result (StructureMatchResult): result from MatchFileObject(file_object).

        Returns:
          StructureMatchResult: pre-filter verdict for the database with WAL applied.
        """
        if not self._plugin_entries and not self._force_fallback:
            return StructureMatchResult(StructureMatchStatus.NO_MATCH)

        if (
            self._force_fallback
            or main_result.status
            in (
                StructureMatchStatus.FALLBACK,
                StructureMatchStatus.INVALID_HEADER,
            )
            or main_result.page_size == 0
        ):
            return StructureMatchResult(StructureMatchStatus.FALLBACK)

        committed, page_commit_indices, page1_offsets, wal_bytes, wal_reads = (
            _BuildWALPageIndex(wal_file_object, main_result.page_size)
        )
        if committed is None:
            return StructureMatchResult(
                StructureMatchStatus.FALLBACK,
                bytes_read=wal_bytes,
                page_size=main_result.page_size,
                read_calls=wal_reads,
            )

        # If no committed WAL frame modifies any sqlite_master catalog page (always
        # including page 1), the database structure is provably unchanged by WAL.
        touched_catalog_pages = set(committed) & main_result.visited_pages
        if not touched_catalog_pages:
            return StructureMatchResult(
                main_result.status,
                bytes_read=wal_bytes,
                matched_plugins=list(main_result.matched_plugins),
                page_size=main_result.page_size,
                read_calls=wal_reads,
                visited_pages=main_result.visited_pages,
            )

        # Growing data-only WAL commits frequently rewrite page 1 solely to update
        # database header counters while leaving sqlite_master unchanged.
        if touched_catalog_pages == {1}:
            header_only, compared_bytes, compared_reads = _WALOnlyUpdatesPage1Header(
                file_object, wal_file_object, main_result.page_size, page1_offsets
            )
            wal_bytes += compared_bytes
            wal_reads += compared_reads
            if header_only:
                return StructureMatchResult(
                    main_result.status,
                    bytes_read=wal_bytes,
                    matched_plugins=list(main_result.matched_plugins),
                    page_size=main_result.page_size,
                    read_calls=wal_reads,
                    visited_pages=main_result.visited_pages,
                )

        # Re-walk sqlite_master with the committed WAL pages overlaid.
        wal_result = self.MatchFileObject(
            file_object,
            wal_file_object=wal_file_object,
            wal_page_offsets=committed,
        )
        wal_result.bytes_read += wal_bytes
        wal_result.read_calls += wal_reads
        if wal_result.status == StructureMatchStatus.INVALID_HEADER:
            wal_result.status = StructureMatchStatus.FALLBACK
            return wal_result

        # Guard against a corrupt-checksum trailing WAL frame that appears to
        # drop a matching table added in an earlier commit: when >= 2 distinct
        # WAL commits touch any sqlite_master catalog page and the final state
        # returned NO_MATCH, conservatively fall back to sqlite3 WAL replay
        # without reading user-table page payloads.
        if (
            wal_result.status == StructureMatchStatus.NO_MATCH
            and main_result.status == StructureMatchStatus.NO_MATCH
        ):
            catalog_pages = main_result.visited_pages | wal_result.visited_pages
            catalog_commits = set()
            for page_number in catalog_pages:
                commits = page_commit_indices.get(page_number)
                if commits:
                    catalog_commits.update(commits)
            if len(catalog_commits) > 1:
                wal_result.status = StructureMatchStatus.FALLBACK

        return wal_result
