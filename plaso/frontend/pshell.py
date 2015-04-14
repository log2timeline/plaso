# -*- coding: utf-8 -*-
"""The pshell front-end."""

from plaso.frontend import extraction_frontend


# TODO: refactor.
class PshellFrontend(extraction_frontend.ExtractionFrontend):
  """Class that implements the pshell front-end."""

  _BYTES_IN_A_MIB = 1024 * 1024
