# -*- coding: utf-8 -*-
"""The AUL Event data container."""

from plaso.containers import events

class AULEventData(events.EventData):
  """Apple Unified Logging (AUL) event data.

  Attributes:
    activity_id (str): path from the root to this plist key.
    body (str): the log message.
    boot_uuid (str): unique boot identifier.
    category (str): event category.
    creation_time (dfdatetime.DateTimeValues): file entry creation date
        and time.
    euid (int): effective user identifier (UID)
    level (str): level of criticality of the event.
    library (str): originating library path.
    library_uuid (str): Unique library identifier.
    pid (int): process identifier (PID).
    process (str): originating process path.
    process_uuid (str): unique process identifier.
    subsystem (str): subsystem that produced the logging event.
    thread_id (str): hex representation of the thread ID.
    ttl (int): log time to live (TTL).
  """
  DATA_TYPE = 'macos:aul:event'

  def __init__(self):
    """Initialise event data."""
    super(AULEventData, self).__init__(data_type=self.DATA_TYPE)
    self.activity_id = None
    self.body = None
    self.boot_uuid = None
    self.category = None
    self.creation_time = None
    self.euid = None
    self.level = None
    self.library = None
    self.library_uuid = None
    self.pid = None
    self.process = None
    self.process_uuid = None
    self.subsystem = None
    self.thread_id = None
    self.ttl = None
