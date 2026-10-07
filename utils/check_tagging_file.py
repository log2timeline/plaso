#!/usr/bin/env python3
"""Script to check tagging files for labels and rules that cannot be loaded."""

import argparse
import sys

from plaso.engine import tagging_file


def Main():
    """The main program function.

    Returns:
      int: exit code that is provided to sys.exit().
    """
    argument_parser = argparse.ArgumentParser(
        description=(
            "Checks tagging files for labels and rules that cannot be loaded by the "
            "tagging analysis plugin."
        )
    )
    argument_parser.add_argument(
        "paths",
        metavar="PATH",
        nargs="+",
        type=str,
        help="paths of the tagging files to check.",
    )
    options = argument_parser.parse_args()

    number_of_findings = 0
    for path in options.paths:
        tagging_file_object = tagging_file.TaggingFile(path)
        try:
            findings = tagging_file_object.Validate()
        except OSError as exception:
            print(f"{path:s}: unable to read file with error: {exception!s}")
            number_of_findings += 1
            continue

        for line_number, description in findings:
            print(f"{path:s}:{line_number:d}: {description:s}")

        number_of_findings += len(findings)

    if number_of_findings:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(Main())
