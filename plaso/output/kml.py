# -*- coding: utf-8 -*-
"""An output module that writes event with geography data to a KML XML file.

The Keyhole Markup Language (KML) is an XML notation for expressing geographic
annotation and visualization within Internet-based, two-dimensional maps and
three-dimensional Earth browsers.
"""

import codecs

from xml.etree import ElementTree

from plaso.output import interface
from plaso.output import manager
from plaso.output import rawpy


class KMLEventFormattingHelper(rawpy.NativePythonEventFormattingHelper):
  """Keyhole Markup Language (KML) XML event formatting helper."""

  def GetFormattedEvent(self, event, event_data, event_data_stream, event_tag):
    """Retrieves a string representation of the event.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.

    Returns:
      str: string representation of the event.
    """
    event_identifier = event.GetIdentifier()

    description_text = self._GetFormattedEventNativePython(
        event, event_data, event_data_stream, event_tag)

    placemark_xml_element = ElementTree.Element('Placemark')

    name_xml_element = ElementTree.SubElement(placemark_xml_element, 'name')
    name_xml_element.text = event_identifier.CopyToString()

    description_xml_element = ElementTree.SubElement(
        placemark_xml_element, 'description')
    description_xml_element.text = '{0:s}\n'.format(description_text)

    point_xml_element = ElementTree.SubElement(placemark_xml_element, 'Point')

    coordinates_xml_element = ElementTree.SubElement(
        point_xml_element, 'coordinates')
    coordinates_xml_element.text = '{0!s},{1!s}'.format(
        event_data.longitude, event_data.latitude)

    # Note that ElementTree.tostring() will appropriately escape the input data.
    xml_string = ElementTree.tostring(placemark_xml_element)

    return codecs.decode(xml_string, self._output_mediator.encoding)


class KMLOutputModule(interface.TextFileOutputModule):
  """Output module for a Keyhole Markup Language (KML) XML file."""

  NAME = 'kml'
  DESCRIPTION = 'Saves events with geography data into a KML format.'

  def __init__(self, output_mediator):
    """Initializes a Keyhole Markup Language (KML) XML file output module.

    Args:
      output_mediator (OutputMediator): an output mediator.
    """
    event_formatting_helper = KMLEventFormattingHelper(output_mediator)
    super(KMLOutputModule, self).__init__(
        output_mediator, event_formatting_helper)

  def WriteEventBody(self, event, event_data, event_data_stream, event_tag):
    """Writes event values to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
      event_tag (EventTag): event tag.
    """
    latitude = getattr(event_data, 'latitude', None)
    longitude = getattr(event_data, 'longitude', None)
    if None not in (latitude, longitude):
      output_text = self._event_formatting_helper.GetFormattedEvent(
          event, event_data, event_data_stream, event_tag)
      self.WriteText(output_text)

  def WriteHeader(self):
    """Writes the header to the output."""
    xml_string = (
        '<?xml version="1.0" encoding="{0:s}"?>'
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>'.format(
            self._output_mediator.encoding))
    self.WriteText(xml_string)

  def WriteFooter(self):
    """Writes the footer to the output."""
    self.WriteText('</Document></kml>')


manager.OutputManager.RegisterOutput(KMLOutputModule)
