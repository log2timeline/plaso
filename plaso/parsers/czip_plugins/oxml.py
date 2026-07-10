"""Compound ZIP parser plugin for OpenXML files."""

import re
import zipfile

from xml.parsers import expat

from defusedxml import ElementTree

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import czip
from plaso.parsers.czip_plugins import interface


class OpenXMLEventData(events.EventData):
    """OXML event data.

    Attributes:
      application (str): name of application that created document.
      application_version (str): version of application that created document.
      author (str): name of author.
      creation_time (dfdatetime.DateTimeValues): creation date and time of the document.
      digital_signature (str): digital signature.
      edit_duration (int): total editing time.
      hyperlinks_changed (bool): True if hyperlinks have changed.
      last_printed_time (dfdatetime.DateTimeValues): date and time the document was last
          printed.
      last_saved_by (str): name of user that last saved the document.
      links_up_to_date (bool): True if the links are up to date.
      modification_time (dfdatetime.DateTimeValues): modification date and time of the
          document.
      number_of_characters (int): number of characters without spaces in the document.
      number_of_characters_with_spaces (int): number of characters including spaces in
          the document.
      number_of_clips (int): number of multi-media clips in the document.
      number_of_hidden_slides (int): number of hidden slides in the document.
      number_of_lines (int): number of lines in the document.
      number_of_pages (int): number of pages in the document.
      number_of_paragraphs (int): number of paragraphs in the document.
      number_of_slides (int): number of slides in the document.
      number_of_words (int): number of words in the document.
      revision_number (int): revision number.
      scale (bool): True if scaling of the thumbnail is desired or false if cropping is
          desired.
      security_flags (int): security flags.
      shared_doc (bool): True if document is shared.
      template (str): name of the template used to created the document.
    """

    DATA_TYPE = "openxml:metadata"

    def __init__(self):
        """Initializes event data."""
        super().__init__(data_type=self.DATA_TYPE)
        self.application = None
        self.application_version = None
        self.author = None
        self.creation_time = None
        self.digital_signature = None
        self.edit_duration = None
        self.hyperlinks_changed = None
        self.last_printed_time = None
        self.last_saved_by = None
        self.links_up_to_date = None
        self.modification_time = None
        self.number_of_characters = None
        self.number_of_characters_with_spaces = None
        self.number_of_clips = None
        self.number_of_hidden_slides = None
        self.number_of_lines = None
        self.number_of_pages = None
        self.number_of_paragraphs = None
        self.number_of_slides = None
        self.number_of_words = None
        self.revision_number = None
        self.scale = None
        self.security_flags = None
        self.shared_doc = None
        self.template = None


class OpenXMLPlugin(interface.CompoundZIPPlugin):
    """Parse metadata from OXML files."""

    NAME = "oxml"
    DATA_FORMAT = "OpenXML (OXML) file"

    REQUIRED_PATHS = frozenset(
        ["[Content_Types].xml", "_rels/.rels", "docProps/core.xml"]
    )

    _PROPERTY_NAMES = {
        "creator": "author",
        "lastModifiedBy": "last_saved_by",
        "Total_Time": "total_edit_time",
        "Pages": "number_of_pages",
        "CharactersWithSpaces": "number_of_characters_with_spaces",
        "Paragraphs": "number_of_paragraphs",
        "Characters": "number_of_characters",
        "Lines": "number_of_lines",
        "revision": "revision_number",
        "Words": "number_of_words",
        "Application": "application",
        "Shared_Doc": "shared",
    }

    _BINARY_VALUE_NAMES = frozenset(
        [
            "application",
            "app_version",
            "author",
            "dig_sig",
            "last_saved_by",
            "shared_doc",
            "template",
        ]
    )

    _BOOLEAN_VALUE_NAMES = frozenset(
        ["hyperlinks_changed", "links_up_to_date", "scale_crop"]
    )

    _INTEGER_VALUE_NAMES = frozenset(
        [
            "doc_security",
            "hidden_slides",
            "i4",
            "mm_clips",
            "number_of_characters",
            "number_of_characters_with_spaces",
            "number_of_lines",
            "number_of_pages",
            "number_of_paragraphs",
            "number_of_words",
            "revision_number",
            "slides",
            "total_time",
        ]
    )

    _ISO8601_STRING_VALUES = frozenset(["created", "last_printed", "modified"])

    def _FormatPropertyName(self, name):
        """Formats a camel case property name as snake case.

        Args:
          name (str): property name in camel case.

        Returns:
          str: property name in snake case.
        """
        # TODO: Add Unicode support.
        fix_key = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", fix_key).lower()

    def _ParsePropertiesXMLFile(self, parser_mediator, xml_data):
        """Parses a properties XML file.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          xml_data (bytes): data of a _rels/.rels XML file.

        Returns:
          tuple: containing:

              dict[str, object]: properties.
              bool: value to indicate the ISO8601 date and time string was corrupted.

        Raises:
          zipfile.BadZipfile: if the properties XML file cannot be read.
        """
        corrupted = False
        properties = {}

        xml_root = ElementTree.fromstring(xml_data)
        for xml_element in xml_root.iter():
            if not xml_element.text:
                continue

            # The property name is formatted as: {URL}name
            # For example: {http://purl.org/dc/terms/}modified
            _, _, name = xml_element.tag.partition("}")

            # Do not including the 'lpstr' attribute because it is very verbose.
            if name == "lpstr":
                continue

            property_name = self._PROPERTY_NAMES.get(name)
            if not property_name:
                property_name = self._FormatPropertyName(name)

            property_value = xml_element.text
            if property_value in (None, b"", ""):
                property_value = None

            elif property_name in self._BINARY_VALUE_NAMES:
                if isinstance(property_value, bytes):
                    try:
                        # TODO: get encoding form XML metadata.
                        property_value = property_value.decode("utf-8")
                    except UnicodeDecodeError:
                        parser_mediator.ProduceWarning(
                            f"Unable to decode property value: {property_name:s} as "
                            f"UTF-8. Unsupported code points are escaped."
                        )
                        property_value = property_value.decode(
                            "utf-8", errors="backslashreplace"
                        )
                        corrupted = True

            elif property_name in self._BOOLEAN_VALUE_NAMES:
                if property_value == "false":
                    property_value = False
                elif property_value == "true":
                    property_value = True
                else:
                    parser_mediator.ProduceWarning(
                        f"Unable to parse boolean value: {property_name:s}"
                    )
                    property_value = None
                    corrupted = True

            elif property_name in self._INTEGER_VALUE_NAMES:
                try:
                    property_value = int(property_value, 10)
                except (TypeError, ValueError):
                    parser_mediator.ProduceWarning(
                        f"Unable to parse integer value: {property_name:s}"
                    )
                    property_value = None
                    corrupted = True

            elif property_name in self._ISO8601_STRING_VALUES:
                # Date and time strings are in ISO8601 format either with 1 second
                # or 100th nano second precision. For example:
                # 2012-11-07T23:29:00Z
                # 2012-03-05T20:40:00.0000000Z
                date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()

                try:
                    date_time.CopyFromStringISO8601(property_value)
                except ValueError as exception:
                    parser_mediator.ProduceWarning(
                        f"Unable to parse ISO8601 string value: {property_name:s} "
                        f"with error: {exception!s}"
                    )
                    date_time = None
                    corrupted = True

                property_value = date_time

            properties[property_name] = property_value

        return properties, corrupted

    def _ParseRelationshipsXMLFile(self, xml_data):
        """Parses the relationships XML file (_rels/.rels).

        Args:
          xml_data (bytes): data of a _rels/.rels XML file.

        Returns:
          list[str]: property file paths. The path is relative to the root of
              the ZIP file.

        Raises:
          zipfile.BadZipfile: if the relationship XML file cannot be read.
        """
        xml_root = ElementTree.fromstring(xml_data)

        property_files = []
        for xml_element in xml_root.iter():
            type_attribute = xml_element.get("Type")
            if "properties" in repr(type_attribute):
                target_attribute = xml_element.get("Target")
                property_files.append(target_attribute)

        return property_files

    def _ParseZIPFile(self, parser_mediator, zip_file):
        """Parses an OXML file-like object.

        Args:
          parser_mediator (ParserMediator): mediates interactions between parsers and
              other components, such as storage and dfVFS.
          zip_file (zipfile.ZipFile): the zip file containing OXML content. It is
              not be closed in this method, but will be closed by the parser logic
               in czip.py.
        """
        try:
            xml_data = zip_file.read("_rels/.rels")
            property_files = self._ParseRelationshipsXMLFile(xml_data)
        except (
            IndexError,
            KeyError,
            LookupError,
            OSError,
            OverflowError,
            ValueError,
            ElementTree.ParseError,
            expat.ExpatError,
            zipfile.BadZipfile,
        ) as exception:
            parser_mediator.ProduceWarning(
                f"Unable to parse relationships XML file: _rels/.rels with error: "
                f"{exception!s}"
            )
            return

        corrupted = False
        metadata = {}

        for path in property_files:
            try:
                xml_data = zip_file.read(path)
                properties, properties_corrupted = self._ParsePropertiesXMLFile(
                    parser_mediator, xml_data
                )
            except (
                IndexError,
                KeyError,
                LookupError,
                OSError,
                OverflowError,
                ValueError,
                ElementTree.ParseError,
                expat.ExpatError,
                zipfile.BadZipfile,
            ) as exception:
                parser_mediator.ProduceWarning(
                    f"Unable to parse properties XML file: {path:s} with error: "
                    f"{exception!s}"
                )
                continue

            metadata.update(properties)
            corrupted = corrupted or properties_corrupted

        event_data = OpenXMLEventData()
        event_data.application = metadata.get("application")
        event_data.application_version = metadata.get("app_version")
        event_data.author = metadata.get("author")
        event_data.creation_time = metadata.get("created")
        event_data.digital_signature = metadata.get("dig_sig")
        event_data.edit_duration = metadata.get("total_time")
        event_data.hyperlinks_changed = metadata.get("hyperlinks_changed")
        # event_data.i4 = metadata.get("i4")
        event_data.last_printed_time = metadata.get("last_printed")
        event_data.last_saved_by = metadata.get("last_saved_by")
        event_data.links_up_to_date = metadata.get("links_up_to_date")
        event_data.modification_time = metadata.get("modified")
        event_data.number_of_characters = metadata.get("number_of_characters")
        event_data.number_of_characters_with_spaces = metadata.get(
            "number_of_characters_with_spaces"
        )
        event_data.number_of_clips = metadata.get("mm_clips")
        event_data.number_of_hidden_slides = metadata.get("hidden_slides")
        event_data.number_of_lines = metadata.get("number_of_lines")
        event_data.number_of_pages = metadata.get("number_of_pages")
        event_data.number_of_paragraphs = metadata.get("number_of_paragraphs")
        event_data.number_of_slides = metadata.get("slides")
        event_data.number_of_words = metadata.get("number_of_words")
        event_data.revision_number = metadata.get("revision_number")
        event_data.scale = metadata.get("scale_crop")
        event_data.security_flags = metadata.get("doc_security")
        event_data.shared_doc = metadata.get("shared_doc")
        event_data.template = metadata.get("template")

        parser_mediator.ProduceEventData(event_data, corrupted=corrupted)


czip.CompoundZIPParser.RegisterPlugin(OpenXMLPlugin)
