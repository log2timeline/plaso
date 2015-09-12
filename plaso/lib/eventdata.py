# -*- coding: utf-8 -*-
"""A place to store information about events, such as format strings, etc."""


# TODO: move this class to events/definitions.py or equiv.
class EventTimestamp(object):
  """Class to manage event data."""
  # The timestamp_desc values.
  ACCESS_TIME = u'Last Access Time'
  CHANGE_TIME = u'Metadata Modification Time'
  CREATION_TIME = u'Creation Time'
  MODIFICATION_TIME = u'Content Modification Time'
  ENTRY_MODIFICATION_TIME = u'Metadata Modification Time'
  # Added time and Creation time are considered the same.
  ADDED_TIME = u'Creation Time'
  # Written time and Modification time are considered the same.
  WRITTEN_TIME = u'Content Modification Time'
  EXIT_TIME = u'Exit Time'
  LAST_RUNTIME = u'Last Time Executed'
  DELETED_TIME = u'Content Deletion Time'

  INSTALLATION_TIME = u'Installation Time'

  FILE_DOWNLOADED = u'File Downloaded'
  PAGE_VISITED = u'Page Visited'
  # TODO: change page visited into last visited time.
  LAST_VISITED_TIME = u'Last Visited Time'

  LAST_CHECKED_TIME = u'Last Checked Time'

  EXPIRATION_TIME = u'Expiration Time'
  START_TIME = u'Start Time'
  END_TIME = u'End Time'

  LAST_SHUTDOWN = u'Last Shutdown Time'

  ACCOUNT_CREATED = u'Account Created'
  LAST_LOGIN_TIME = u'Last Login Time'
  LAST_PASSWORD_RESET = u'Last Password Reset'

  FIRST_CONNECTED = u'First Connection Time'
  LAST_CONNECTED = u'Last Connection Time'

  LAST_PRINTED = u'Last Printed Time'

  LAST_RESUME_TIME = u'Last Resume Time'

  # The timestamp does not represent a date and time value.
  NOT_A_TIME = u'Not a time'

  # Note that the unknown time is used for date and time values
  # of which the exact meaning is unknown and being researched.
  # For most cases do not use this timestamp description.
  UNKNOWN = u'Unknown Time'
