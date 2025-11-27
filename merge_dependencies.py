#!/usr/bin/env python3

import yaml
import json
import sys


def load_yaml(filepath):
    with open(filepath, 'r') as f:
        # Strip YAML document markers like '---' and '...'
        lines = [line for line in f if line.strip() not in ['---', '...']]
    return yaml.safe_load('\n'.join(lines))


def load_json(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)


def save_json(data, filepath):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


def merge_taint_into_json(yaml_data, json_data, declmap_data):
    """
    yaml_data: taint YAML (has result-map with IncomingRegions)
    json_data: existing dep JSON (has 'variables' and 'cells')
    declmap_data: JSON with 'resolved' and 'static_c'

    Behavior:
      - resolved[impl_file] contains list of { "function": ..., "decl_file": ... }
      - static_c[impl_file] contains list of function names

      For each function F in yaml result-map:
        * if F in resolved[impl_file]:
            for each incoming src_file:
              add edge src_file -> impl_file
              add edge src_file -> decl_file
              (only if both files exist in json_data["variables"])
        * elif F in static_c[impl_file]:
            for each incoming src_file:
              add edge src_file -> impl_file
              (only if both files exist in json_data["variables"])
        * else:
            report error (function unmapped)
    """

    result_map = yaml_data.get('result-map', {})
    variables = json_data.get('variables', [])
    file_index = {file: idx for idx, file in enumerate(variables)}

    resolved_map = declmap_data.get("resolved", {})
    static_map = declmap_data.get("static_c", {})

    error_messages = []

    for symbol, props in result_map.items():
        func_name = symbol  # function name key in YAML
        impl_file = props.get('file')

        if not impl_file:
            error_messages.append(
                f"[no impl file] function '{func_name}' has no 'file' entry in YAML"
            )
            continue

        # impl file must exist in variables
        impl_idx = file_index.get(impl_file)
        if impl_idx is None:
            error_messages.append(
                f"[missing impl variable] function '{func_name}': "
                f"impl file '{impl_file}' not in variables list"
            )
            continue

        # Try to find declaration (resolved)
        decl_file = None
        for entry in resolved_map.get(impl_file, []):
            if entry.get("function") == func_name:
                decl_file = entry.get("decl_file")
                break

        is_static = False

        if decl_file is None:
            # Not resolved: check static
            if func_name in static_map.get(impl_file, []):
                is_static = True
            else:
                # Not in resolved and not in static_c -> error
                error_messages.append(
                    f"[unmapped function] function '{func_name}' (impl file '{impl_file}') "
                    f"not found in 'resolved' or 'static_c'"
                )
                continue

        incoming_regions = props.get('IncomingRegions', {}) or {}

        for src_path, value in incoming_regions.items():
            # src_path looks like "toxcore/foo.c: 42"
            src_file = src_path.split(':')[0].strip()
            src_idx = file_index.get(src_file)

            if src_idx is None:
                error_messages.append(
                    f"[missing src variable] function '{func_name}': "
                    f"src file '{src_file}' not in variables list"
                )
                continue

            # Edge 1: src -> impl (always for functions we actually handle)
            json_data['cells'].append({
                "src": src_idx,
                "dest": impl_idx,
                "values": {
                    "Dataflow": float(value)
                }
            })

            # Edge 2: src -> decl (only for resolved, non-static)
            if not is_static and decl_file:
                decl_idx = file_index.get(decl_file)
                if decl_idx is None:
                    error_messages.append(
                        f"[missing decl variable] function '{func_name}': "
                        f"decl file '{decl_file}' not in variables list"
                    )
                    continue

                json_data['cells'].append({
                    "src": src_idx,
                    "dest": decl_idx,
                    "values": {
                        "Dataflow": float(value)
                    }
                })

    # Dump all errors to stderr
    """
    if error_messages:
        sys.stderr.write("Errors during taint merge:\n")
        for msg in error_messages:
            sys.stderr.write("  " + msg + "\n")"""

    return json_data


def main(yaml_path, json_path, declmap_path, output_path):
    yaml_data = load_yaml(yaml_path)
    json_data = load_json(json_path)
    declmap_data = load_json(declmap_path)

    merged_data = merge_taint_into_json(yaml_data, json_data, declmap_data)
    save_json(merged_data, output_path)


if __name__ == "__main__":
    # Usage:
    #   python merge_taint.py taint.yml deps.json declmap.json out.json
    if len(sys.argv) != 5:
        print("Usage: python merge_taint.py <input_yaml> <input_json> <declmap_json> <combined_output.json>")
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
