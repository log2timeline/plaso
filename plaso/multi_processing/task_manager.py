# -*- coding: utf-8 -*-
"""The task manager."""

import time

from plaso.containers import tasks


class TaskManager(object):
  """Class that manages tasks and tracks their completion and status."""

  # Consider a task inactive after 5 minutes of no activity.
  _TASK_INACTIVE_TIME = 5 * 60 * 1000000

  def __init__(self, maximum_number_of_tasks=0):
    """Initializes a task manager object.

    Args:
      maximum_number_of_tasks (Optional[int]): maximum number of concurrent
          tasks, where 0 represents no limit.
    """
    super(TaskManager, self).__init__()
    self._active_tasks = {}
    self._cancelled_tasks = {}
    self._maximum_number_of_tasks = maximum_number_of_tasks
    self._scheduled_tasks = {}

  def CompleteTask(self, task_identifier):
    """Completes a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not scheduled.
    """
    if task_identifier not in self._scheduled_tasks:
      raise KeyError(u'Task not scheduled')

    del self._active_tasks[task_identifier]
    del self._scheduled_tasks[task_identifier]

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

  def GetCancelledTasks(self):
    """Retrieves all cancelled tasks.

    Returns:
      list[task]: task.
    """
    return self._cancelled_tasks.values()

  def GetScheduledTaskIdentifiers(self):
    """Retrieves all scheduled task identifiers.

    Returns:
      list[str]: unique identifiers of the tasks.
    """
    return list(self._scheduled_tasks.keys())

  def HasScheduledTasks(self):
    """Determines if there are scheduled tasks.

    A task will be cancelled if it last update exceeds the inactive time.

    Returns:
      bool: True if there are scheduled has active tasks.
    """
    if not self._scheduled_tasks:
      return False

    inactive_time = int(time.time() * 1000000) - self._TASK_INACTIVE_TIME

    has_active_tasks = False
    for task_identifier, last_update in iter(self._scheduled_tasks.items()):
      if last_update > inactive_time:
        has_active_tasks = True
      else:
        del self._scheduled_tasks[task_identifier]
        task = self._active_tasks[task_identifier]
        self._cancelled_tasks[task_identifier] = task
        del self._active_tasks[task_identifier]

    return has_active_tasks

  def ScheduleTask(self, task_identifier):
    """Schedules a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is already scheduled.
    """
    if task_identifier in self._scheduled_tasks:
      raise KeyError(u'Task already scheduled')

    # TODO: add check for maximum_number_of_tasks.
    self._scheduled_tasks[task_identifier] = int(time.time() * 1000000)

  def UpdateTask(self, task_identifier):
    """Updates a task.

    Args:
      task_identifier (str): unique identifier of the task.

    Raises:
      KeyError: if the task is not scheduled.
    """
    if task_identifier not in self._scheduled_tasks:
      raise KeyError(u'Task not scheduled')

    self._scheduled_tasks[task_identifier] = int(time.time() * 1000000)
