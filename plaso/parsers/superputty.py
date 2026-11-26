"""Parser for SuperPuTTY sessions (Sessions.XML) files."""

import os
import re

from defusedxml import ElementTree

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class SuperPuTTYSessionEventData(events.EventData):
    """SuperPuTTY session event data.

    Attributes:
      extra_arguments (str): extra PuTTY command line arguments, provided by
          the ExtraArgs attribute.
      hostname (str): host name or IP address, provided by the Host attribute.
      local_path (str): local path used in file transfers, provided by
          the LocalPath attribute.
      port_number (int): port number, provided by the Port attribute.
      protocol (str): protocol, such as "SSH" or "Telnet", provided by the Proto
          attribute.
      putty_session (str): name of the PuTTY session profile, provided by
          the PuttySession attribute.
      remote_path (str): remote path used in file transfers, provided by
          the RemotePath attribute.
      session_identifier (str): session identifier, which consists of the folder
          path and name of the session, such as "Folder/Name", provided by
          the SessionId attribute.
      session_name (str): session name, provided by the SessionName attribute.
      username (str): username, provided by the Username attribute.
    """

    DATA_TYPE = "superputty:session"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.extra_arguments = None
        self.hostname = None
        self.local_path = None
        self.port_number = None
        self.protocol = None
        self.putty_session = None
        self.remote_path = None
        self.session_identifier = None
        self.session_name = None
        self.username = None


class SuperPuTTYSessionsFileEntryFilter(interface.BaseFileEntryFilter):
    """File entry filter for SuperPuTTY sessions (Sessions.XML) files."""

    # SuperPuTTY stores its sessions in Sessions.XML and keeps backups of
    # previous versions named Sessions.{yyyyMMdd_hhmmss}.XML in the same folder.
    _FILENAME_RE = re.compile(
        r"^Sessions(?:[.][0-9]{8}_[0-9]{6})?[.]XML$", flags=re.IGNORECASE
    )

    def Match(self, file_entry):
        """Determines if a file entry is a SuperPuTTY sessions file.

        Args:
          file_entry (dfvfs.FileEntry): file entry.

        Returns:
          bool: True if the file entry matches the filter.
        """
        if not file_entry:
            return False

        return bool(self._FILENAME_RE.match(file_entry.name))


class SuperPuTTYSessionsParser(interface.FileObjectParser):
    """Parser for SuperPuTTY sessions (Sessions.XML) files."""

    NAME = "superputty_sessions"
    DATA_FORMAT = "SuperPuTTY sessions (Sessions.XML) file"

    FILTERS = frozenset([SuperPuTTYSessionsFileEntryFilter()])

    _HEADER_READ_SIZE = 512

    _MAXIMUM_FILE_SIZE = 16 * 1024 * 1024

    _ROOT_ELEMENT_NAME = "ArrayOfSessionData"

    _UTF8_BYTE_ORDER_MARK = b"\xef\xbb\xbf"

    def _CheckHeader(self, file_object):
        """Checks if the file-like object starts with a SuperPuTTY sessions header.

        Args:
          file_object (dfvfs.FileIO): file-like object.

        Returns:
          bool: True if the file-like object starts with an XML declaration
              followed by the ArrayOfSessionData root element.
        """
        file_object.seek(0, os.SEEK_SET)
        data = file_object.read(self._HEADER_READ_SIZE)

        data = data.removeprefix(self._UTF8_BYTE_ORDER_MARK)
        if not data.startswith(b"<?xml"):
            return False

        _, _, data = data.partition(b"?>")
        root_element_start = f"<{self._ROOT_ELEMENT_NAME:s}".encode("ascii")
        if not data.lstrip().startswith(root_element_start):
            return False

        return True

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a SuperPuTTY sessions file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        if not self._CheckHeader(file_object):
            raise errors.WrongParser(
                "Not a SuperPuTTY sessions file [missing XML root element]"
            )

        file_size = file_object.get_size()
        if file_size > self._MAXIMUM_FILE_SIZE:
            parser_mediator.ProduceWarning(
                f"unsupported file size: {file_size:d} exceeds maximum: "
                f"{self._MAXIMUM_FILE_SIZE:d}"
            )
            return

        # The current offset of the file-like object needs to point at the start of
        # the file for ElementTree to parse the XML data correctly.
        file_object.seek(0, os.SEEK_SET)

        # LookupError is raised for an unsupported XML encoding and ValueError,
        # by defusedxml, for forbidden XML constructs such as entities.
        try:
            xml = ElementTree.parse(file_object)
        except (ElementTree.ParseError, LookupError, ValueError) as exception:
            parser_mediator.ProduceWarning(
                f"unable to parse XML with error: {exception!s}"
            )
            return

        root_node = xml.getroot()
        if root_node.tag != self._ROOT_ELEMENT_NAME:
            raise errors.WrongParser(
                f"Not a SuperPuTTY sessions file [unsupported XML root element: "
                f"{root_node.tag!s}]"
            )

        for session_node in root_node.iterfind("SessionData"):
            corrupted = False

            port_number = session_node.get("Port")
            if port_number is not None:
                try:
                    port_number = int(port_number, 10)
                except ValueError:
                    parser_mediator.ProduceWarning(
                        f"unsupported port number: {port_number:s}"
                    )
                    port_number = None
                    corrupted = True

            event_data = SuperPuTTYSessionEventData()
            event_data.extra_arguments = session_node.get("ExtraArgs") or None
            event_data.hostname = session_node.get("Host") or None
            event_data.local_path = session_node.get("LocalPath") or None
            event_data.port_number = port_number
            event_data.protocol = session_node.get("Proto") or None
            event_data.putty_session = session_node.get("PuttySession") or None
            event_data.remote_path = session_node.get("RemotePath") or None
            event_data.session_identifier = session_node.get("SessionId") or None
            event_data.session_name = session_node.get("SessionName") or None
            event_data.username = session_node.get("Username") or None

            parser_mediator.ProduceEventData(event_data, corrupted=corrupted)


manager.ParsersManager.RegisterParser(SuperPuTTYSessionsParser)
