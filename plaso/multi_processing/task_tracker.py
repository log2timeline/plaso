# -*- coding: utf-8 -*-
"""The task tracker."""

import time

from plaso.containers import tasks


class TaskTracker(object):
  """Class that defines a task tracker."""

  # Consider a task inactive after 5 minutes of no activity.
  _TASK_INACTIVE_TIME = 5 * 60 * 1000000

  def __init__(self, maximum_number_of_tasks=0):
    """Initializes a task tracker server object.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
    """
    super(TaskTracker, self).__init__()
    self._active_tasks = {}
    self._inactive_tasks = {}
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._tracked_tasks = {}

  # TODO: add support for task types.
  def CreateTask(self, session_identifier):
    """Creates a task.

    Args:
      session_identifier (str): the identifier of the session the task is
          part of.

    Returns:
      Task: task attribute container.
    """
    task = tasks.Task(session_identifier)
    self._active_tasks[task.identifier] = task
    return task

  def GetInactiveTasks(self):
    """Retrieves the inactive tasks.

    Returns:
      list[task]: task.
    """
    return self._inactive_tasks.values()

  def GetTrackedTaskIdentifiers(self):
    """Retrieves the tracked task identifiers.

    Returns:
      list[str]: unique identifiers of the tasks.
    """
    return list(self._tracked_tasks.keys())

  def HasActiveTasks(self):
    """Determines if the tracker has active tasks.

    Returns:
      bool: True if the tracker has active tasks.
    """
    if not self._tracked_tasks:
      return False

    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

    has_active_tasks = False
    for task_identifier, last_update in iter(self._tracked_tasks.items()):
      if last_update > inactive_time:
        has_active_tasks = True
      else:
        del self._tracked_tasks[task_identifier]
        task = self._active_tasks[task_identifier]
        self._inactive_tasks[task_identifier] = task
        del self._active_tasks[task_identifier]

    return has_active_tasks

  def TrackTask(self, task_identifier):
    """Tracks a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is already tracked.
    """
    if task_identifier in self._tracked_tasks:
      raise KeyError(u'Task already tracked')

    # TODO: add check for maximum_number_of_tasks.
    self._tracked_tasks[task_identifier] = int(time.time() * 1000000)

  def UpdateTask(self, task_identifier):
    """Updates a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not tracked.
    """
    if task_identifier not in self._tracked_tasks:
      raise KeyError(u'Task not tracked')

    self._tracked_tasks[task_identifier] = int(time.time() * 1000000)

  def UntrackTask(self, task_identifier):
    """Uptracks a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not tracked.
    """
    if task_identifier not in self._tracked_tasks:
      raise KeyError(u'Task not tracked')

    del self._active_tasks[task_identifier]
    del self._tracked_tasks[task_identifier]
