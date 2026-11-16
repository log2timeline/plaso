#!/usr/bin/env python3
"""Tests for the bounded SQLite REQUIRED_STRUCTURE pre-filter."""

import io
import os
import sqlite3
import struct
import tempfile
import unittest

from plaso.parsers import sqlite_structure


class _MockPlugin:
    """Minimal stand-in for SQLitePlugin declaring NAME and REQUIRED_STRUCTURE."""

    NAME = ""
    REQUIRED_STRUCTURE = {}

    def __init__(self, name, required_structure):
        """Initializes a mock plugin.

        Args:
          name (str): plugin name.
          required_structure (dict[str, frozenset[str]]): required tables and columns.
        """
        super().__init__()
        self.NAME = name  # pylint: disable=invalid-name
        self.REQUIRED_STRUCTURE = required_structure  # pylint: disable=invalid-name


class _CustomCheckPlugin(_MockPlugin):
    """Mock plugin that overrides CheckRequiredTablesAndColumns."""

    def CheckRequiredTablesAndColumns(self, database):
        """Checks custom database requirements.

        Args:
          database (object): unused placeholder database.

        Returns:
          bool: always True.
        """
        return database is not None


class _TrackedBytesIO:
    """File-like wrapper recording every byte range read."""

    def __init__(self, data):
        """Initializes a tracked in-memory file-like object.

        Args:
          data (bytes): backing byte buffer.
        """
        super().__init__()
        self._buffer = io.BytesIO(data)
        self.read_ranges = []
        self.total_bytes_read = 0

    # Note that the following functions do not follow the style guide because
    # they are part of the Python file-like object interface.
    # pylint: disable=invalid-name

    def seek(self, offset, whence=os.SEEK_SET):
        """Seeks within the buffer.

        Args:
          offset (int): byte offset.
          whence (Optional[int]): seek origin.

        Returns:
          int: new stream position.
        """
        return self._buffer.seek(offset, whence)

    def read(self, size=-1):
        """Reads bytes from the buffer and records the read range.

        Args:
          size (Optional[int]): maximum number of bytes to read.

        Returns:
          bytes: bytes read from the buffer.
        """
        start_offset = self._buffer.tell()
        chunk = self._buffer.read(size)
        if chunk:
            self.read_ranges.append((start_offset, start_offset + len(chunk)))
            self.total_bytes_read += len(chunk)
        return chunk


def _BuildSQLiteBytes(sql_statements, encoding="UTF-8", page_size=4096, use_wal=False):
    """Creates a real SQLite database (and optional uncheckpointed WAL) in bytes.

    Args:
      sql_statements (list[str]): SQL statements to execute.
      encoding (Optional[str]): SQLite PRAGMA encoding name.
      page_size (Optional[int]): database page size in bytes.
      use_wal (Optional[bool]): True to enable WAL mode without checkpointing.

    Returns:
      tuple: containing:

        bytes: main database file bytes
        bytes: WAL file bytes (empty when use_wal is False)
    """
    with tempfile.TemporaryDirectory() as temporary_directory:
        database_path = os.path.join(temporary_directory, "test.db")
        connection = sqlite3.connect(database_path)
        connection.execute(f"PRAGMA page_size = {page_size:d}")
        connection.execute(f'PRAGMA encoding = "{encoding:s}"')
        if use_wal:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA wal_autocheckpoint = 0")
        for statement in sql_statements:
            connection.execute(statement)
        connection.commit()
        if not use_wal:
            connection.close()
            with open(database_path, "rb") as file_object:
                return file_object.read(), b""

        # Read database and WAL while connection holds WAL open (uncheckpointed).
        with open(database_path, "rb") as file_object:
            database_bytes = file_object.read()
        wal_path = f"{database_path:s}-wal"
        wal_bytes = b""
        if os.path.exists(wal_path):
            with open(wal_path, "rb") as file_object:
                wal_bytes = file_object.read()
        connection.close()
        return database_bytes, wal_bytes


class SQLiteStructureUnitTest(unittest.TestCase):
    """Unit tests for header validation, DDL column parsing, B-tree walk, and WAL."""

    def testValidateHeaderValidAndInvalid(self):
        """Tests SQLite 3 100-byte header validation."""
        for page_size in (512, 1024, 4096, 32768, 65536):
            database_bytes, _ = _BuildSQLiteBytes(
                ["CREATE TABLE items (identifier INT)"], page_size=page_size
            )
            validated = sqlite_structure.ValidateHeader(database_bytes[:100])
            self.assertEqual(validated, (page_size, page_size, 1))

        # Missing NUL byte in magic.
        bad_magic = bytearray(database_bytes[:100])
        bad_magic[15] = ord("X")
        self.assertIsNone(sqlite_structure.ValidateHeader(bytes(bad_magic)))

        # Non-power-of-two page size (such as 51200 / 0xC800).
        bad_page_size = bytearray(database_bytes[:100])
        struct.pack_into(">H", bad_page_size, 16, 51200)
        self.assertIsNone(sqlite_structure.ValidateHeader(bytes(bad_page_size)))

        # Bad payload fractions.
        bad_fractions = bytearray(database_bytes[:100])
        bad_fractions[21] = 63
        self.assertIsNone(sqlite_structure.ValidateHeader(bytes(bad_fractions)))

        # Usable size below 480 (page_size=512, reserved=33 gives usable=479).
        minimum_database, _ = _BuildSQLiteBytes(
            ["CREATE TABLE items (identifier INT)"], page_size=512
        )
        bad_reserved = bytearray(minimum_database[:100])
        bad_reserved[20] = 33
        self.assertIsNone(sqlite_structure.ValidateHeader(bytes(bad_reserved)))

        # Truncated header.
        self.assertIsNone(sqlite_structure.ValidateHeader(database_bytes[:99]))

    def testExtractColumnsFromCreateTableSQL(self):
        """Tests DDL column extraction across SQLite quoting, comments, and syntax."""
        test_cases = [
            (
                "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT NOT NULL)",
                frozenset(("id", "name")),
            ),
            (
                'CREATE TABLE "t""(1)" ("a""b" INT, `c``d` TEXT, [e f] BLOB, '
                "'g''h' REAL)",
                frozenset(('a"b', "c`d", "e f", "g'h")),
            ),
            (
                "CREATE TABLE /* comment 1 */ items -- comment 2\n"
                "(/* comment 3 */ alpha INT, -- comment 4\n"
                " beta TEXT DEFAULT '-- not comment' CHECK (beta != '/*x*/'))",
                frozenset(("alpha", "beta")),
            ),
            (
                "CREATE TABLE items (id INT, count INT, "
                "CONSTRAINT primary_id PRIMARY KEY (id), "
                "UNIQUE (count), CHECK (count > 0), "
                "FOREIGN KEY (count) REFERENCES other(id))",
                frozenset(("id", "count")),
            ),
            (
                'CREATE TABLE items ("primary" INT, [unique] TEXT, `check` INT, '
                "'foreign' INT, \"constraint\" INT)",
                frozenset(("primary", "unique", "check", "foreign", "constraint")),
            ),
            (
                "CREATE TEMP TABLE IF NOT EXISTS main.items ("
                "alpha DECIMAL(10, 2) DEFAULT (abs(-1)), "
                "beta TEXT CHECK (beta IN ('a,b', 'c)d')), gamma) "
                "WITHOUT ROWID, STRICT",
                frozenset(("alpha", "beta", "gamma")),
            ),
        ]
        for sql_statement, expected_columns in test_cases:
            self.assertEqual(
                sqlite_structure.ExtractColumnsFromCreateTableSQL(sql_statement),
                expected_columns,
                sql_statement,
            )

        # Conservative None fallbacks: virtual tables and malformed DDL.
        for fallback_sql in (
            "CREATE VIRTUAL TABLE virtual_items USING fts5(title, body)",
            "CREATE TABLE items (alpha INT, 'unterminated",
            "CREATE TABLE items /* unterminated (alpha INT)",
            "CREATE TABLE items ()",
            "",
        ):
            self.assertIsNone(
                sqlite_structure.ExtractColumnsFromCreateTableSQL(fallback_sql),
                fallback_sql,
            )

    def testEncodingsUTF8UTF16LEUTF16BE(self):
        """Tests matching across UTF-8, UTF-16LE, and UTF-16BE databases."""
        plugin = _MockPlugin("demo", {"urls": frozenset(("id", "url", "title"))})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        for encoding in ("UTF-8", "UTF-16le", "UTF-16be"):
            database_bytes, _ = _BuildSQLiteBytes(
                ["CREATE TABLE urls (id INT, url TEXT, title TEXT)"],
                encoding=encoding,
            )
            result = matcher.MatchFileObject(io.BytesIO(database_bytes))
            self.assertEqual(
                result.status,
                sqlite_structure.StructureMatchStatus.MATCH,
                encoding,
            )
            self.assertEqual(
                [matched.NAME for matched in result.matched_plugins], ["demo"]
            )

    def testCaseSensitivityAndAndroidMetadataKept(self):
        """Tests exact case sensitivity and preservation of android_metadata."""
        lower_plugin = _MockPlugin("lower_users", {"users": frozenset(("id",))})
        upper_plugin = _MockPlugin("upper_users", {"Users": frozenset(("id",))})
        android_plugin = _MockPlugin(
            "android_webview",
            {
                "android_metadata": frozenset(("locale",)),
                "cookies": frozenset(("name", "value")),
            },
        )
        matcher = sqlite_structure.SQLitePluginStructureMatcher(
            [lower_plugin, upper_plugin, android_plugin]
        )

        database_bytes, _ = _BuildSQLiteBytes(
            [
                "CREATE TABLE Users (id INT)",
                "CREATE TABLE android_metadata (locale TEXT)",
                "CREATE TABLE cookies (name TEXT, value TEXT)",
            ]
        )
        result = matcher.MatchFileObject(io.BytesIO(database_bytes))
        self.assertEqual(result.status, sqlite_structure.StructureMatchStatus.MATCH)
        self.assertEqual(
            sorted(matched.NAME for matched in result.matched_plugins),
            ["android_webview", "upper_users"],
        )

    def testColumnPreFilterRejectsGenericTableCollisions(self):
        """Tests that a colliding table name with non-matching columns is skipped."""
        kodi_plugin = _MockPlugin(
            "kodi",
            {"files": frozenset(("idFile", "idPath", "strFilename", "playCount"))},
        )
        matcher = sqlite_structure.SQLitePluginStructureMatcher([kodi_plugin])

        database_bytes, _ = _BuildSQLiteBytes(
            ["CREATE TABLE files (sha256 TEXT, size_bytes INTEGER)"]
        )
        result = matcher.MatchFileObject(io.BytesIO(database_bytes))
        self.assertEqual(result.status, sqlite_structure.StructureMatchStatus.NO_MATCH)
        self.assertEqual(result.matched_plugins, [])

    def testMultiPageBTreeAndOverflowSQL(self):
        """Tests interior B-tree pages and multi-page overflow CREATE TABLE SQL."""
        # 512-byte pages force both interior B-tree splits and overflow DDL chains.
        statements = [
            f"CREATE TABLE table_{index:03d} (id INT, value TEXT)"
            for index in range(60)
        ]
        column_definitions = ", ".join(
            f"column_{index:03d} TEXT" for index in range(140)
        )
        statements.append(f"CREATE TABLE target_wide ({column_definitions:s})")

        database_bytes, _ = _BuildSQLiteBytes(statements, page_size=512)
        plugin = _MockPlugin(
            "wide_plugin",
            {"target_wide": frozenset(("column_000", "column_075", "column_139"))},
        )
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        result = matcher.MatchFileObject(io.BytesIO(database_bytes))
        self.assertEqual(result.status, sqlite_structure.StructureMatchStatus.MATCH)
        self.assertEqual(
            [matched.NAME for matched in result.matched_plugins], ["wide_plugin"]
        )
        self.assertGreater(len(result.visited_pages), 1)

    def testZeroPIIAndZeroUserTableReads(self):
        """Verifies user table payloads are never read on large non-matching files."""
        sensitive_marker = b"SENSITIVE_USER_DATA_DO_NOT_READ_1234567890"
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = os.path.join(temporary_directory, "messages.db")
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA page_size = 4096")
            connection.execute("CREATE TABLE private_messages (id INT, body BLOB)")
            payload = sensitive_marker * 100
            connection.executemany(
                "INSERT INTO private_messages VALUES (?, ?)",
                [(index, payload) for index in range(500)],
            )
            connection.commit()
            connection.close()
            with open(database_path, "rb") as file_object:
                database_bytes = file_object.read()

        self.assertGreater(len(database_bytes), 2_000_000)
        plugin = _MockPlugin("chrome", {"urls": frozenset(("id", "url"))})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        tracked_stream = _TrackedBytesIO(database_bytes)
        result = matcher.MatchFileObject(tracked_stream)
        self.assertEqual(result.status, sqlite_structure.StructureMatchStatus.NO_MATCH)
        # Only page 1 (4096 bytes) should be read out of more than 2 MB.
        self.assertEqual(tracked_stream.total_bytes_read, 4096)
        for start_offset, end_offset in tracked_stream.read_ranges:
            self.assertNotIn(sensitive_marker, database_bytes[start_offset:end_offset])

    def testWALStructureEvolutionAndNoUserPayloadRead(self):
        """Tests WAL overlay: unchanged structure skips, newly created table matches."""
        plugin = _MockPlugin(
            "target", {"wal_events": frozenset(("id", "timestamp", "extra"))}
        )
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        # Case 1: WAL only inserts rows into an unrelated table -> NO_MATCH.
        wal_marker = b"WAL_SECRET_PAYLOAD_NEVER_READ"
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = os.path.join(temporary_directory, "application.db")
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA page_size = 4096")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA wal_autocheckpoint = 0")
            connection.execute("CREATE TABLE notes (id INT, body BLOB)")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            connection.executemany(
                "INSERT INTO notes VALUES (?, ?)",
                [(index, wal_marker * 100) for index in range(50)],
            )
            connection.commit()
            with open(database_path, "rb") as file_object:
                database_bytes = file_object.read()
            with open(f"{database_path:s}-wal", "rb") as file_object:
                wal_bytes = file_object.read()
            connection.close()

        self.assertGreater(len(wal_bytes), 150_000)
        main_tracked = _TrackedBytesIO(database_bytes)
        wal_tracked = _TrackedBytesIO(wal_bytes)
        main_result = matcher.MatchFileObject(main_tracked)
        wal_result = matcher.MatchFileObjectWithWAL(
            main_tracked, wal_tracked, main_result
        )
        self.assertEqual(
            main_result.status, sqlite_structure.StructureMatchStatus.NO_MATCH
        )
        self.assertEqual(
            wal_result.status, sqlite_structure.StructureMatchStatus.NO_MATCH
        )
        for start_offset, end_offset in wal_tracked.read_ranges:
            self.assertNotIn(wal_marker, wal_bytes[start_offset:end_offset])

        # Case 2: Main database has no matching table; WAL creates it -> MATCH.
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = os.path.join(temporary_directory, "evolved.db")
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA page_size = 4096")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA wal_autocheckpoint = 0")
            connection.execute("CREATE TABLE unrelated (value INT)")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            # Create matching table only in the WAL.
            connection.execute("CREATE TABLE wal_events (id INT, timestamp INT)")
            connection.execute("ALTER TABLE wal_events ADD COLUMN extra TEXT")
            connection.commit()
            with open(database_path, "rb") as file_object:
                database_bytes = file_object.read()
            with open(f"{database_path:s}-wal", "rb") as file_object:
                wal_bytes = file_object.read()
            connection.close()

        main_stream = io.BytesIO(database_bytes)
        wal_stream = io.BytesIO(wal_bytes)
        main_result = matcher.MatchFileObject(main_stream)
        wal_result = matcher.MatchFileObjectWithWAL(
            main_stream, wal_stream, main_result
        )
        self.assertEqual(
            main_result.status, sqlite_structure.StructureMatchStatus.NO_MATCH
        )
        self.assertEqual(wal_result.status, sqlite_structure.StructureMatchStatus.MATCH)
        self.assertEqual(
            [matched.NAME for matched in wal_result.matched_plugins], ["target"]
        )

    def testAdversarialCyclicBTreeAndOverflowAndIOCap(self):
        """Tests that crafted malformed databases terminate within 512 KiB I/O."""
        plugin = _MockPlugin("any", {"items": frozenset(("alpha",))})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        # 1. Cyclic interior B-tree: page 1 -> page 2 -> page 1.
        base_bytes, _ = _BuildSQLiteBytes(
            ["CREATE TABLE items (alpha INT)"], page_size=4096
        )
        cyclic = bytearray(base_bytes + b"\x00" * 4096)
        # Page 1 interior header at offset 100: type=0x05, cell_count=1, right_child=2.
        cyclic[100] = 0x05
        struct.pack_into(">H", cyclic, 103, 1)
        struct.pack_into(">I", cyclic, 108, 2)
        struct.pack_into(">H", cyclic, 112, 200)
        struct.pack_into(">I", cyclic, 200, 2)
        # Page 2 interior header at offset 4096: points back to page 1.
        cyclic[4096] = 0x05
        struct.pack_into(">H", cyclic, 4099, 1)
        struct.pack_into(">I", cyclic, 4104, 1)
        struct.pack_into(">H", cyclic, 4108, 200)
        struct.pack_into(">I", cyclic, 4096 + 200, 1)
        cyclic_result = matcher.MatchFileObject(io.BytesIO(bytes(cyclic)))
        self.assertEqual(
            cyclic_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )

        # 2. Crafted 64 x 64 KiB (4 MiB) interior/leaf bomb stays <= 512 KiB I/O.
        page_size = 65536
        header = bytearray(100)
        header[0:16] = b"SQLite format 3\x00"
        struct.pack_into(">H", header, 16, 1)  # 65536
        header[18] = 1
        header[19] = 1
        header[20] = 0
        header[21:24] = b"\x40\x20\x20"
        struct.pack_into(">I", header, 44, 4)
        struct.pack_into(">I", header, 56, 1)

        bomb = bytearray(page_size * 65)
        bomb[0:100] = header
        # Page 1 interior pointing to pages 2..65.
        bomb[100] = 0x05
        struct.pack_into(">H", bomb, 103, 63)
        struct.pack_into(">I", bomb, 108, 65)
        for index in range(63):
            cell_offset = 500 + index * 8
            struct.pack_into(">H", bomb, 112 + index * 2, cell_offset)
            struct.pack_into(">I", bomb, cell_offset, index + 2)
        # Each leaf page has cells spread across every 4 KiB chunk.
        for page_number in range(2, 66):
            page_offset = (page_number - 1) * page_size
            bomb[page_offset] = 0x0D
            struct.pack_into(">H", bomb, page_offset + 3, 15)
            for cell_index in range(15):
                cell_offset = (cell_index + 1) * 4096 + 16
                struct.pack_into(
                    ">H", bomb, page_offset + 8 + cell_index * 2, cell_offset
                )

        bomb_result = matcher.MatchFileObject(io.BytesIO(bytes(bomb)))
        self.assertEqual(
            bomb_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )
        self.assertLessEqual(bomb_result.bytes_read, 512 * 1024)

    def testVirtualTableConservativeFallback(self):
        """Tests that a plugin targeting a VIRTUAL TABLE falls back conservatively."""
        plugin = _MockPlugin(
            "virtual_table_plugin", {"search_index": frozenset(("title", "body"))}
        )
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])
        database_bytes, _ = _BuildSQLiteBytes(
            ["CREATE VIRTUAL TABLE search_index USING fts5(title, body)"]
        )
        result = matcher.MatchFileObject(io.BytesIO(database_bytes))
        # Must not return NO_MATCH (which would cause a false negative).
        self.assertEqual(result.status, sqlite_structure.StructureMatchStatus.MATCH)
        self.assertEqual(
            [matched.NAME for matched in result.matched_plugins],
            ["virtual_table_plugin"],
        )

    def testSmallPageUTF16OverflowTableName(self):
        """Tests spilled table_name overflow when local_payload < cell prefix size."""
        columns = frozenset(("event", "bundle_id", "app_version", "extra_0", "extra_5"))
        plugin = _MockPlugin("appusage", {"application_usage": columns})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        statements = [
            f"CREATE TABLE noise_{index:d} (alpha INT, beta TEXT)" for index in range(3)
        ]
        column_definitions = ", ".join(
            f'"{column_name:s}" TEXT' for column_name in sorted(columns)
        )
        statements.append(f'CREATE TABLE "application_usage" ({column_definitions:s})')

        # 512-byte pages + UTF-16LE force local_payload=39 bytes, spilling the
        # table name into overflow pages.
        database_bytes, wal_bytes = _BuildSQLiteBytes(
            statements, encoding="UTF-16le", page_size=512, use_wal=True
        )
        main_stream = io.BytesIO(database_bytes)
        wal_stream = io.BytesIO(wal_bytes)
        main_result = matcher.MatchFileObject(main_stream)
        wal_result = matcher.MatchFileObjectWithWAL(
            main_stream, wal_stream, main_result
        )
        self.assertEqual(wal_result.status, sqlite_structure.StructureMatchStatus.MATCH)
        self.assertEqual(
            [matched.NAME for matched in wal_result.matched_plugins], ["appusage"]
        )

    def testNonStandardReadableHeaderFallbackVsHardInvalid(self):
        """Tests read-only-tolerable headers fall back while hard-invalid reject."""
        plugin = _MockPlugin("demo", {"items": frozenset(("alpha",))})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])
        database_bytes, _ = _BuildSQLiteBytes(["CREATE TABLE items (alpha INT)"])

        # SQLite opens databases with write_version > 2 in read-only mode.
        read_only_header = bytearray(database_bytes)
        read_only_header[18] = 0x7F
        read_only_result = matcher.MatchFileObject(io.BytesIO(bytes(read_only_header)))
        self.assertEqual(
            read_only_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )

        # SQLite strictly rejects read_version > 2.
        bad_read_version = bytearray(database_bytes)
        bad_read_version[19] = 3
        bad_read_version_result = matcher.MatchFileObject(
            io.BytesIO(bytes(bad_read_version))
        )
        self.assertEqual(
            bad_read_version_result.status,
            sqlite_structure.StructureMatchStatus.INVALID_HEADER,
        )

    def testPluginOverrideAndEmptyStructureFallback(self):
        """Tests fallback for empty REQUIRED_STRUCTURE or check overrides."""
        database_bytes, _ = _BuildSQLiteBytes(["CREATE TABLE unrelated (value INT)"])

        # Empty REQUIRED_STRUCTURE falls back conservatively.
        empty_plugin = _MockPlugin("empty_required", {})
        matcher_empty = sqlite_structure.SQLitePluginStructureMatcher([empty_plugin])
        empty_result = matcher_empty.MatchFileObject(io.BytesIO(database_bytes))
        self.assertEqual(
            empty_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )
        zero_byte_result = matcher_empty.MatchFileObject(io.BytesIO(b""))
        self.assertEqual(
            zero_byte_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )

        # Subclass overriding CheckRequiredTablesAndColumns falls back.
        custom_plugin = _CustomCheckPlugin("custom_check", {"urls": frozenset(("id",))})
        matcher_custom = sqlite_structure.SQLitePluginStructureMatcher([custom_plugin])
        custom_result = matcher_custom.MatchFileObject(io.BytesIO(database_bytes))
        self.assertEqual(
            custom_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )

        # Instance-level CheckRequiredTablesAndColumns override falls back.
        patched_plugin = _MockPlugin("patched", {"urls": frozenset(("id",))})
        setattr(
            patched_plugin,
            "CheckRequiredTablesAndColumns",
            lambda database: True,
        )
        matcher_patched = sqlite_structure.SQLitePluginStructureMatcher(
            [patched_plugin]
        )
        patched_result = matcher_patched.MatchFileObject(io.BytesIO(database_bytes))
        self.assertEqual(
            patched_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )

    def testWALMultiCommitCorruptChecksumFallback(self):
        """Tests fallback when >=2 WAL commits modify catalog pages and end NO_MATCH."""
        plugin = _MockPlugin("target", {"wal_events": frozenset(("id", "timestamp"))})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = os.path.join(temporary_directory, "wal_drop.db")
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA page_size = 4096")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA wal_autocheckpoint = 0")
            connection.execute("CREATE TABLE unrelated (value INT)")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            # Commit 1 creates the matching table in the WAL.
            connection.execute("CREATE TABLE wal_events (id INT, timestamp INT)")
            connection.commit()
            # Commit 2 drops the matching table in the WAL.
            connection.execute("DROP TABLE wal_events")
            connection.commit()

            with open(database_path, "rb") as file_object:
                database_bytes = file_object.read()
            with open(f"{database_path:s}-wal", "rb") as file_object:
                wal_bytes = bytearray(file_object.read())
            connection.close()

        # Corrupt the trailing commit frame checksum so sqlite3 stops at commit 1
        # (where wal_events exists) while unverified frame replay sees commit 2.
        frame_stride = 24 + 4096
        number_of_frames = (len(wal_bytes) - 32) // frame_stride
        self.assertGreaterEqual(number_of_frames, 2)
        last_frame_offset = 32 + (number_of_frames - 1) * frame_stride
        wal_bytes[last_frame_offset + 16] ^= 0xFF

        main_stream = io.BytesIO(database_bytes)
        wal_stream = io.BytesIO(bytes(wal_bytes))
        main_result = matcher.MatchFileObject(main_stream)
        wal_result = matcher.MatchFileObjectWithWAL(
            main_stream, wal_stream, main_result
        )
        self.assertEqual(
            main_result.status, sqlite_structure.StructureMatchStatus.NO_MATCH
        )
        self.assertEqual(
            wal_result.status, sqlite_structure.StructureMatchStatus.FALLBACK
        )

    def testWALGrowingDataOnlyCommitsSkipFallback(self):
        """Tests that multi-commit WAL growth on page 1 header returns NO_MATCH."""
        plugin = _MockPlugin("target", {"wal_events": frozenset(("id", "timestamp"))})
        matcher = sqlite_structure.SQLitePluginStructureMatcher([plugin])
        wal_marker = b"WAL_GROWING_USER_PAYLOAD_DO_NOT_READ"

        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = os.path.join(temporary_directory, "growing.db")
            connection = sqlite3.connect(database_path)
            connection.execute("PRAGMA page_size = 4096")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA wal_autocheckpoint = 0")
            connection.execute("CREATE TABLE notes (id INT, body BLOB)")
            connection.commit()
            connection.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            # Multiple commits that each grow the database (causing page 1 header
            # updates in the WAL) without changing sqlite_master.
            for batch_index in range(4):
                connection.executemany(
                    "INSERT INTO notes VALUES (?, ?)",
                    [
                        (batch_index * 10 + index, wal_marker * 120)
                        for index in range(10)
                    ],
                )
                connection.commit()

            with open(database_path, "rb") as file_object:
                database_bytes = file_object.read()
            with open(f"{database_path:s}-wal", "rb") as file_object:
                wal_bytes = file_object.read()
            connection.close()

        main_tracked = _TrackedBytesIO(database_bytes)
        wal_tracked = _TrackedBytesIO(wal_bytes)
        main_result = matcher.MatchFileObject(main_tracked)
        wal_result = matcher.MatchFileObjectWithWAL(
            main_tracked, wal_tracked, main_result
        )
        self.assertEqual(
            main_result.status, sqlite_structure.StructureMatchStatus.NO_MATCH
        )
        self.assertEqual(
            wal_result.status, sqlite_structure.StructureMatchStatus.NO_MATCH
        )
        for start_offset, end_offset in wal_tracked.read_ranges:
            self.assertNotIn(wal_marker, wal_bytes[start_offset:end_offset])


if __name__ == "__main__":
    unittest.main()
