# -*- coding: utf-8 -*-
"""Task related attribute container object definitions."""

import time
import uuid

from plaso.containers import interface


class Task(interface.AttributeContainer):
  """Class to represent a task attribute container.

  A task describes a piece of work for a multi processing worker process
  e.g. to process a path specification or to analyze an event.

  Attributes:
    completion_time (int): time that the task was completed. Contains the
                           number of micro seconds since January 1, 1970,
                           00:00:00 UTC.
    identifier (str): unique identifier of the task.
    path_spec (dfvfs.PathSpec): path specification.
    session_identifier (str): the identifier of the session the task
                              is part of.
    start_time (int): time that the task was started. Contains the number
                      of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = u'task'

  def __init__(self, session_identifier=None):
    """Initializes a task attribute container.

    Args:
      session_identifier (Optional[str]): identifier of the session the task
                                          is part of.
    """
    super(Task, self).__init__()
    self.completion_time = None
    self.identifier = u'{0:s}'.format(uuid.uuid4().get_hex())
    self.path_spec = None
    self.session_identifier = session_identifier
    self.start_time = int(time.time() * 1000000)

  def CreateTaskCompletion(self):
    """Creates a task completion.

    Returns:
      TaskCompletion: task completion attribute container.
    """
    self.completion_time = int(time.time() * 1000000)

    task_completion = TaskCompletion()
    task_completion.identifier = self.identifier
    task_completion.session_identifier = self.session_identifier
    task_completion.timestamp = self.completion_time
    return task_completion

  def CreateTaskStart(self):
    """Creates a task start.

    Returns:
      TaskStart: task start attribute container.
    """
    task_start = TaskStart()
    task_start.identifier = self.identifier
    task_start.session_identifier = self.session_identifier
    task_start.timestamp = self.start_time
    return task_start


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
    self.timestamp = None


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

  def __init__(self, identifier=None, session_identifier=None):
    """Initializes a task start attribute container.

    Args:
      identifier (Optional[str]): unique identifier of the task.
          The identifier should match that of the corresponding
          task completion information.
      session_identifier (Optional[str]): identifier of the session the task
                                          is part of.
    """
    super(TaskStart, self).__init__()
    self.identifier = identifier
    self.session_identifier = session_identifier
    self.timestamp = None
