#!/usr/bin/env python3
"""Script to check the event data attribute containers schema."""

import argparse
import importlib
import inspect
import logging
import pkgutil
import sys

from plaso.containers import events
from plaso.output import formatting_helper


class EventDataAttributeContainersSchemaValidator:
    """Event data attribute containers schema validator."""

    _ALLOWED_OVERRIDES = frozenset(
        [
            # Used in l2tcsv, but is always 2.
            "version",
        ]
    )

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

    def CheckSchema(self, attribute_containers, reserved_names):
        """Checks the event data attribute containers schema.

        Args:
          attribute_containers (list[class]): event data attribute container
              classes.
          reserved_names (set[str]): reserved field names.

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

            conflicting_names = []
            for name in sorted(event_data.GetAttributeNames()):
                if name and name[0] != "_":
                    if name in reserved_names:
                        conflicting_names.append(name)

            if conflicting_names:
                names = ", ".join(conflicting_names)
                lines.append(f"{cls.DATA_TYPE:s} {{ {names:s} }}")

        return "\n".join(lines)

    def GetAttributeContainers(self):
        """Retrieves event data attribute containers from Plaso.

        Returns:
          list[class]: event data attribute container classes.
        """
        return self._GetClassesFromPackage(["plaso"], events.EventData)

    def GetFieldFormattingHelpers(self):
        """Retrieves field formatting helpers from Plaso.

        Returns:
          list[class]: field formatting helper classes.
        """
        return self._GetClassesFromPackage(
            ["plaso"], formatting_helper.FieldFormattingHelper
        )

    def GetReservedNames(self, formatting_helpers):
        """Determines the reserved field names from the field formatting helpers.

        Args:
          formatting_helpers (list[class]): field formatting helper classes.

        Returns:
          set[str]: reserved field names.
        """
        reserved_names = set()

        for cls in formatting_helpers:
            try:
                helper = cls()
            except TypeError:
                logging.warning(f"Unable to inspect: {cls.__name__:s}")
                continue

            # pylint: disable=protected-access
            for name in helper._FIELD_FORMAT_CALLBACKS.keys():
                if name not in self._ALLOWED_OVERRIDES:
                    reserved_names.add(name)

        return reserved_names


def Main():
    """The main program function.

    Returns:
      int: exit code that is provided to sys.exit().
    """
    argument_parser = argparse.ArgumentParser(
        description=("Checks the event data schema of Plaso.")
    )
    argument_parser.parse_args()

    validator = EventDataAttributeContainersSchemaValidator()

    formatting_helpers = validator.GetFieldFormattingHelpers()
    if not formatting_helpers:
        print("Unable to determine field formatting helpers")
        return 1

    reserved_names = validator.GetReservedNames(formatting_helpers)

    attribute_containers = validator.GetAttributeContainers()
    if not attribute_containers:
        print("Unable to determine event data attribute containers")
        return 1

    schema = validator.CheckSchema(attribute_containers, reserved_names)
    print(schema)

    return 0


if __name__ == "__main__":
    sys.exit(Main())
