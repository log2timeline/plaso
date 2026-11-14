"""Parser for Microsoft Defender MpEngineDb (mpenginedb.db) files.

The Microsoft Defender antimalware engine keeps a SQLite database, also known as
the MetaVault, in:

  C:\\ProgramData\\Microsoft\\Windows Defender\\Scans\\mpenginedb.db

Every page of the database, and of its Write-Ahead Log (WAL) file, is encrypted
with RC4 using a fixed 256 byte key that is stored in mpengine.dll. The key is
restarted for every page and the first 16 bytes of the SQLite header are
encrypted separately from the bytes following offset 24. The WAL checksums are
calculated over the encrypted page data.
"""

import io
import json
import os
import re
import sqlite3
import struct

from dfdatetime import filetime as dfdatetime_filetime
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager
from plaso.parsers import sqlite


class MpEngineDbAttributePersistContextEventData(events.EventData):
    """Microsoft Defender MpEngineDb attribute persist context event data.

    Attributes:
      context (str): context or tag, such as "ExecutedPENoCert".
      expiration_time (dfdatetime.DateTimeValues): date and time the record
          expires.
      insertion_time (dfdatetime.DateTimeValues): date and time the record was
          inserted.
      path (str): path or key the context applies to.
    """

    DATA_TYPE = "windows:defender:mpenginedb:attribute_persist_context"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.context = None
        self.expiration_time = None
        self.insertion_time = None
        self.path = None


class MpEngineDbBackupProcessInfoEventData(events.EventData):
    """Microsoft Defender MpEngineDb backup process information event data.

    Attributes:
      impacted_namespaces (str): impacted ransomware rollback name spaces.
      instance_time (dfdatetime.DateTimeValues): date and time the record was
          written.
      next_usn (int): next NTFS update sequence number (USN) at the time of the
          backup, which can be correlated with the $UsnJrnl.
      path (str): path of the executable or file.
    """

    DATA_TYPE = "windows:defender:mpenginedb:backup_process_info"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.impacted_namespaces = None
        self.instance_time = None
        self.next_usn = None
        self.path = None


class MpEngineDbFileHashEventData(events.EventData):
    """Microsoft Defender MpEngineDb file hash event data.

    Attributes:
      instance_time (dfdatetime.DateTimeValues): date and time the record was
          written.
      md5_hash (str): MD5 hash of the file.
      mft_entry (int): NTFS master file table (MFT) entry number.
      mft_sequence_number (int): NTFS MFT sequence number.
      sha1_hash (str): SHA-1 hash of the file.
      sha256_hash (str): SHA-256 hash of the file.
      ssdeep_hash (str): ssdeep (CTPH) fuzzy hash of the file.
      usn (int): NTFS update sequence number (USN).
      volume_serial_number (int): volume serial number.
    """

    DATA_TYPE = "windows:defender:mpenginedb:file_hash"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.instance_time = None
        self.md5_hash = None
        self.mft_entry = None
        self.mft_sequence_number = None
        self.sha1_hash = None
        self.sha256_hash = None
        self.ssdeep_hash = None
        self.usn = None
        self.volume_serial_number = None


class MpEngineDbLowFidelityEventData(events.EventData):
    """Microsoft Defender MpEngineDb low fidelity signature hit event data.

    Attributes:
      instance_time (dfdatetime.DateTimeValues): date and time the record was
          written.
      is_synchronous (bool): True if the signature was evaluated synchronously.
      path (str): path of the file or name of the scanned object.
      signature_sequence (int): signature sequence number.
      signature_sha1 (str): SHA-1 of the signature.
    """

    DATA_TYPE = "windows:defender:mpenginedb:low_fidelity"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.instance_time = None
        self.is_synchronous = None
        self.path = None
        self.signature_sequence = None
        self.signature_sha1 = None


class MpEngineDbRollingQueueEventData(events.EventData):
    """Microsoft Defender MpEngineDb rolling queue entry event data.

    Attributes:
      entry_key (str): key of the queue entry, for example a path or an ATT&CK
          technique identifier.
      entry_value (str): value of the queue entry, usually JSON.
      expiration_time (dfdatetime.DateTimeValues): date and time the entry
          expires.
      insertion_time (dfdatetime.DateTimeValues): date and time the entry was
          inserted.
      process_identifier (int): identifier (PID) of the process the entry
          relates to.
      process_image (str): path of the process image the entry relates to.
      process_start_time (dfdatetime.DateTimeValues): date and time the process
          the entry relates to started.
      queue_name (str): name of the rolling queue, for example
          "RQ_RecentExecDropped".
    """

    DATA_TYPE = "windows:defender:mpenginedb:rolling_queue"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.entry_key = None
        self.entry_value = None
        self.expiration_time = None
        self.insertion_time = None
        self.process_identifier = None
        self.process_image = None
        self.process_start_time = None
        self.queue_name = None


class MpEngineDbParser(interface.FileEntryParser):
    """Parser for Microsoft Defender MpEngineDb (mpenginedb.db) files."""

    NAME = "mpenginedb"
    DATA_FORMAT = "Microsoft Defender MpEngineDb (mpenginedb.db) file"

    FILTERS = frozenset([interface.FileNameFileEntryFilter("mpenginedb.db")])

    # The 256 byte RC4 key of Microsoft Defender antimalware engine builds
    # 1.1.25080.5 and 1.1.26100.4, stored in mpengine.dll.
    _RC4_KEY = bytes.fromhex(
        "1e87781b8dbaa844ce69702c0c78b786a3f623b738f5edf9af83530fb3fc54fa"
        "a21eb9cf1331fd0f0da954f687cb9e18279697900e53fb317c9cbce48e23d053"
        "71ecc15951b8f3649d7ca33ed68dc9047e82c9baad9799d0d458cb847ca9ffbe"
        "3c8a775233557dde13a8b14087cc1bc8f10f6ecdd083a959cff84a9d1d50755e"
        "3e191818af23e2293558766d2c07e25712b2ca0b535ed8f6c56ce73d24bdd029"
        "1771861a54b4c285a9a3db7aca6d224aeacd621db9f2a22ed1e9e11d75bed7dc"
        "0ecb0a8e68a2ff1263408dc808dffd164b116774cd0b9b8d05411ed6262e429b"
        "a495676b8398db2f35d3c1b9ced52636f2765e1a95cb7ca4c3ddabddbff38253"
    )

    _SQLITE_SIGNATURE = b"SQLite format 3\x00"

    _MAXIMUM_FILE_SIZE = 512 * 1024 * 1024

    _VALID_PAGE_SIZES = frozenset([512, 1024, 2048, 4096, 8192, 16384, 32768])

    _WAL_HEADER_SIZE = 32
    _WAL_FRAME_HEADER_SIZE = 24
    _WAL_MAGIC_NUMBER = 0x377F0682

    # Windows FILETIME values outside of 1980-01-01 and 2107-01-01 are not
    # timestamps, for example identifiers stored in the same column.
    _FILETIME_MINIMUM = 119600064000000000
    _FILETIME_MAXIMUM = 159793632000000000

    _PROCESS_ID_RE = re.compile(r"pid:(?P<pid>\d+),ProcessStart:(?P<start>\d+)")

    def _CopyFileObjectToBytes(self, file_object):
        """Reads the entire content of a file-like object.

        Args:
          file_object (dfvfs.FileIO): file-like object.

        Returns:
          bytes: data.
        """
        file_object.seek(0, os.SEEK_SET)
        return file_object.read(file_object.get_size())

    def _CreateFiletime(self, value):
        """Creates a FILETIME date and time values object.

        Args:
          value (int): FILETIME timestamp.

        Returns:
          dfdatetime.Filetime: date and time values or None if the value is not
              a plausible timestamp.
        """
        if (
            not isinstance(value, int)
            or value < self._FILETIME_MINIMUM
            or value >= self._FILETIME_MAXIMUM
        ):
            return None

        return dfdatetime_filetime.Filetime(timestamp=value)

    def _DecryptDatabase(self, database_data, wal_data):
        """Decrypts a database and applies the committed frames of its WAL.

        Args:
          database_data (bytes): encrypted database data.
          wal_data (bytes): encrypted WAL data or None.

        Returns:
          bytes: decrypted SQLite database without a WAL.

        Raises:
          WrongParser: if the database cannot be decrypted with the known key.
        """
        if len(database_data) < 100:
            raise errors.WrongParser("File too small to be a SQLite database")

        page_size = struct.unpack(">H", database_data[16:18])[0]
        if page_size == 1:
            page_size = 65536
        if page_size not in self._VALID_PAGE_SIZES:
            raise errors.WrongParser(f"Unsupported page size: {page_size:d}")

        key_stream = self._GetKeyStream(page_size)

        header_data = self._XorData(database_data[:16], key_stream[:16])
        if header_data != self._SQLITE_SIGNATURE:
            raise errors.WrongParser(
                "Unsupported database, not encrypted with a known key"
            )

        number_of_pages = len(database_data) // page_size
        pages = {}
        for page_number in range(1, number_of_pages + 1):
            page_offset = (page_number - 1) * page_size
            pages[page_number] = self._DecryptPage(
                database_data[page_offset : page_offset + page_size],
                page_number,
                key_stream,
            )

        database_size = number_of_pages
        if wal_data:
            wal_database_size = self._ApplyWriteAheadLog(
                wal_data, page_size, key_stream, pages
            )
            if wal_database_size:
                database_size = wal_database_size

        empty_page = bytes(page_size)
        decrypted_data = bytearray(
            b"".join(
                pages.get(index, empty_page) for index in range(1, database_size + 1)
            )
        )

        # Reset the file format write and read versions, from WAL to legacy, since
        # the WAL has been applied.
        decrypted_data[18] = 1
        decrypted_data[19] = 1

        return bytes(decrypted_data)

    def _ApplyWriteAheadLog(self, wal_data, page_size, key_stream, pages):
        """Applies the committed frames of a WAL to decrypted pages.

        Args:
          wal_data (bytes): encrypted WAL data.
          page_size (int): database page size.
          key_stream (bytes): RC4 key stream.
          pages (dict[int, bytes]): decrypted pages per page number, which will
              be updated.

        Returns:
          int: size of the database in pages after the last commit or None if
              the WAL has no valid committed frames.
        """
        if len(wal_data) < self._WAL_HEADER_SIZE:
            return None

        magic, _, wal_page_size, _, salt1, salt2, checksum1, checksum2 = struct.unpack(
            ">8I", wal_data[: self._WAL_HEADER_SIZE]
        )
        if magic & ~1 != self._WAL_MAGIC_NUMBER or wal_page_size != page_size:
            return None

        big_endian = bool(magic & 1)

        sum1, sum2 = self._CalculateWalChecksum(wal_data[:24], 0, 0, big_endian)
        if (sum1, sum2) != (checksum1, checksum2):
            return None

        database_size = None
        pending_pages = {}
        frame_size = self._WAL_FRAME_HEADER_SIZE + page_size
        frame_offset = self._WAL_HEADER_SIZE

        while frame_offset + frame_size <= len(wal_data):
            frame_header = wal_data[
                frame_offset : frame_offset + self._WAL_FRAME_HEADER_SIZE
            ]
            frame_data = wal_data[
                frame_offset + self._WAL_FRAME_HEADER_SIZE : frame_offset + frame_size
            ]

            (
                page_number,
                commit_size,
                frame_salt1,
                frame_salt2,
                frame_sum1,
                frame_sum2,
            ) = struct.unpack(">6I", frame_header)
            if (frame_salt1, frame_salt2) != (salt1, salt2):
                break

            # The checksum covers the encrypted frame data.
            sum1, sum2 = self._CalculateWalChecksum(
                frame_header[:8], sum1, sum2, big_endian
            )
            sum1, sum2 = self._CalculateWalChecksum(frame_data, sum1, sum2, big_endian)
            if (sum1, sum2) != (frame_sum1, frame_sum2):
                break

            pending_pages[page_number] = frame_data

            if commit_size:
                for pending_number, pending_data in pending_pages.items():
                    pages[pending_number] = self._DecryptPage(
                        pending_data, pending_number, key_stream
                    )
                pending_pages = {}
                database_size = commit_size

            frame_offset += frame_size

        return database_size

    def _CalculateWalChecksum(self, data, sum1, sum2, big_endian):
        """Calculates a SQLite WAL checksum.

        Args:
          data (bytes): data to checksum, with a size that is a multiple of 8.
          sum1 (int): first checksum value so far.
          sum2 (int): second checksum value so far.
          big_endian (bool): True if the words are in big-endian byte order.

        Returns:
          tuple[int, int]: updated checksum values.
        """
        format_string = ">" if big_endian else "<"
        values = struct.unpack(f"{format_string}{len(data) // 4:d}I", data)
        for index in range(0, len(values), 2):
            sum1 = (sum1 + values[index] + sum2) & 0xFFFFFFFF
            sum2 = (sum2 + values[index + 1] + sum1) & 0xFFFFFFFF

        return sum1, sum2

    def _DecryptPage(self, page_data, page_number, key_stream):
        """Decrypts a database page.

        The RC4 key stream is restarted for every page. In the first page the
        bytes 16 to 23, which contain the page size and format versions, are not
        encrypted and the key stream restarts at offset 24.

        Args:
          page_data (bytes): encrypted page data.
          page_number (int): page number, where the first page is 1.
          key_stream (bytes): RC4 key stream.

        Returns:
          bytes: decrypted page data.
        """
        if page_number != 1:
            return self._XorData(page_data, key_stream)

        return (
            self._XorData(page_data[:16], key_stream[:16])
            + page_data[16:24]
            + self._XorData(page_data[24:], key_stream)
        )

    def _GetKeyStream(self, size):
        """Generates the RC4 key stream.

        Args:
          size (int): number of key stream bytes.

        Returns:
          bytes: key stream.
        """
        key = self._RC4_KEY
        state = list(range(256))
        index2 = 0
        for index1 in range(256):
            index2 = (index2 + state[index1] + key[index1 % len(key)]) & 0xFF
            state[index1], state[index2] = state[index2], state[index1]

        key_stream = bytearray(size)
        index1 = index2 = 0
        for offset in range(size):
            index1 = (index1 + 1) & 0xFF
            index2 = (index2 + state[index1]) & 0xFF
            state[index1], state[index2] = state[index2], state[index1]
            key_stream[offset] = state[(state[index1] + state[index2]) & 0xFF]

        return bytes(key_stream)

    def _OpenWriteAheadLog(self, file_entry):
        """Opens the WAL file that belongs to a database file entry.

        Args:
          file_entry (dfvfs.FileEntry): file entry of the database.

        Returns:
          bytes: WAL data or None if not available.
        """
        path_spec = file_entry.path_spec
        location = getattr(path_spec, "location", None)
        if not location:
            return None

        file_system = file_entry.GetFileSystem()
        wal_path_spec = path_spec_factory.Factory.NewPathSpec(
            file_system.type_indicator,
            parent=path_spec.parent,
            location=f"{location}-wal",
        )
        wal_file_entry = file_system.GetFileEntryByPathSpec(wal_path_spec)
        if not wal_file_entry:
            return None

        wal_file_object = wal_file_entry.GetFileObject()
        if not wal_file_object:
            return None

        if wal_file_object.get_size() > self._MAXIMUM_FILE_SIZE:
            return None

        return self._CopyFileObjectToBytes(wal_file_object)

    def _ParseAttributePersistContext(self, parser_mediator, database):
        """Parses the AttributePersistContext table.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          database (SQLiteDatabase): database.
        """
        for row in self._QueryTable(
            parser_mediator,
            database,
            "AttributePersistContext",
            "SELECT FilePath, Context, InsertTime, ExpireTime "
            "FROM AttributePersistContext",
        ):
            event_data = MpEngineDbAttributePersistContextEventData()
            event_data.context = row["Context"]
            event_data.expiration_time = self._CreateFiletime(row["ExpireTime"])
            event_data.insertion_time = self._CreateFiletime(row["InsertTime"])
            event_data.path = row["FilePath"]

            parser_mediator.ProduceEventData(event_data)

    def _ParseBackupProcessInfo(self, parser_mediator, database):
        """Parses the BackupProcessInfo table.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          database (SQLiteDatabase): database.
        """
        for row in self._QueryTable(
            parser_mediator,
            database,
            "BackupProcessInfo",
            "SELECT FilePath, NextUSN, ImpactedCBPNameSpaces, InstanceTimeStamp "
            "FROM BackupProcessInfo",
        ):
            event_data = MpEngineDbBackupProcessInfoEventData()
            event_data.impacted_namespaces = row["ImpactedCBPNameSpaces"] or None
            event_data.instance_time = self._CreateFiletime(row["InstanceTimeStamp"])
            event_data.next_usn = row["NextUSN"]
            event_data.path = row["FilePath"]

            parser_mediator.ProduceEventData(event_data)

    def _ParseFileHashes(self, parser_mediator, database):
        """Parses the FileHashes table.

        Note that Microsoft Defender stores the MD5 hash in the column named
        SHA1 and the SHA-1 hash in the column named MD5.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          database (SQLiteDatabase): database.
        """
        for row in self._QueryTable(
            parser_mediator,
            database,
            "FileHashes",
            "SELECT VSN, FileID, USN, InstanceTimeStamp, SHA1, MD5, SHA256, CTPH "
            "FROM FileHashes",
        ):
            event_data = MpEngineDbFileHashEventData()
            event_data.instance_time = self._CreateFiletime(row["InstanceTimeStamp"])
            event_data.md5_hash = self._GetHexadecimalString(row["SHA1"])
            event_data.sha1_hash = self._GetHexadecimalString(row["MD5"])
            event_data.sha256_hash = self._GetHexadecimalString(row["SHA256"])
            event_data.usn = row["USN"]

            file_identifier = row["FileID"]
            if isinstance(file_identifier, int):
                file_identifier &= 0xFFFFFFFFFFFFFFFF
                event_data.mft_entry = file_identifier & 0xFFFFFFFFFFFF
                event_data.mft_sequence_number = file_identifier >> 48

            ctph = row["CTPH"]
            if isinstance(ctph, bytes):
                event_data.ssdeep_hash = (
                    ctph.rstrip(b"\x00").decode("ascii", errors="backslashreplace")
                    or None
                )

            volume_serial_number = row["VSN"]
            if isinstance(volume_serial_number, int):
                event_data.volume_serial_number = volume_serial_number & 0xFFFFFFFF

            parser_mediator.ProduceEventData(event_data)

    def _ParseFileLowFidelity(self, parser_mediator, database):
        """Parses the FileLowFiAsync table.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          database (SQLiteDatabase): database.
        """
        for row in self._QueryTable(
            parser_mediator,
            database,
            "FileLowFiAsync",
            "SELECT FileName, SigSeq, SigSha, SigIsSync, InstanceTimeStamp "
            "FROM FileLowFiAsync",
        ):
            event_data = MpEngineDbLowFidelityEventData()
            event_data.instance_time = self._CreateFiletime(row["InstanceTimeStamp"])
            event_data.is_synchronous = (
                None if row["SigIsSync"] is None else bool(row["SigIsSync"])
            )
            event_data.path = row["FileName"]
            event_data.signature_sequence = row["SigSeq"]
            event_data.signature_sha1 = self._GetHexadecimalString(row["SigSha"])

            parser_mediator.ProduceEventData(event_data)

    def _ParseRollingQueues(self, parser_mediator, database):
        """Parses the RollingQueuesValues table.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          database (SQLiteDatabase): database.
        """
        for row in self._QueryTable(
            parser_mediator,
            database,
            "RollingQueuesValues",
            "SELECT EntryTable, EntryKey, EntryValue, InsertTime, ExpireTime "
            "FROM RollingQueuesValues",
        ):
            event_data = MpEngineDbRollingQueueEventData()
            event_data.entry_key = row["EntryKey"]
            event_data.entry_value = row["EntryValue"]
            event_data.expiration_time = self._CreateFiletime(row["ExpireTime"])
            event_data.insertion_time = self._CreateFiletime(row["InsertTime"])
            event_data.queue_name = row["EntryTable"]

            # Per process queues are named or keyed "pid:<PID>,ProcessStart:<FILETIME>"
            # and the entry value can contain the same process reference.
            process_reference = None
            for value in (row["EntryTable"], row["EntryKey"]):
                if isinstance(value, str):
                    process_reference = self._PROCESS_ID_RE.search(value)
                    if process_reference:
                        break

            entry_value = row["EntryValue"]
            if isinstance(entry_value, str) and entry_value[:1] == "{":
                json_value = self._ParseJson(entry_value)
                if isinstance(json_value, dict):
                    process_image = json_value.get("Process_Img")
                    if isinstance(process_image, str):
                        event_data.process_image = process_image

                    process_id = json_value.get("ProcessId")
                    if not process_reference and isinstance(process_id, str):
                        process_reference = self._PROCESS_ID_RE.search(process_id)

            if process_reference:
                event_data.process_identifier = int(process_reference.group("pid"))
                event_data.process_start_time = self._CreateFiletime(
                    int(process_reference.group("start"))
                )

            parser_mediator.ProduceEventData(event_data)

    def _ParseJson(self, value):
        """Parses a JSON string.

        Args:
          value (str): JSON string.

        Returns:
          object: parsed JSON or None if the string is not valid JSON, for
              example because it was truncated.
        """
        try:
            return json.loads(value)
        except ValueError:
            return None

    def _GetHexadecimalString(self, value):
        """Converts a binary value into a lower case hexadecimal string.

        Args:
          value (bytes): binary value.

        Returns:
          str: hexadecimal string or None if the value is empty.
        """
        if not isinstance(value, bytes) or not value:
            return None

        return value.hex()

    def _QueryTable(self, parser_mediator, database, table_name, query):
        """Queries a table of the database, if it exists.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          database (SQLiteDatabase): database.
          table_name (str): name of the table.
          query (str): SQL query.

        Yields:
          sqlite3.Row: rows of the query result.
        """
        if table_name not in database.tables:
            return

        try:
            rows = database.Query(query).fetchall()
        except sqlite3.DatabaseError as exception:
            parser_mediator.ProduceWarning(
                f"unable to query table: {table_name:s} with error: {exception!s}"
            )
            return

        yield from rows

    def _XorData(self, data, key_stream):
        """Exclusive ORs data with the start of a key stream.

        Args:
          data (bytes): data.
          key_stream (bytes): key stream, which is at least as large as the data.

        Returns:
          bytes: data XOR key stream.
        """
        size = len(data)
        value = int.from_bytes(data, "big") ^ int.from_bytes(key_stream[:size], "big")
        return value.to_bytes(size, "big")

    def ParseFileEntry(self, parser_mediator, file_entry):
        """Parses a Microsoft Defender MpEngineDb file entry.

        Args:
          parser_mediator (ParserMediator): parser mediator.
          file_entry (dfvfs.FileEntry): file entry.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        file_object = file_entry.GetFileObject()
        if not file_object:
            raise errors.WrongParser("Unable to open file")

        file_size = file_object.get_size()
        if file_size == 0:
            return

        if file_size > self._MAXIMUM_FILE_SIZE:
            raise errors.WrongParser(f"File size: {file_size:d} too large")

        database_data = self._CopyFileObjectToBytes(file_object)
        wal_data = self._OpenWriteAheadLog(file_entry)

        decrypted_data = self._DecryptDatabase(database_data, wal_data)

        database = sqlite.SQLiteDatabase(
            file_entry.name, temporary_directory=parser_mediator.temporary_directory
        )

        try:
            database.Open(io.BytesIO(decrypted_data))
        except (OSError, ValueError, sqlite3.DatabaseError) as exception:
            raise errors.WrongParser(
                f"Unable to open decrypted database with error: {exception!s}"
            ) from exception

        try:
            self._ParseAttributePersistContext(parser_mediator, database)
            self._ParseBackupProcessInfo(parser_mediator, database)
            self._ParseFileHashes(parser_mediator, database)
            self._ParseFileLowFidelity(parser_mediator, database)
            self._ParseRollingQueues(parser_mediator, database)

        finally:
            database.Close()


manager.ParsersManager.RegisterParser(MpEngineDbParser)
