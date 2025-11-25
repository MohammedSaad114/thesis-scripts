#!/usr/bin/env python3

import sys
import json
from pathlib import Path


def extract_implement_map(input_json, output_json):
    in_path = Path(input_json)
    out_path = Path(output_json)

    with in_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    cells = data.get("cells", [])

    # Core mapping: (function, impl_file) -> decl_file
    fun_impl_to_decl = {}

    # Groupings
    impl_file_to_functions = {}  # impl_file -> set(functions)
    decl_file_to_functions = {}  # decl_file -> set(functions)

    for cell in cells:
        details = cell.get("details") or []
        for d in details:
            if d.get("type") != "Implement":
                continue

            src = d.get("src", {})
            dest = d.get("dest", {})

            impl_file = src.get("file")
            decl_file = dest.get("file")
            fun_src = src.get("object")
            fun_dst = dest.get("object")

            # Prefer src.object, fall back to dest.object
            fun_name = fun_src or fun_dst

            if not (fun_name and impl_file and decl_file):
                continue

            key = (fun_name, impl_file)
            fun_impl_to_decl[key] = decl_file

            impl_file_to_functions.setdefault(impl_file, set()).add(fun_name)
            decl_file_to_functions.setdefault(decl_file, set()).add(fun_name)

    # Build JSON-friendly structure (no tuple keys)
    fun_impl_to_decl_list = [
        {"function": fun, "impl_file": impl, "decl_file": decl}
        for (fun, impl), decl in sorted(fun_impl_to_decl.items())
    ]

    output = {
        "stats": {
            "num_relations": len(fun_impl_to_decl_list),
            "num_functions": len({fun for (fun, _) in fun_impl_to_decl.keys()}),
            "num_impl_files": len(impl_file_to_functions),
            "num_decl_files": len(decl_file_to_functions),
        },
        "fun_impl_to_decl": fun_impl_to_decl_list,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_structural.json> <output_implement_map.json>")
        sys.exit(1)

    extract_implement_map(sys.argv[1], sys.argv[2])
