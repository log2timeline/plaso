"""Multi-processing related functions and classes for testing."""

import ctypes
import multiprocessing

from plaso.parsers import mediator as parsers_mediator
from plaso.storage.fake import writer as fake_writer

from tests import test_lib as shared_test_lib


class TestProcess:
    """Stand-in for a worker process that does not start a real process.

    Attributes:
      name (str): process name.
      pid (int): process identifier (PID).
      rpc_port (multiprocessing.Value): port number of the RPC server.
      terminated (bool): True if the process was terminated.
    """

    # The method names match those of multiprocessing.Process.
    # pylint: disable=invalid-name

    def __init__(self, name, pid, alive=True, rpc_port=1):
        """Initializes a stand-in process.

        Args:
          name (str): process name.
          pid (int): process identifier (PID).
          alive (Optional[bool]): True if the process is alive.
          rpc_port (Optional[int]): port number of the RPC server.
        """
        super().__init__()
        self._is_alive = alive
        self.name = name
        self.pid = pid
        self.rpc_port = multiprocessing.Value(ctypes.c_uint16, rpc_port)
        self.terminated = False

    def is_alive(self):
        """Determines if the process is alive.

        Returns:
          bool: True if the process is alive.
        """
        return self._is_alive

    def join(self, timeout=None):  # pylint: disable=unused-argument
        """Waits for the process to stop.

        Args:
          timeout (Optional[float]): number of seconds to wait.
        """
        return

    def terminate(self):
        """Terminates the process."""
        self._is_alive = False
        self.terminated = True


class MultiProcessingTestCase(shared_test_lib.BaseTestCase):
    """Multi-processing test case."""

    def _CreateParserMediator(self, storage_writer, file_entry=None, parser_chain=None):
        """Creates a parser mediator.

        Args:
          storage_writer (StorageWriter): storage writer.
          file_entry (Optional[dfvfs.FileEntry]): file entry object being parsed.
          parser_chain (Optional[str]): parsing chain up to this point.

        Returns:
          ParserMediator: parser mediator.
        """
        parser_mediator = parsers_mediator.ParserMediator()

        parser_mediator.SetStorageWriter(storage_writer)

        if file_entry:
            parser_mediator.SetFileEntry(file_entry)

        if parser_chain:
            parser_mediator.parser_chain = parser_chain

        return parser_mediator

    def _CreateStorageWriter(self):
        """Creates a storage writer object.

        Returns:
          FakeStorageWriter: storage writer.
        """
        storage_writer = fake_writer.FakeStorageWriter()
        storage_writer.Open()
        return storage_writer
