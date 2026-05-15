#!/usr/bin/env python3
"""Script to extract the event data attribute containers schema."""

import argparse
import importlib
import inspect
import logging
import pkgutil
import sys

from plaso.containers import events


class EventDataAttributeContainersSchemaExtractor:
    """Event data attribute containers schema extractor."""

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

    argument_parser.parse_args()

    extractor = EventDataAttributeContainersSchemaExtractor()

    attribute_containers = extractor.GetAttributeContainers()
    if not attribute_containers:
        print("Unable to determine event data attribute containers")
        return 1

    schema = extractor.FormatSchema(attribute_containers)
    print(schema)

    return 0


if __name__ == "__main__":
    sys.exit(Main())
