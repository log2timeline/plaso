# -*- coding: utf-8 -*-
"""Task related attribute container object definitions."""

import time
import uuid

from plaso.containers import interface


class TaskCompletion(interface.AttributeContainer):
  """Class to represent a task completion attribute container.

  Attributes:
    identifier: a string containing the identifier of the task.
    session_identifier: a string containing the identifier of the session
                        the task is part of.
    timestamp: an integer containing a timestamp of the start of the
               task. The integer represents the number of micro seconds
               since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'task_completion'

  def __init__(self, identifier, session_identifier):
    """Initializes a task completion attribute container.

    Args:
      identifier: a string containing the identifier of the task.
      session_identifier: a string containing the identifier of the session
                          the task is part of.
    """
    super(TaskCompletion, self).__init__()
    self.identifier = identifier
    self.session_identifier = session_identifier
    self.timestamp = int(time.time() * 100000)


class TaskStart(interface.AttributeContainer):
  """Class to represent a task start attribute container.

  Attributes:
    identifier: a string containing the identifier of the task.
    session_identifier: a string containing the identifier of the session
                        the task is part of.
    timestamp: an integer containing a timestamp of the start of the
               task. The integer represents the number of micro seconds
               since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'task_start'

  def __init__(self, session_identifier):
    """Initializes a task start attribute container.

    Args:
      session_identifier: a string containing the identifier of the session
                          the task is part of.
    """
    super(TaskStart, self).__init__()
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.session_identifier = session_identifier
    self.timestamp = int(time.time() * 100000)
