#!/usr/bin/env python3
"""Script to sort a Plaso YAML file."""

import argparse
import os
import sys
import yaml


class SingleQuoteValueDumper(yaml.SafeDumper):
    """YAML dumper that single quotes string values."""

    def __init__(self, *args, **kwargs):
        """Initializes a YAML dumper."""
        super().__init__(*args, **kwargs)
        self._processing_key = False

    def represent_data(self, data):
        """Represent data."""
        if not isinstance(data, str):
            return super().represent_data(data)

        if self._processing_key:
            return self.represent_scalar("tag:yaml.org,2002:str", data)

        return self.represent_scalar("tag:yaml.org,2002:str", data, style="'")

    def represent_mapping(self, tag, mapping, flow_style=None):
        """Represent a mapping."""
        if hasattr(mapping, "items"):
            mapping = list(mapping.items())

        value = []
        node = yaml.MappingNode(tag, value, flow_style=flow_style)

        if self.alias_key is not None:
            self.represented_objects[self.alias_key] = node

        for item_key, item_value in mapping:
            self._processing_key = True
            node_key = self.represent_data(item_key)

            self._processing_key = False
            node_value = self.represent_data(item_value)

            value.append((node_key, node_value))

        return node


def Main():
    """The main program function.

    Returns:
      int: exit code that is provided to sys.exit().
    """
    argument_parser = argparse.ArgumentParser(description="Sorts a Plaso YAML file")

    argument_parser.add_argument(
        "yaml_file",
        type=str,
        help=("path to the Plaso YAML file."),
    )
    options = argument_parser.parse_args()

    if not os.path.isfile(options.yaml_file):
        print(f"No such file: {options.yaml_file:s}")
        return 1

    with open(options.yaml_file, encoding="utf8") as file_object:
        header = file_object.readline()
        if header == "# Plaso timeliner configuration.\n":
            pass
        elif not header.startswith("# Plaso ") or not header.endswith(
            " event formatters.\n"
        ):
            print("Unsupported Plaso YAML file format.")
            return 1

        yaml_documents = list(yaml.load_all(file_object, Loader=yaml.SafeLoader))

    key = "data_type"

    sorted_yaml_documents = sorted(
        yaml_documents,
        key=lambda yaml_document: (yaml_document.get(key, "") if yaml_document else ""),
    )
    with open(options.yaml_file, "w", encoding="utf8") as file_object:
        file_object.write(f"{header:s}---\n")
        yaml.dump_all(
            sorted_yaml_documents,
            file_object,
            Dumper=SingleQuoteValueDumper,
            sort_keys=False,
        )
    return 0


if __name__ == "__main__":
    sys.exit(Main())
