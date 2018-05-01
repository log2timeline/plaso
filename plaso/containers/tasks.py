# -*- coding: utf-8 -*-
"""Task related attribute container definitions."""

from __future__ import unicode_literals

import time
import uuid

from plaso.containers import interface
from plaso.containers import manager
from plaso.lib import definitions


class Task(interface.AttributeContainer):
  """Task attribute container.

  A task describes a piece of work for a multi processing worker process
  e.g. to process a path specification or to analyze an event.

  Attributes:
    aborted (bool): True if the session was aborted.
    completion_time (int): time that the task was completed. Contains the
        number of micro seconds since January 1, 1970, 00:00:00 UTC.
    file_entry_type (str): dfVFS type of the file entry the path specification
        is referencing.
    identifier (str): unique identifier of the task.
    last_processing_time (int): the last time the task was marked as being
      processed as number of milliseconds since January 1, 1970, 00:00:00 UTC.
    merge_priority (int): priority used for the task storage file merge, where
        a lower value indicates a higher priority to merge.
    original_task_identifier (str): the identifier of the task of which this
        task is a retry or None if not set.
    path_spec (dfvfs.PathSpec): path specification.
    retry_count (int): number of times the task has been retried.
    retry_task_identifier (str): identifier of the retry task, when the task
        is being retried or None if not set.
    session_identifier (str): the identifier of the session the task is part of.
    start_time (int): time that the task was started. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
    storage_file_size (int): size of the storage file in bytes.
  """
  CONTAINER_TYPE = 'task'

  def __init__(self, session_identifier=None):
    """Initializes a task attribute container.

    Args:
      session_identifier (Optional[str]): identifier of the session the task
          is part of.
    """
    super(Task, self).__init__()
    self.aborted = False
    self.completion_time = None
    self.file_entry_type = None
    self.identifier = '{0:s}'.format(uuid.uuid4().hex)
    self.last_processing_time = None
    self.merge_priority = None
    self.original_task_identifier = None
    self.path_spec = None
    self.retry_count = 0
    self.retry_task_identifier = None
    self.session_identifier = session_identifier
    self.start_time = int(time.time() * definitions.MICROSECONDS_PER_SECOND)
    self.storage_file_size = None

  # This method is necessary for heap sort.
  def __lt__(self, other):
    """Compares if the task attribute container is less than the other.

    Args:
      other (Task): task attribute container to compare to.

    Returns:
      bool: True if the task attribute container is less than the other.
    """
    return self.identifier < other.identifier

  def CreateRetryTask(self):
    """Creates a new task to retry the existing task.

    Returns:
      task (Task): a task to retry of the existing task.
    """
    retry_task = Task(session_identifier=self.session_identifier)
    retry_task.file_entry_type = self.file_entry_type
    retry_task.merge_priority = self.merge_priority
    retry_task.original_task_identifier = self.identifier
    retry_task.path_spec = self.path_spec
    retry_task.retry_count = self.retry_count + 1
    retry_task.storage_file_size = self.storage_file_size

    self.retry_task_identifier = retry_task.identifier

    return retry_task

  def CreateTaskCompletion(self):
    """Creates a task completion.

    Returns:
      TaskCompletion: task completion attribute container.
    """
    self.completion_time = int(
        time.time() * definitions.MICROSECONDS_PER_SECOND)

    task_completion = TaskCompletion()
    task_completion.aborted = self.aborted
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

  def UpdateProcessingTime(self):
    """Updates the processing time to now."""
    self.last_processing_time = int(
        time.time() * definitions.MICROSECONDS_PER_SECOND)


class TaskCompletion(interface.AttributeContainer):
  """Task completion attribute container.

  Attributes:
    aborted (bool): True if the session was aborted.
    identifier (str): unique identifier of the task.
    session_identifier (str): the identifier of the session the task
        is part of.
    timestamp (int): time that the task was completed. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = 'task_completion'

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
    self.aborted = False
    self.identifier = identifier
    self.session_identifier = session_identifier
    self.timestamp = None


class TaskStart(interface.AttributeContainer):
  """Task start attribute container.

  Attributes:
    identifier (str): unique identifier of the task.
    session_identifier (str): the identifier of the session the task
        is part of.
    timestamp (int): time that the task was started. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
  """
  CONTAINER_TYPE = 'task_start'

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


manager.AttributeContainersManager.RegisterAttributeContainers([
    Task, TaskCompletion, TaskStart])
