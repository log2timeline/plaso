# -*- coding: utf-8 -*-
"""Collection filters helper."""

from __future__ import unicode_literals


class CollectionFiltersHelper(object):
  """Helper for collection filters.

  Attributes:
    excluded_file_system_find_specs (list[dfvfs.FindSpec]): file system find
        specifications of paths to exclude from the collection.
    included_file_system_find_specs (list[dfvfs.FindSpec]): file system find
        specifications of paths to include in the collection.
    registry_find_specs (list[dfwinreg.FindSpec]): Windows Registry find
        specifications.
  """

  def __init__(self):
    """Initializes a collection filters helper."""
    super(CollectionFiltersHelper, self).__init__()
    self.excluded_file_system_find_specs = []
    self.included_file_system_find_specs = []
    self.registry_find_specs = []
