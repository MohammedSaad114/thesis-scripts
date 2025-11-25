#!/usr/bin/env python3

import sys
import json
import yaml
from pathlib import Path


def yaml_to_maps(yaml_path, json_path):
    yaml_path = Path(yaml_path)
    json_path = Path(json_path)

    with yaml_path.open("r", encoding="utf-8") as f:
        docs = list(yaml.safe_load_all(f))

    # find the doc containing result-map
    result_doc = None
    for d in docs:
        if isinstance(d, dict) and "result-map" in d:
            result_doc = d
            break

    if result_doc is None:
        raise ValueError("No 'result-map' section found.")

    result_map = result_doc["result-map"]

    incoming_files = set()              # all files appearing in IncomingRegions
    file_to_defined_functions = {}      # file (from "file") -> set(functions it defines)
    functions = set()
    
    for key, entry in result_map.items():
        if not isinstance(entry, dict):
            continue

        func_name = entry.get("DemangledName", key)
        def_file = entry.get("file")
        functions.add(func_name)
        # mapping: file -> functions it DEFINES
        if def_file:
            file_to_defined_functions.setdefault(def_file, set()).add(func_name)
            

        # collect all incoming region files into one set
        incoming = entry.get("IncomingRegions") or {}
        incoming_files.update(incoming.keys())

    # build JSON-friendly structure
    output = {
          "stats": {
            "num_functions": len(functions),
            "num_files": len(
            file_to_defined_functions)
        },
        # single entry with all unique incoming region files
        "incoming_files": sorted(incoming_files),

        # mapping: file -> functions defined in that file
        "file_to_defined_functions": {
            f: sorted(funcs) for f, funcs in sorted(file_to_defined_functions.items())
        },
    }

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.yaml> <output.json>")
        sys.exit(1)

    yaml_to_maps(sys.argv[1], sys.argv[2])
