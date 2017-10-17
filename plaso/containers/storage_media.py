# -*- coding: utf-8 -*-
"""Storage media related attribute container definitions."""

from __future__ import unicode_literals

from plaso.containers import interface
from plaso.containers import manager


class MountPoint(interface.AttributeContainer):
  """Mount point attribute container.

  Attributes:
    mount_path (str): path where the path specification is mounted, such as
        "/mnt/image" or "C:\\".
    path_spec (dfvfs.PathSpec): path specification.
  """
  CONTAINER_TYPE = 'mount_point'

  def __init__(self, mount_path=None, path_specification=None):
    """Initializes a mount point.

    Args:
      mount_path (Optional[str]): path where the path specification is mounted,
          such as "/mnt/image" or "C:\\".
      path_specification (Optional[dfvfs.PathSpec]): path specification.
    """
    super(MountPoint, self).__init__()
    self.mount_path = mount_path
    self.path_specification = path_specification


manager.AttributeContainersManager.RegisterAttributeContainer(MountPoint)
