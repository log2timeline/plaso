# -*- coding: utf-8 -*-
"""Digest hashes related attribute container object definitions."""

from plaso.containers import interface
from plaso.containers import manager


class DigestHashRecording(interface.AttributeContainer):
  """Class to represent a digest hash recording.

  A digest hash recording provides contextual information about typically a
  cryptographic digest hash, such as SHA-256 or MD5. The recording can
  indicate if the digest hash is of known good or bad file content.

  Attributes:
    digest_hash (str): digest hash.
    found_in_library (bool): True if the digest hash was found in the library,
        False if not and None if unknown.
    labels (list[str]): labels for an event tag.
    library (str): name of the digest hash library.
  """
  CONTAINER_TYPE = u'digest_hash_recording'

  def __init__(self, digest_hash=None, found_in_library=None, library=None):
    """Initializes a digest hash recording attribute container.

    Args:
      digest_hash (Optional[str]): digest hash.
      found_in_library (Optional[bool]): True if the digest hash was found in
          the library, False if not and None if unknown.
      library (Optional[str]): name of the digest hash library.
    """
    super(DigestHashRecording, self).__init__()
    self.digest_hash = digest_hash
    self.found_in_library = found_in_library
    self.labels = None
    self.library = library


manager.AttributeContainersManager.RegisterAttributeContainer(
    DigestHashRecording)
