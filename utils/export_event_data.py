#!/usr/bin/env python3
"""Script to extract the event data attribute containers schema."""

import argparse
import importlib
import inspect
import logging
import pkgutil
import re
import sys

from plaso.containers import events


class EventDataAttributeContainersSchemaExtractor:
    """Event data attribute containers schema extractor.

    Attributes:
      number_of_documentation_issues (int): number of event data attribute
          documentation issues found while formatting the schema.
    """

    # Name at the start of an entry of the "Attributes:" docstring section,
    # such as "name (str): description." or "name: description.".
    _ATTRIBUTE_NAME_RE = re.compile(r"(?P<name>\w+)\s*[(:]")

    def __init__(self):
        """Initializes an event data attribute containers schema extractor."""
        super().__init__()
        self.number_of_documentation_issues = 0

    def _CheckDocumentation(self, cls, event_data):
        """Checks that the event data attributes are documented.

        An attribute documented in a parent event data class counts as
        documented. Attributes documented but not defined are only reported
        for the docstring of the class itself. Issues are logged as warnings and
        counted.

        Args:
          cls (class): event data attribute container class.
          event_data (EventData): event data attribute container.
        """
        defined_names = {
            name for name in event_data.GetAttributeNames() if name and name[0] != "_"
        }

        own_documented_names = self._GetDocumentedAttributeNames(cls)

        documented_names = set(own_documented_names)
        for parent_class in cls.__mro__[1:]:
            if issubclass(parent_class, events.EventData):
                documented_names.update(self._GetDocumentedAttributeNames(parent_class))

        description = f"{cls.__name__:s} ({cls.DATA_TYPE:s})"

        undocumented_names = defined_names - documented_names
        if undocumented_names:
            names = ", ".join(sorted(undocumented_names))
            logging.warning(f"{description:s}: undocumented attributes: {names:s}")
            self.number_of_documentation_issues += 1

        undefined_names = own_documented_names - defined_names
        if undefined_names:
            names = ", ".join(sorted(undefined_names))
            logging.warning(
                f"{description:s}: documented but undefined attributes: {names:s}"
            )
            self.number_of_documentation_issues += 1

    def _GetClassesFromPackage(self, package, base_class):
        """Retrieves event data attribute containers from a package.

        Args:
          package (list[str]): package name segments such as ["plaso", "parsers"].
          base_class (class): base class.

        Returns:
          list[class]: classes.
        """
        classes = []
        package_path = "/".join(package)
        for _, name, is_package in pkgutil.iter_modules(path=[package_path]):
            if package_path == "plaso/containers" and name in ("errors", "events"):
                continue

            sub_package = list(package)
            sub_package.append(name)
            if is_package:
                sub_classes = self._GetClassesFromPackage(sub_package, base_class)
                classes.extend(sub_classes)
            else:
                module_path = ".".join(sub_package)
                try:
                    module_object = importlib.import_module(module_path)
                except ModuleNotFoundError:
                    continue

                for _, cls in inspect.getmembers(module_object, inspect.isclass):
                    if issubclass(cls, base_class):
                        classes.append(cls)

        return classes

    def _GetDocumentedAttributeNames(self, cls):
        """Retrieves the attribute names documented in a class docstring.

        Only the docstring of the class itself is read, not the docstrings of
        its parent classes.

        Args:
          cls (class): class.

        Returns:
          set[str]: names of the attributes in the "Attributes:" section of the
              docstring.
        """
        attribute_names = set()

        in_section = False
        entry_indentation = None

        docstring = inspect.cleandoc(cls.__doc__ or "")
        for line in docstring.splitlines():
            stripped_line = line.strip()
            if stripped_line == "Attributes:":
                in_section = True
                continue

            if not in_section or not stripped_line:
                continue

            indentation = len(line) - len(line.lstrip())
            if indentation == 0:
                # A line that is not indented starts the next section.
                break

            # The first entry defines the indentation of the entries, lines that
            # are indented further continue the description of an entry.
            if entry_indentation is None:
                entry_indentation = indentation

            if indentation == entry_indentation:
                match = self._ATTRIBUTE_NAME_RE.match(stripped_line)
                if match:
                    attribute_names.add(match.group("name"))

        return attribute_names

    def FormatSchema(self, attribute_containers):
        """Formats the event data attribute containers as a schema.

        Args:
          attribute_containers (list[class]): event data attribute container
              classes.

        Returns:
          str: event data schema.
        """
        lines = []

        for cls in sorted(attribute_containers, key=lambda cls: cls.DATA_TYPE):
            try:
                event_data = cls()
            except TypeError:
                logging.warning(f"Unable to inspect data type: {cls.DATA_TYPE:s}")
                continue

            self._CheckDocumentation(cls, event_data)

            lines.append(f"{event_data.data_type:s}")
            for name in sorted(event_data.GetAttributeNames()):
                if name and name[0] != "_":
                    lines.append(f"  {name:s}")
            lines.append("")

        return "\n".join(lines)

    def GetAttributeContainers(self):
        """Retrieves event data attribute containers from Plaso.

        Returns:
          list[class]: event data attribute container classes.
        """
        return self._GetClassesFromPackage(["plaso"], events.EventData)


def Main():
    """The main program function.

    Returns:
      int: exit code that is provided to sys.exit().
    """
    argument_parser = argparse.ArgumentParser(
        description=("Extract the event data schema from Plaso.")
    )
    argument_parser.add_argument(
        "--strict",
        dest="strict",
        action="store_true",
        default=False,
        help=(
            "return an error if the event data attributes are not correctly "
            "documented."
        ),
    )
    options = argument_parser.parse_args()

    extractor = EventDataAttributeContainersSchemaExtractor()

    attribute_containers = extractor.GetAttributeContainers()
    if not attribute_containers:
        print("Unable to determine event data attribute containers")
        return 1

    schema = extractor.FormatSchema(attribute_containers)
    print(schema)

    if options.strict and extractor.number_of_documentation_issues:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(Main())
