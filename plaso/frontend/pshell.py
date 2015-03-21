# -*- coding: utf-8 -*-
"""The pshell front-end."""

from plaso.frontend import frontend


class PshellFrontend(frontend.ExtractionFrontend):
  """Class that implements the pshell front-end."""

  _BYTES_IN_A_MIB = 1024 * 1024

  def __init__(self):
    """Initializes the front-end object."""
    input_reader = frontend.StdinFrontendInputReader()
    output_writer = frontend.StdoutFrontendOutputWriter()

    super(PshellFrontend, self).__init__(input_reader, output_writer)
