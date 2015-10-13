# -*- coding: utf-8 -*-
"""Engine utility functions."""

import logging

from dfvfs.helpers import file_system_searcher

from plaso.dfwinreg import path_expander as dfwinreg_path_expander


def BuildFindSpecsFromFile(filter_file_path, pre_obj=None):
  """Returns a list of find specification from a filter file.

  Args:
    filter_file_path: A path to a file that contains find specifications.
    pre_obj: A preprocessing object (instance of PreprocessObject). This is
             optional but when provided takes care of expanding each segment.
  """
  find_specs = []

  if pre_obj:
    expander = dfwinreg_path_expander.WinRegistryKeyPathExpander()

  with open(filter_file_path, 'rb') as file_object:
    for line in file_object:
      line = line.strip()
      if line.startswith(u'#'):
        continue

      if pre_obj:
        path_attributes = pre_obj.__dict__
        try:
          line = expander.ExpandPath(line, path_attributes=path_attributes)
        except KeyError as exception:
          logging.error((
              u'Unable to use collection filter line: {0:s} with error: '
              u'{1:s}').format(line, exception))
          continue

      if not line.startswith(u'/'):
        logging.warning((
            u'The filter string must be defined as an abolute path: '
            u'{0:s}').format(line))
        continue

      _, _, file_path = line.rstrip().rpartition(u'/')
      if not file_path:
        logging.warning(
            u'Unable to parse the filter string: {0:s}'.format(line))
        continue

      # Convert the filter paths into a list of path segments and strip
      # the root path segment.
      path_segments = line.split(u'/')
      path_segments.pop(0)

      find_specs.append(file_system_searcher.FindSpec(
          location_regex=path_segments, case_sensitive=False))

  return find_specs
