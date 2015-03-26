# -*- coding: utf-8 -*-
"""Formatters for OLE Compound File (OLECF) events."""

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.lib import errors


class OleCfItemFormatter(interface.EventFormatter):
  """Formatter for an OLECF item."""

  DATA_TYPE = 'olecf:item'

  FORMAT_STRING = u'Name: {name}'
  FORMAT_STRING_SHORT = u'Name: {name}'

  SOURCE_LONG = 'OLECF Item'
  SOURCE_SHORT = 'OLECF'


class OleCfDestListEntryFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OLECF DestList stream."""

  DATA_TYPE = 'olecf:dest_list:entry'

  FORMAT_STRING_PIECES = [
      u'Entry: {entry_number}',
      u'Pin status: {pin_status}',
      u'Hostname: {hostname}',
      u'Path: {path}',
      u'Droid volume identifier: {droid_volume_identifier}',
      u'Droid file identifier: {droid_file_identifier}',
      u'Birth droid volume identifier: {birth_droid_volume_identifier}',
      u'Birth droid file identifier: {birth_droid_file_identifier}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Entry: {entry_number}',
      u'Pin status: {pin_status}',
      u'Path: {path}']

  def GetMessages(self, unused_formatter_mediator, event_object):
    """Determines the formatted message strings for an event object.

    Args:
      formatter_mediator: the formatter mediator object (instance of
                          FormatterMediator).
      event_object: the event object (instance of EventObject).

    Returns:
      A tuple containing the formatted message string and short message string.

    Raises:
      WrongFormatter: if the event object cannot be formatted by the formatter.
    """
    if self.DATA_TYPE != event_object.data_type:
      raise errors.WrongFormatter(u'Unsupported data type: {0:s}.'.format(
          event_object.data_type))

    event_values = event_object.GetValues()

    pin_status = event_values.get(u'pin_status', 0)
    if pin_status == 0xffffffff:
      event_values[u'pin_status'] = u'Unpinned'
    else:
      event_values[u'pin_status'] = u'Pinned'

    return self._ConditionalFormatMessages(event_values)


class OleCfDocumentSummaryInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OLECF Summary Info property set stream."""

  DATA_TYPE = 'olecf:document_summary_info'

  FORMAT_STRING_PIECES = [
      u'Number of bytes: {number_of_bytes}',
      u'Number of lines: {number_of_lines}',
      u'Number of paragraphs: {number_of_paragraphs}',
      u'Number of slides: {number_of_slides}',
      u'Number of notes: {number_of_notes}',
      u'Number of hidden slides: {number_of_hidden_slides}',
      u'Number of multi-media clips: {number_of_clips}',
      u'Company: {company}',
      u'Manager: {manager}',
      u'Shared document: {shared_document}',
      u'Application version: {application_version}',
      u'Content type: {content_type}',
      u'Content status: {content_status}',
      u'Language: {language}',
      u'Document version: {document_version}']

      # TODO: add support for the following properties.
      # u'Digital signature: {digital_signature}',

  FORMAT_STRING_SHORT_PIECES = [
      u'Company: {company}']

  SOURCE_LONG = 'OLECF Document Summary Info'
  SOURCE_SHORT = 'OLECF'


class OleCfSummaryInfoFormatter(interface.ConditionalEventFormatter):
  """Formatter for an OLECF Summary Info property set stream."""

  DATA_TYPE = 'olecf:summary_info'

  FORMAT_STRING_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}',
      u'Keywords: {keywords}',
      u'Comments: {comments}',
      u'Template: {template}',
      u'Revision number: {revision_number}',
      u'Last saved by: {last_saved_by}',
      u'Total edit time: {total_edit_time}',
      u'Number of pages: {number_of_pages}',
      u'Number of words: {number_of_words}',
      u'Number of characters: {number_of_characters}',
      u'Application: {application}',
      u'Security: {security}']

  FORMAT_STRING_SHORT_PIECES = [
      u'Title: {title}',
      u'Subject: {subject}',
      u'Author: {author}',
      u'Revision number: {revision_number}']

  SOURCE_LONG = 'OLECF Summary Info'
  SOURCE_SHORT = 'OLECF'

  # TODO: add a function to print the security as a descriptive string.
  _SECURITY_VALUES = {
      0x00000001: 'Password protected',
      0x00000002: 'Read-only recommended',
      0x00000004: 'Read-only enforced',
      0x00000008: 'Locked for annotations',
  }


manager.FormattersManager.RegisterFormatters([
    OleCfItemFormatter, OleCfDestListEntryFormatter,
    OleCfDocumentSummaryInfoFormatter, OleCfSummaryInfoFormatter])
