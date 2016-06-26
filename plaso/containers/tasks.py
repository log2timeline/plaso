# -*- coding: utf-8 -*-
"""Task related attribute container object definitions."""

import time
import uuid

from plaso.containers import interface


class TaskCompletion(interface.AttributeContainer):
  """Class to represent a task completion attribute container.

  Attributes:
    identifier (str): unique identifier of the task.
    session_identifier (str): the identifier of the session the task
                              is part of.
    timestamp (int): time that the task was completed. Contains the number
                     of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'task_completion'

  def __init__(self, identifier=None, session_identifier=None):
    """Initializes a task completion attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the task.
          The identifier should match that of the corresponding
          task start information.
      session_identifier (Optional[str]): identifier of the session the task
                                          is part of.
    """
    super(TaskCompletion, self).__init__()
    self.identifier = identifier
    self.session_identifier = session_identifier
    self.timestamp = int(time.time() * 1000000)


class TaskStart(interface.AttributeContainer):
  """Class to represent a task start attribute container.

  Attributes:
    identifier (str): unique identifier of the task.
    session_identifier (str): the identifier of the session the task
                              is part of.
    timestamp (int): time that the task was started. Contains the number
                     of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'task_start'

  def __init__(self, session_identifier=None):
    """Initializes a task start attribute container.

    Args:
      session_identifier (Optional[str]): identifier of the session the task
                                          is part of.
    """
    super(TaskStart, self).__init__()
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.session_identifier = session_identifier
    self.timestamp = int(time.time() * 1000000)
