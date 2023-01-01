# -*- coding: utf-8 -*-
"""Task attribute container definition."""

import time
import uuid

from acstore.containers import interface
from acstore.containers import manager

from plaso.lib import definitions


class Task(interface.AttributeContainer):
  """Task attribute container.

  A task describes a piece of work for a multi processing worker process
  for example a task to process a path specification or to analyze an event.

  Attributes:
    aborted (bool): True if the task was aborted.
    completion_time (int): time that the task was completed. Contains the
        number of micro seconds since January 1, 1970, 00:00:00 UTC.
    file_entry_type (str): dfVFS type of the file entry the path specification
        is referencing.
    has_retry (bool): True if the task was previously abandoned and a retry
        task was created, False otherwise.
    identifier (str): unique identifier of the task.
    last_processing_time (int): the last time the task was marked as being
        processed as number of milliseconds since January 1, 1970, 00:00:00 UTC.
    merge_priority (int): priority used for the task storage file merge, where
        a lower value indicates a higher priority to merge.
    path_spec (dfvfs.PathSpec): path specification.
    session_identifier (str): the identifier of the session the task is part of.
    start_time (int): time that the task was started. Contains the number
        of micro seconds since January 1, 1970, 00:00:00 UTC.
    storage_file_size (int): size of the storage file in bytes.
    storage_format (str): the format the task results are to be stored in.
  """

  CONTAINER_TYPE = 'task'

  SCHEMA = {
      'aborted': 'bool',
      'completion_time': 'int',
      'file_entry_type': 'str',
      'has_retry': 'bool',
      'identifier': 'str',
      'last_processing_time': 'int',
      'merge_priority': 'int',
      'path_spec': 'dfvfs.PathSpec',
      'session_identifier': 'str',
      'start_time': 'int',
      'storage_file_size': 'int',
      'storage_format': 'str'}

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
    self.has_retry = False
    self.identifier = '{0:s}'.format(uuid.uuid4().hex)
    self.last_processing_time = None
    self.merge_priority = None
    self.path_spec = None
    self.session_identifier = session_identifier
    self.start_time = int(time.time() * definitions.MICROSECONDS_PER_SECOND)
    self.storage_file_size = None
    self.storage_format = None

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
    """Creates a new task to retry a previously abandoned task.

    The retry task will have a new identifier but most of the attributes
    will be a copy of the previously abandoned task.

    Returns:
      Task: a task to retry a previously abandoned task.
    """
    retry_task = Task(session_identifier=self.session_identifier)
    retry_task.file_entry_type = self.file_entry_type
    retry_task.merge_priority = self.merge_priority
    retry_task.path_spec = self.path_spec
    retry_task.storage_file_size = self.storage_file_size
    retry_task.storage_format = self.storage_format

    self.has_retry = True

    return retry_task

  def UpdateProcessingTime(self):
    """Updates the processing time to now."""
    self.last_processing_time = int(
        time.time() * definitions.MICROSECONDS_PER_SECOND)


manager.AttributeContainersManager.RegisterAttributeContainer(Task)
