#!/usr/bin/env python3

import sys
import json
from pathlib import Path


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def build_impl_lookup(impl_map):
    """
    Build (function, impl_file) -> decl_file lookup from implement_map.json

    Expected structure:
    {
      "fun_impl_to_decl": [
        {"function": "PCPDynamicMeters_init",
         "impl_file": "pcp/PCPDynamicMeter.c",
         "decl_file": "pcp/PCPDynamicMeter.h"},
        ...
      ],
      ...
    }
    """
    lookup = {}
    for entry in impl_map.get("fun_impl_to_decl", []):
        fun = entry.get("function")
        impl = entry.get("impl_file")
        decl = entry.get("decl_file")
        if not (fun and impl and decl):
            continue
        key = (fun, impl)
        lookup[key] = decl
    return lookup


def annotate_functions(yaml_map, impl_lookup):
    """
    yaml_map: JSON like the snippet you posted:
      {
        "stats": { ... },
        "incoming_files": [...],
        "file_to_defined_functions": {
          "args.c": ["arg_init", ...],
          ...
        }
      }

    impl_lookup: (function, impl_file) -> decl_file
    """

    file_to_defined_functions = yaml_map.get("file_to_defined_functions", {})

    resolved = {}    # impl_file -> list of {function, decl_file}
    unresolved = {}  # impl_file -> list of function names

    total_functions = 0
    resolved_count = 0
    unresolved_count = 0

    for impl_file, fun_list in file_to_defined_functions.items():
        for fun in fun_list:
            total_functions += 1
            key = (fun, impl_file)
            decl_file = impl_lookup.get(key)

            if decl_file:
                resolved.setdefault(impl_file, []).append({
                    "function": fun,
                    "decl_file": decl_file
                })
                resolved_count += 1
            else:
                unresolved.setdefault(impl_file, []).append(fun)
                unresolved_count += 1

    stats = {
        "num_functions": total_functions,
        "num_resolved": resolved_count,
        "num_unresolved": unresolved_count,
        "num_impl_files": len(file_to_defined_functions),
        "num_impl_files_with_unresolved": len(unresolved),
    }

    return {
        "stats": stats,
        "resolved": resolved,
        "unresolved": unresolved,
    }


def main():
    if len(sys.argv) != 4:
        print(
            f"Usage: {sys.argv[0]} <vara_functions.json> <implement_map.json> <output.json>"
        )
        sys.exit(1)

    vara_fn_path = sys.argv[1]
    impl_map_path = sys.argv[2]
    out_path = sys.argv[3]

    vara_map = load_json(vara_fn_path)
    impl_map = load_json(impl_map_path)

    impl_lookup = build_impl_lookup(impl_map)
    annotated = annotate_functions(vara_map, impl_lookup)

    # Print stats to stdout
    s = annotated["stats"]
    print("Total Impl files    :", s["num_impl_files"])
    print("Impl files w/ misses:", s["num_impl_files_with_unresolved"])
    print("Total functions     :", s["num_functions"])
    print("Resolved            :", s["num_resolved"])
    print("Unresolved          :", s["num_unresolved"])

    # Write full JSON
    with Path(out_path).open("w", encoding="utf-8") as f:
        json.dump(annotated, f, indent=2)


if __name__ == "__main__":
    main()
