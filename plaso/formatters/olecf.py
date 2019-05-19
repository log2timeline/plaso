# -*- coding: utf-8 -*-
"""The OLE Compound File (OLECF) event formatters."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors
from plaso.lib import py2to3


class OLECFItemFormatter(interface.EventFormatter):
  """Formatter for an OLECF item event."""

  DATA_TYPE = 'olecf:item'

  FORMAT_STRING = 'Name: {name}'
  FORMAT_STRING_SHORT = 'Name: {name}'

  SOURCE_LONG = 'OLECF Item'
  SOURCE_SHORT = 'OLECF'


class OLECFDestListEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OLECF DestList stream event."""

  DATA_TYPE = 'olecf:dest_list:entry'

  FORMAT_STRING_PIECES = [
      'Entry: {entry_number}',
      'Pin status: {pin_status}',
      'Hostname: {hostname}',
      'Path: {path}',
      'Droid volume identifier: {droid_volume_identifier}',
      'Droid file identifier: {droid_file_identifier}',
      'Birth droid volume identifier: {birth_droid_volume_identifier}',
      'Birth droid file identifier: {birth_droid_file_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      'Entry: {entry_number}',
      'Pin status: {pin_status}',
      'Path: {path}']

  # pylint: disable=unused-argument
  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    pin_status = event_values.get('pin_status', 0)
    if pin_status == -1:
      event_values['pin_status'] = 'Unpinned'
    else:
      event_values['pin_status'] = 'Pinned'

    return self._ConditionalFormatMessages(event_values)


class OLECFDocumentSummaryInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OLECF Document Summary Info property set stream event."""

  DATA_TYPE = 'olecf:document_summary_info'

  FORMAT_STRING_PIECES = [
      'Number of bytes: {number_of_bytes}',
      'Number of lines: {number_of_lines}',
      'Number of paragraphs: {number_of_paragraphs}',
      'Number of slides: {number_of_slides}',
      'Number of notes: {number_of_notes}',
      'Number of hidden slides: {number_of_hidden_slides}',
      'Number of multi-media clips: {number_of_clips}',
      'Company: {company}',
      'Manager: {manager}',
      'Shared document: {shared_document}',
      'Application version: {application_version}',
      'Content type: {content_type}',
      'Content status: {content_status}',
      'Language: {language}',
      'Document version: {document_version}']

      # TODO: add support for the following properties.
      # 'Digital signature: {digital_signature}',

  FORMAT_STRING_SHORT_PIECES = [
      'Company: {company}']

  SOURCE_LONG = 'OLECF Document Summary Info'
  SOURCE_SHORT = 'OLECF'


class OLECFSummaryInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OLECF Summary Info property set stream event."""

  DATA_TYPE = 'olecf:summary_info'

  FORMAT_STRING_PIECES = [
      'Title: {title}',
      'Subject: {subject}',
      'Author: {author}',
      'Keywords: {keywords}',
      'Comments: {comments}',
      'Template: {template}',
      'Revision number: {revision_number}',
      'Last saved by: {last_saved_by}',
      'Total edit time: {total_edit_time}',
      'Number of pages: {number_of_pages}',
      'Number of words: {number_of_words}',
      'Number of characters: {number_of_characters}',
      'Application: {application}',
      'Security: {security}']

  FORMAT_STRING_SHORT_PIECES = [
      'Title: {title}',
      'Subject: {subject}',
      'Author: {author}',
      'Revision number: {revision_number}']

  SOURCE_LONG = 'OLECF Summary Info'
  SOURCE_SHORT = 'OLECF'

  _SECURITY_VALUES = {
      0x00000001: 'Password protected',
      0x00000002: 'Read-only recommended',
      0x00000004: 'Read-only enforced',
      0x00000008: 'Locked for annotations',
  }

  def GetMessages(self, formatter_mediator, event_data):
    """Determines the formatted message strings for the event data.

    Args:
      formatter_mediator (FormatterMediator): mediates the interactions
          between formatters and other components, such as storage and Windows
          EventLog resources.
      event_data (EventData): event data.

    Returns:
      tuple(str, str): formatted message string and short message string.

    Raises:
      WrongFormatter: if the event data cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_data.data_type:
      raise errors.WrongFormatter('Unsupported data type: {0:s}.'.format(
          event_data.data_type))

    event_values = event_data.CopyToDict()

    security = event_values.get('security', None)
    if security:
      security_flags = []
      for flag, description in iter(self._SECURITY_VALUES.items()):
        if security & flag:
          security_flags.append(description)

      security_string = '0x{0:08x}: {1:s}'.format(
          security, ','.join(security_flags))

      event_values['security'] = security_string

    for key, value in iter(event_values.items()):
      if isinstance(value, py2to3.BYTES_TYPE):
        event_values[key] = repr(value)

    return self._ConditionalFormatMessages(event_values)


manager.FormattersManager.RegisterFormatters([
    OLECFItemFormatter, OLECFDestListEntryFormatter,
    OLECFDocumentSummaryInfoFormatter, OLECFSummaryInfoFormatter])
