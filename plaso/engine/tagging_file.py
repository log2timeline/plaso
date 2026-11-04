"""Tagging file."""

import io
import re

from plaso.containers import events
from plaso.filters import event_filter
from plaso.lib import errors


class TaggingFile:
    """Tagging file that defines one or more event tagging rules."""

    # A line with no indent is a tag name.
    _TAG_LABEL_LINE = re.compile(r"^(\w+)")

    # A line with leading indent is one of the rules for the preceding tag.
    _TAG_RULE_LINE = re.compile(r"^\s+(.+)")

    # If any of these words are in the query then it's probably objectfilter.
    _OBJECTFILTER_WORDS = re.compile(
        r"\s(is|isnot|equals|notequals|inset|notinset|contains|notcontains)\s"
    )

    def __init__(self, path):
        """Initializes a tagging file.

        Args:
          path (str): path to a file that contains one or more event tagging rules.
        """
        super().__init__()
        self._path = path

    def GetEventTaggingRules(self):
        """Retrieves the event tagging rules from the tagging file.

        Returns:
          dict[str, EventObjectFilter]: tagging rules, that consists of one or more
              filter objects per label.

        Raises:
          TaggingFileError: if a filter expression cannot be compiled.
        """
        rules_per_label = {}

        label_name = None
        with io.open(self._path, "r", encoding="utf-8") as tagging_file:
            for line in tagging_file.readlines():
                line = line.rstrip()

                stripped_line = line.lstrip()
                if not stripped_line:
                    label_name = None
                    continue

                if stripped_line[0] == "#":
                    continue

                if not line[0].isspace():
                    label_name = line
                    rules_per_label[label_name] = []

                elif label_name:
                    rules_per_label[label_name].append(stripped_line)

        filter_objects_per_label = {}

        for label_name, rules in rules_per_label.items():
            filter_object = event_filter.EventObjectFilter()

            try:
                filter_rule = " OR ".join([f"({rule:s})" for rule in rules])
                filter_object.CompileFilter(filter_rule)
            except errors.ParseError as exception:
                raise errors.TaggingFileError(
                    f"Unable to compile filter for label: {label_name:s} with error: "
                    f"{exception!s}"
                )

            # TODO: change other code remove list around filter_object
            filter_objects_per_label[label_name] = [filter_object]

        return filter_objects_per_label

    def Validate(self):
        """Validates the labels and rules in the tagging file.

        Returns:
          list[tuple[int, str]]: line number and description of every label or
              rule that cannot be loaded, empty if all can be loaded.
        """
        findings = []
        event_tag = events.EventTag()
        label_names = set()

        label_name = None
        label_line_number = None
        number_of_rules = 0

        with open(self._path, "rb") as tagging_file:
            lines = tagging_file.read().split(b"\n")

        for line_number, line in enumerate(lines, start=1):
            try:
                line = line.decode("utf-8")
            except UnicodeDecodeError as exception:
                findings.append(
                    (
                        line_number,
                        f"Unable to decode line as UTF-8 with error: {exception!s}",
                    )
                )
                return findings

            line = line.rstrip()

            stripped_line = line.lstrip()
            if stripped_line and stripped_line[0] == "#":
                continue

            if not stripped_line or not line[0].isspace():
                # A blank line or a label line ends the rules of the previous label.
                if label_name and not number_of_rules:
                    findings.append(
                        (label_line_number, f"Label without rules: {label_name:s}")
                    )
                label_name = None

            if not stripped_line:
                continue

            if not line[0].isspace():
                if line in label_names:
                    findings.append(
                        (line_number, f"Label defined more than once: {line:s}")
                    )

                try:
                    event_tag.AddLabel(line)
                except ValueError as exception:
                    findings.append((line_number, str(exception)))

                label_names.add(line)
                label_name = line
                label_line_number = line_number
                number_of_rules = 0

            elif label_name:
                number_of_rules += 1

                filter_object = event_filter.EventObjectFilter()
                try:
                    filter_object.CompileFilter(stripped_line)
                except errors.ParseError as exception:
                    findings.append(
                        (
                            line_number,
                            f"Unable to compile rule: {stripped_line:s} with error: "
                            f"{exception!s}",
                        )
                    )

            else:
                findings.append(
                    (line_number, f"Rule not attached to a label: {stripped_line:s}")
                )

        if label_name and not number_of_rules:
            findings.append((label_line_number, f"Label without rules: {label_name:s}"))

        return findings
