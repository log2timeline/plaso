# -*- coding: utf-8 -*-
"""A scan tree-based path filter implementation.

The scan tree is a tree based on multiple paths that contains the path
segments per node. The most significant path segment is at the root and
therefore compared first. More information can be found here:
https://github.com/libyal/libsigscan/wiki/Internals#scanning-tree-based-signature-scanning

The scan tree is used in the filter to filter provided paths.
"""


class _PathFilterTable(object):
  """Path filter table.

  The path filter table is used to construct a scan tree.
  """

  def __init__(self, paths, ignore_list, path_segment_separator='/'):
    """Initializes and builds the path filter table from a list of paths.

    Args:
      paths (list[str]): paths.
      ignore_list (list[int]): path segment indexes to ignore, where 0 is the
          index of the first path segment relative from the root.
      path_segment_separator (Optional[str]): path segment separator.
    """
    super(_PathFilterTable, self).__init__()
    self._path_segment_separator = path_segment_separator
    self.path_segments_per_index = {}
    self.paths = list(paths)

    for path in self.paths:
      self._AddPathSegments(path, ignore_list)

  def _AddPathSegments(self, path, ignore_list):
    """Adds the path segments to the table.

    Args:
      path (str): path.
      ignore_list (list[int]): path segment indexes to ignore, where 0 is the
          index of the first path segment relative from the root.
    """
    path_segments = path.split(self._path_segment_separator)
    for path_segment_index, path_segment in enumerate(path_segments):
      if path_segment_index not in self.path_segments_per_index:
        self.path_segments_per_index[path_segment_index] = {}

      if path_segment_index not in ignore_list:
        path_segments = self.path_segments_per_index[path_segment_index]

        if path_segment not in path_segments:
          path_segments[path_segment] = []

        paths_per_segment_list = path_segments[path_segment]
        paths_per_segment_list.append(path)

  def GetPathIndexesList(self, path_segment_index, path_segment):
    """Retrieves the path indexes list.

    Args:
      path_segment_index (int): index of the path segment in the table.
      path_segment (str): path segment.

    Returns:
      list[int]: path indexes.
    """
    return self.path_segments_per_index[path_segment_index][path_segment]

  def GetPathSegments(self, path_segment_index):
    """Retrieves the path segments for a specific path segment index.

    Args:
      path_segment_index (int): index of the path segment in the table.

    Returns:
      dict[str, list[str]]: paths per path segment.
    """
    return self.path_segments_per_index[path_segment_index]

  def ToDebugString(self):
    """Converts the path filter table into a debug string.

    Returns:
      str: debug string representing the path filter table.
    """
    text_parts = ['Path segment index\tPath segments(s)']
    for index, path_segments in self.path_segments_per_index.items():
      text_parts.append('{0:d}\t\t\t[{1:s}]'.format(
          index, ', '.join(path_segments)))

    text_parts.append('')

    return '\n'.join(text_parts)


class _PathSegmentWeights(object):
  """Path segment weights.

  The path segment weights are used to determine the most significant
  path segment per index. The path segment weights are used to construct
  a scan tree.
  """

  def __init__(self):
    """Initializes path segment weights."""
    super(_PathSegmentWeights, self).__init__()
    self._indexes_per_weight = {}
    self._weight_per_index = {}

  def AddIndex(self, path_segment_index):
    """Adds a path segment index and sets its weight to 0.

    Args:
      path_segment_index (int): index of the path segment in the path filter
          table.

    Raises:
      ValueError: if the path segment weights already contains
          the path segment index.
    """
    if path_segment_index in self._weight_per_index:
      raise ValueError('Path segment index already set.')

    self._weight_per_index[path_segment_index] = 0

  def AddWeight(self, path_segment_index, weight):
    """Adds a weight for a specific path segment index.

    Args:
      path_segment_index (int): index of the path segment in the path filter
          table.
      weight (int): weight of the path segment.

    Raises:
      ValueError: if the path segment weights do not contain
          the path segment index.
    """
    if path_segment_index not in self._weight_per_index:
      raise ValueError('Path segment index not set.')

    self._weight_per_index[path_segment_index] += weight

    if weight not in self._indexes_per_weight:
      self._indexes_per_weight[weight] = []

    self._indexes_per_weight[weight].append(path_segment_index)

  def GetFirstAvailableIndex(self):
    """Retrieves the first available path segment index.

    Returns:
      int: first available path segment index or None if not available.
    """
    path_segment_indexes = sorted(self._weight_per_index.keys())
    if not path_segment_indexes:
      return None

    return path_segment_indexes[0]

  def GetLargestWeight(self):
    """Retrieves the largest weight.

    Returns:
      int: largest weight or 0 if there are no weights.
    """
    if not self._indexes_per_weight:
      return 0

    return max(self._indexes_per_weight)

  def GetIndexesForWeight(self, weight):
    """Retrieves the path segment indexes for a specific weight.

    Args:
      weight (int): weight.

    Returns:
      list[int]: path segment indexes for the weight.
    """
    return self._indexes_per_weight[weight]

  def GetWeightForIndex(self, path_segment_index):
    """Retrieves the weight for a specific path segment index.

    Args:
      path_segment_index (int): index of the path segment in the path filter
          table.

    Returns:
      int: weight for the path segment index.
    """
    return self._weight_per_index[path_segment_index]

  def SetWeight(self, path_segment_index, weight):
    """Sets a weight for a specific path segment index.

    Args:
      path_segment_index (int): index of the path segment in the path filter
          table.
      weight (int): weight.

    Raises:
      ValueError: if the path segment weights do not contain
          the path segment index.
    """
    if path_segment_index not in self._weight_per_index:
      raise ValueError('Path segment index not set.')

    self._weight_per_index[path_segment_index] = weight

    if weight not in self._indexes_per_weight:
      self._indexes_per_weight[weight] = []

    self._indexes_per_weight[weight].append(path_segment_index)

  def ToDebugString(self):
    """Converts the path segment weights into a debug string.

    Returns:
      str: debug string representing the path segment weights.
    """
    text_parts = ['Path segment index\tWeight']
    for path_segment_index, weight in self._weight_per_index.items():
      text_parts.append('{0:d}\t\t\t{1:d}'.format(
          path_segment_index, weight))
    text_parts.append('')

    text_parts.append('Weight\t\t\tPath segment index(es)')
    for weight, path_segment_indexes in self._indexes_per_weight.items():
      text_parts.append('{0:d}\t\t\t{1!s}'.format(
          weight, path_segment_indexes))
    text_parts.append('')

    return '\n'.join(text_parts)


class PathFilterScanTree(object):
  """Path filter scan tree."""

  def __init__(self, paths, case_sensitive=True, path_segment_separator='/'):
    """Initializes and builds a path filter scan tree.

    Args:
      paths (list[str]): paths.
      case_sensitive (Optional[bool]): True if string matches should be case
          sensitive.
      path_segment_separator (Optional[str]): path segment separator.
    """
    super(PathFilterScanTree, self).__init__()
    self._case_sensitive = case_sensitive
    self._path_segment_separator = path_segment_separator
    self._root_node = None

    if not self._case_sensitive:
      paths = [path.lower() for path in paths]

    path_filter_table = _PathFilterTable(
        paths, [], path_segment_separator=self._path_segment_separator)

    if path_filter_table.paths:
      self._root_node = self._BuildScanTreeNode(path_filter_table, [])

  def _BuildScanTreeNode(self, path_filter_table, ignore_list):
    """Builds a scan tree node.

    Args:
      path_filter_table (_PathFilterTable): path filter table.
      ignore_list (list[int]): path segment indexes to ignore, where 0 is the
          index of the first path segment relative from the root.

    Returns:
      PathFilterScanTreeNode: a scan tree node.

    Raises:
      ValueError: if the path segment index value or the number of paths
          segments value is out of bounds.
    """
    # Make a copy of the lists because the function is going to alter them
    # and the changes must remain in scope of the function.
    paths_list = list(path_filter_table.paths)
    ignore_list = list(ignore_list)

    similarity_weights = _PathSegmentWeights()
    occurrence_weights = _PathSegmentWeights()
    value_weights = _PathSegmentWeights()

    for path_segment_index in path_filter_table.path_segments_per_index.keys():
      # Skip a path segment index for which no path segments are defined
      # in the path filter table.
      if not path_filter_table.path_segments_per_index[path_segment_index]:
        continue

      similarity_weights.AddIndex(path_segment_index)
      occurrence_weights.AddIndex(path_segment_index)
      value_weights.AddIndex(path_segment_index)

      path_segments = path_filter_table.GetPathSegments(path_segment_index)

      number_of_path_segments = len(path_segments.keys())
      if number_of_path_segments > 1:
        occurrence_weights.SetWeight(
            path_segment_index, number_of_path_segments)

      for paths_per_segment_list in path_segments.values():
        path_segment_weight = len(paths_per_segment_list)
        if path_segment_weight > 1:
          similarity_weights.AddWeight(path_segment_index, path_segment_weight)

    path_segment_index = self._GetMostSignificantPathSegmentIndex(
        paths_list, similarity_weights, occurrence_weights, value_weights)

    ignore_list.append(path_segment_index)

    if path_segment_index < 0:
      raise ValueError('Invalid path segment index value out of bounds.')

    scan_tree_node = PathFilterScanTreeNode(path_segment_index)

    path_segments = path_filter_table.GetPathSegments(path_segment_index)

    for path_segment, paths_per_segment_list in path_segments.items():
      if not paths_per_segment_list:
        raise ValueError('Invalid number of paths value out of bounds.')

      if len(paths_per_segment_list) == 1:
        for path in paths_per_segment_list:
          scan_tree_node.AddPathSegment(path_segment, path)

      else:
        sub_path_filter_table = _PathFilterTable(
            paths_per_segment_list, ignore_list,
            path_segment_separator=self._path_segment_separator)

        scan_sub_node = self._BuildScanTreeNode(
            sub_path_filter_table, ignore_list)

        scan_tree_node.AddPathSegment(path_segment, scan_sub_node)

      for path in paths_per_segment_list:
        paths_list.remove(path)

    number_of_paths = len(paths_list)
    if number_of_paths == 1:
      scan_tree_node.SetDefaultValue(paths_list[0])

    elif number_of_paths > 1:
      path_filter_table = _PathFilterTable(
          paths_list, ignore_list,
          path_segment_separator=self._path_segment_separator)

      scan_sub_node = self._BuildScanTreeNode(path_filter_table, ignore_list)

      scan_tree_node.SetDefaultValue(scan_sub_node)

    return scan_tree_node

  def _GetMostSignificantPathSegmentIndex(
      self, paths, similarity_weights, occurrence_weights, value_weights):
    """Retrieves the index of the most significant path segment.

    Args:
      paths (list[str]): paths.
      similarity_weights (_PathSegmentWeights): similarity weights.
      occurrence_weights (_PathSegmentWeights): occurrence weights.
      value_weights (_PathSegmentWeights): value weights.

    Returns:
      int: path segment index.

    Raises:
      ValueError: when paths is an empty list.
    """
    if not paths:
      raise ValueError('Missing paths.')

    number_of_paths = len(paths)

    path_segment_index = None
    if number_of_paths == 1:
      path_segment_index = self._GetPathSegmentIndexForValueWeights(
          value_weights)

    elif number_of_paths == 2:
      path_segment_index = self._GetPathSegmentIndexForOccurrenceWeights(
          occurrence_weights, value_weights)

    elif number_of_paths > 2:
      path_segment_index = self._GetPathSegmentIndexForSimilarityWeights(
          similarity_weights, occurrence_weights, value_weights)

    return path_segment_index

  def _GetPathSegmentIndexForOccurrenceWeights(
      self, occurrence_weights, value_weights):
    """Retrieves the index of the path segment based on occurrence weights.

    Args:
      occurrence_weights (_PathSegmentWeights): occurrence weights.
      value_weights (_PathSegmentWeights): value weights.

    Returns:
      int: path segment index.
    """
    largest_weight = occurrence_weights.GetLargestWeight()

    if largest_weight > 0:
      occurrence_weight_indexes = occurrence_weights.GetIndexesForWeight(
          largest_weight)
      number_of_occurrence_indexes = len(occurrence_weight_indexes)
    else:
      number_of_occurrence_indexes = 0

    path_segment_index = None
    if number_of_occurrence_indexes == 0:
      path_segment_index = self._GetPathSegmentIndexForValueWeights(
          value_weights)

    elif number_of_occurrence_indexes == 1:
      path_segment_index = occurrence_weight_indexes[0]

    else:
      largest_weight = 0

      for occurrence_index in occurrence_weight_indexes:
        value_weight = value_weights.GetWeightForIndex(occurrence_index)

        if not path_segment_index or largest_weight < value_weight:
          largest_weight = value_weight
          path_segment_index = occurrence_index

    return path_segment_index

  def _GetPathSegmentIndexForSimilarityWeights(
      self, similarity_weights, occurrence_weights, value_weights):
    """Retrieves the index of the path segment based on similarity weights.

    Args:
      similarity_weights (_PathSegmentWeights): similarity weights.
      occurrence_weights (_PathSegmentWeights): occurrence weights.
      value_weights (_PathSegmentWeights): value weights.

    Returns:
      int: path segment index.
    """
    largest_weight = similarity_weights.GetLargestWeight()

    if largest_weight > 0:
      similarity_weight_indexes = similarity_weights.GetIndexesForWeight(
          largest_weight)
      number_of_similarity_indexes = len(similarity_weight_indexes)
    else:
      number_of_similarity_indexes = 0

    path_segment_index = None
    if number_of_similarity_indexes == 0:
      path_segment_index = self._GetPathSegmentIndexForOccurrenceWeights(
          occurrence_weights, value_weights)

    elif number_of_similarity_indexes == 1:
      path_segment_index = similarity_weight_indexes[0]

    else:
      largest_weight = 0
      largest_value_weight = 0

      for similarity_index in similarity_weight_indexes:
        occurrence_weight = occurrence_weights.GetWeightForIndex(
            similarity_index)

        if largest_weight > 0 and largest_weight == occurrence_weight:
          value_weight = value_weights.GetWeightForIndex(similarity_index)

          if largest_value_weight < value_weight:
            largest_weight = 0

        if not path_segment_index or largest_weight < occurrence_weight:
          largest_weight = occurrence_weight
          path_segment_index = similarity_index

          largest_value_weight = value_weights.GetWeightForIndex(
              similarity_index)

    return path_segment_index

  def _GetPathSegmentIndexForValueWeights(self, value_weights):
    """Retrieves the index of the path segment based on value weights.

    Args:
      value_weights (_PathSegmentWeights): value weights.

    Returns:
      int: path segment index.

    Raises:
      RuntimeError: is no path segment index can be found.
    """
    largest_weight = value_weights.GetLargestWeight()

    if largest_weight > 0:
      value_weight_indexes = value_weights.GetIndexesForWeight(largest_weight)
    else:
      value_weight_indexes = []

    if value_weight_indexes:
      path_segment_index = value_weight_indexes[0]
    else:
      path_segment_index = value_weights.GetFirstAvailableIndex()

    if path_segment_index is None:
      raise RuntimeError('No path segment index found.')

    return path_segment_index

  def CheckPath(self, path, path_segment_separator=None):
    """Checks if a path matches the scan tree-based path filter.

    Args:
      path (str): path.
      path_segment_separator (Optional[str]): path segment separator, where
          None defaults to the path segment separator that was set when
          the path filter scan tree was initialized.

    Returns:
      bool: True if the path matches the filter, False otherwise.
    """
    if not self._case_sensitive:
      path = path.lower()

    if path_segment_separator is None:
      path_segment_separator = self._path_segment_separator

    path_segments = path.split(path_segment_separator)
    number_of_path_segments = len(path_segments)

    scan_object = self._root_node
    while scan_object:
      if isinstance(scan_object, str):
        break

      if scan_object.path_segment_index >= number_of_path_segments:
        scan_object = scan_object.default_value
        continue

      path_segment = path_segments[scan_object.path_segment_index]
      scan_object = scan_object.GetScanObject(path_segment)

    if not isinstance(scan_object, str):
      return False

    filter_path_segments = scan_object.split(self._path_segment_separator)
    return filter_path_segments == path_segments


class PathFilterScanTreeNode(object):
  """Class that implements a path filter scan tree node.

  The path filter scan tree node defines the path segments for a specific
  path segment index to filter. Each path segment will point to a scan object
  that indicates the next part of the path filter. A default value indicates
  the scan object to use next when there was no match.

  Attributes:
    default_value (str|PathFilterScanTreeNode): the default scan object, which
        is either a scan tree sub node or a path.
    parent (PathFilterScanTreeNode): the parent path filter scan tree node or
        None if the node has no parent.
    path_segment_index (int): path segment index represented by the node.
  """

  def __init__(self, path_segment_index):
    """Initializes a path filter scan tree node.

    Args:
      path_segment_index (int): path segment index.
    """
    super(PathFilterScanTreeNode, self).__init__()
    self._path_segments = {}
    self.default_value = None
    self.parent = None
    self.path_segment_index = path_segment_index

  @property
  def path_segments(self):
    """list[str]: path segments."""
    return self._path_segments.keys()

  def AddPathSegment(self, path_segment, scan_object):  # pylint: disable=missing-type-doc
    """Adds a path segment.

    Args:
      path_segment (str): path segment.
      scan_object (str|PathFilterScanTreeNode): a scan object, which is either
          a scan tree sub node or a path.

    Raises:
      ValueError: if the node already contains a scan object for
          the path segment.
    """
    if path_segment in self._path_segments:
      raise ValueError('Path segment already set.')

    if isinstance(scan_object, PathFilterScanTreeNode):
      scan_object.parent = self

    self._path_segments[path_segment] = scan_object

  def GetScanObject(self, path_segment):  # pylint: disable=missing-return-type-doc
    """Retrieves the scan object for a specific path segment.

    Args:
      path_segment (str): path segment.

    Returns:
      str|PathFilterScanTreeNode: a scan object, which is either
          a scan tree sub node, a path or the default value.
    """
    return self._path_segments.get(path_segment, self.default_value)

  def SetDefaultValue(self, scan_object):
    """Sets the default (non-match) value.

    Args:
      scan_object (str|PathFilterScanTreeNode): a scan object, which is either
          a scan tree sub node or a path.

    Raises:
      TypeError: if the scan object is of an unsupported type.
      ValueError: if the default value is already set.
    """
    if not isinstance(scan_object, (str, PathFilterScanTreeNode)):
      raise TypeError('Unsupported scan object type.')

    if self.default_value:
      raise ValueError('Default value already set.')

    self.default_value = scan_object

  def ToDebugString(self, indentation_level=1):
    """Converts the path filter scan tree node into a debug string.

    Args:
      indentation_level (int): text indentation level.

    Returns:
      str: debug string representing the path filter scan tree node.
    """
    indentation = '  ' * indentation_level

    text_parts = ['{0:s}path segment index: {1:d}\n'.format(
        indentation, self.path_segment_index)]

    for path_segment, scan_object in self._path_segments.items():
      text_parts.append('{0:s}path segment: {1:s}\n'.format(
          indentation, path_segment))

      if isinstance(scan_object, PathFilterScanTreeNode):
        text_parts.append('{0:s}scan tree node:\n'.format(indentation))
        text_parts.append(scan_object.ToDebugString(indentation_level + 1))

      elif isinstance(scan_object, str):
        text_parts.append('{0:s}path: {1:s}\n'.format(indentation, scan_object))

    text_parts.append('{0:s}default value:\n'.format(indentation))

    if isinstance(self.default_value, PathFilterScanTreeNode):
      text_parts.append('{0:s}scan tree node:\n'.format(indentation))
      text_parts.append(self.default_value.ToDebugString(indentation_level + 1))

    elif isinstance(self.default_value, str):
      text_parts.append('{0:s}pattern: {1:s}\n'.format(
          indentation, self.default_value))

    text_parts.append('\n')

    return ''.join(text_parts)
