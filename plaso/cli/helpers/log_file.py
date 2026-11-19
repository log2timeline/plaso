"""The log file CLI arguments helper."""

import datetime

from plaso.cli import tools
from plaso.cli.helpers import interface
from plaso.cli.helpers import manager
from plaso.lib import errors


class LogFileArgumentsHelper(interface.ArgumentsHelper):
    """Log file CLI arguments helper."""

    NAME = "log_file"
    DESCRIPTION = "Log file command line arguments."

    @classmethod
    def AddArguments(cls, argument_group):
        """Adds command line arguments to an argument group.

        This function takes an argument parser or an argument group object and adds
        to it all the command line arguments this helper supports.

        Args:
          argument_group (argparse._ArgumentGroup|argparse.ArgumentParser):
              argparse group.
        """
        argument_group.add_argument(
            "--logfile",
            "--log_file",
            "--log-file",
            action="store",
            metavar="FILENAME",
            dest="log_file",
            type=str,
            default="",
            help=(
                "Path of the file in which to store log messages, by default this "
                "file will be named after the tool, such as: "
                '"log2timeline-YYYYMMDDThhmmss.log.gz". Note that the file will be '
                'gzip compressed if the extension is ".gz".'
            ),
        )

    @classmethod
    def ParseOptions(cls, options, configuration_object):
        """Parses and validates options.

        Args:
          options (argparse.Namespace): parser options.
          configuration_object (CLITool): object to be configured by the argument
              helper.

        Raises:
          BadConfigObject: when the configuration object is of the wrong type.
        """
        if not isinstance(configuration_object, tools.CLITool):
            raise errors.BadConfigObject(
                "Configuration object is not an instance of CLITool"
            )

        log_file = cls._ParseStringOption(options, "log_file")
        if not log_file:
            local_date_time = datetime.datetime.now()
            log_file = (
                f"{configuration_object.NAME:s}-{local_date_time.year:04d}"
                f"{local_date_time.month:02d}{local_date_time.day:02d}T"
                f"{local_date_time.hour:02d}{local_date_time.minute:02d}"
                f"{local_date_time.second:02d}.log.gz"
            )

        setattr(configuration_object, "_log_file", log_file)


manager.ArgumentHelperManager.RegisterHelper(LogFileArgumentsHelper)
