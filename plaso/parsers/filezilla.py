"""Parser for FileZilla site manager (sitemanager.xml) files."""

import os

from defusedxml import ElementTree

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class FileZillaSiteManagerSiteEventData(events.EventData):
    """FileZilla site manager site event data.

    Attributes:
      comments (str): comments of the site.
      folder_path (str): path of the site manager folder that contains the site,
          where the folder names are separated by "/", or None if the site is
          not stored in a folder.
      hostname (str): host name or IP address of the server.
      key_file (str): path of the SSH private key file used to log on to
          the server.
      local_directory (str): default local directory.
      logon_type (int): logon type.
      name (str): name of the site.
      port_number (int): port number of the server.
      protocol (int): protocol.
      remote_directory (str): default remote directory, in the FileZilla
          serialized remote path format.
      username (str): username used to log on to the server.
    """

    DATA_TYPE = "filezilla:site_manager:site"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.comments = None
        self.folder_path = None
        self.hostname = None
        self.key_file = None
        self.local_directory = None
        self.logon_type = None
        self.name = None
        self.port_number = None
        self.protocol = None
        self.remote_directory = None
        self.username = None


class FileZillaSiteManagerParser(interface.FileObjectParser):
    """Parses FileZilla site manager (sitemanager.xml) files."""

    NAME = "filezilla_sitemanager"
    DATA_FORMAT = "FileZilla site manager (sitemanager.xml) file"

    _HEADER_READ_SIZE = 256

    _MAXIMUM_FILE_SIZE = 16 * 1024 * 1024

    _UTF8_BYTE_ORDER_MARK = b"\xef\xbb\xbf"

    def _GetElementText(self, element, tag):
        """Retrieves the text of a sub element.

        Args:
          element (xml.etree.ElementTree.Element): element.
          tag (str): tag of the sub element.

        Returns:
          str: text of the sub element or None if not available or empty.
        """
        sub_element = element.find(tag)
        if sub_element is None:
            return None

        return sub_element.text or None

    def _GetElementInteger(self, parser_mediator, element, tag):
        """Retrieves the integer value of a sub element.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          element (xml.etree.ElementTree.Element): element.
          tag (str): tag of the sub element.

        Returns:
          int: integer value of the sub element or None if not available or not
              an integer.
        """
        text = self._GetElementText(element, tag)
        if text is None:
            return None

        try:
            return int(text, 10)
        except ValueError:
            parser_mediator.ProduceWarning(f"unsupported {tag:s} value: {text:s}")
            return None

    def _GetServerName(self, server_element):
        """Retrieves the name of a server.

        Older versions of FileZilla store the name of the site as text of the
        Server element instead of a Name sub element.

        Args:
          server_element (xml.etree.ElementTree.Element): Server element.

        Returns:
          str: name of the server or None if not available.
        """
        name = self._GetElementText(server_element, "Name")
        if name:
            return name

        text_values = [server_element.text]
        text_values.extend([sub_element.tail for sub_element in server_element])

        for text in text_values:
            text = (text or "").strip()
            if text:
                return text

        return None

    def _ParseServer(self, parser_mediator, server_element, folder_names):
        """Parses a Server element.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers
              and other components, such as storage and dfVFS.
          server_element (xml.etree.ElementTree.Element): Server element.
          folder_names (list[str]): names of the folders that contain the server.
        """
        # Note that the password, stored in the Pass element, is intentionally
        # not extracted.
        event_data = FileZillaSiteManagerSiteEventData()
        event_data.comments = self._GetElementText(server_element, "Comments")
        event_data.folder_path = "/".join(folder_names) or None
        event_data.hostname = self._GetElementText(server_element, "Host")
        event_data.key_file = self._GetElementText(server_element, "Keyfile")
        event_data.local_directory = self._GetElementText(server_element, "LocalDir")
        event_data.logon_type = self._GetElementInteger(
            parser_mediator, server_element, "Logontype"
        )
        event_data.name = self._GetServerName(server_element)
        event_data.port_number = self._GetElementInteger(
            parser_mediator, server_element, "Port"
        )
        event_data.protocol = self._GetElementInteger(
            parser_mediator, server_element, "Protocol"
        )
        event_data.remote_directory = self._GetElementText(server_element, "RemoteDir")
        event_data.username = self._GetElementText(server_element, "User")

        parser_mediator.ProduceEventData(event_data)

    def ParseFileObject(self, parser_mediator, file_object):
        """Parses a FileZilla site manager file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          file_object (dfvfs.FileIO): file-like object.

        Raises:
          WrongParser: when the file cannot be parsed.
        """
        data = file_object.read(self._HEADER_READ_SIZE)
        data = data.removeprefix(self._UTF8_BYTE_ORDER_MARK)
        if not data.startswith(b"<?xml"):
            raise errors.WrongParser("Not a FileZilla site manager file [not XML]")

        _, _, data = data.partition(b"?>")
        if not data.lstrip().startswith(b"<FileZilla3"):
            raise errors.WrongParser(
                "Not a FileZilla site manager file [wrong XML root key]"
            )

        # For ElementTree to work we need to work on a file object with its current
        # offset at the start.
        file_object.seek(0, os.SEEK_SET)

        # LookupError is raised for an unsupported encoding and ValueError for a
        # multi-byte encoding in the XML declaration.
        try:
            xml = ElementTree.parse(file_object)
        except (ElementTree.ParseError, LookupError, ValueError) as exception:
            raise errors.WrongParser(
                f"Unable to parse FileZilla site manager file with error: "
                f"{exception!s}"
            )

        root_element = xml.getroot()
        if root_element.tag != "FileZilla3":
            raise errors.WrongParser(
                "Not a FileZilla site manager file [wrong XML root key]"
            )

        servers_element = root_element.find("Servers")
        if servers_element is None:
            raise errors.WrongParser(
                "Not a FileZilla site manager file [missing Servers element]"
            )

        # Folders are traversed iteratively, in document order, to prevent deeply
        # nested folders from exhausting the recursion limit.
        elements_stack = [(iter(servers_element), [])]
        while elements_stack:
            sub_elements, folder_names = elements_stack[-1]

            sub_element = next(sub_elements, None)
            if sub_element is None:
                elements_stack.pop()

            elif sub_element.tag == "Server":
                self._ParseServer(parser_mediator, sub_element, folder_names)

            elif sub_element.tag == "Folder":
                folder_name = (sub_element.text or "").strip()
                elements_stack.append((iter(sub_element), folder_names + [folder_name]))


manager.ParsersManager.RegisterParser(FileZillaSiteManagerParser)
