# -*- coding: utf-8 -*-
"""Engine utility functions."""

import logging

from dfvfs.helpers import file_system_searcher


class _PathExpander(object):
  """Class that implements the path expander."""

  def ExpandPath(self, path, path_attributes=None):
    """Expands a path based on attributes in pre calculated values.

       A path may contain paths that are attributes, based on calculations
       from preprocessing.

       A path attribute is defined as anything within a curly bracket, e.g.
       "\\System\\{my_attribute}\\Path\\Keyname". If the path attribute
       my_attribute is defined its value will be replaced with the attribute
       name, e.g. "\\System\\MyValue\\Path\\Keyname".

       If the path needs to have curly brackets in the path then they need
       to be escaped with another curly bracket, e.g.
       "\\System\\{my_attribute}\\{{123-AF25-E523}}\\KeyName". In this
       case the {{123-AF25-E523}} will be replaced with "{123-AF25-E523}".

    Args:
      path: the path before being expanded.
      path_attributes: optional dictionary of path attributes.

    Returns:
      A Registry key path that's expanded based on attribute values.

    Raises:
      KeyError: If an attribute name is in the key path not set in
                the preprocessing object a KeyError will be raised.
    """
    if not path_attributes:
      return path

    try:
      expanded_path = path.format(**path_attributes)
    except KeyError as exception:
      raise KeyError(
          u'Unable to expand path with error: {0:s}'.format(exception))

    return expanded_path


def BuildFindSpecsFromFile(filter_file_path, pre_obj=None):
  """Returns a list of find specification from a filter file.

  Args:
    filter_file_path: A path to a file that contains find specifications.
    pre_obj: A preprocessing object (instance of PreprocessObject). This is
             optional but when provided takes care of expanding each segment.
  """
  find_specs = []

  if pre_obj:
    expander = _PathExpander()

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
