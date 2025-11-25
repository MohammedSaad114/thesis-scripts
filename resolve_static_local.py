#!/usr/bin/env python3

import sys
import json
import re
from pathlib import Path


# -------------------------------
# Regexes
# -------------------------------

STATIC_REGEX = re.compile(
    r'\bstatic\b\s+(?:inline\s+)?[^\(]*?\b(\w+)\s*\(',
    re.MULTILINE | re.DOTALL
)

FUNC_DEF_REGEX = re.compile(
    r'^\s*[\w\*\s]+\b(\w+)\s*\([^;]*\)\s*\{',
    re.MULTILINE
)

# -------------------------------
# Helper functions
# -------------------------------

def load_json(p):
    with Path(p).open("r", encoding="utf-8") as f:
        return json.load(f)


def build_impl_lookup(impl_map):
    """Build (function, impl_file) -> decl_file."""
    lookup = {}
    for entry in impl_map.get("fun_impl_to_decl", []):
        fun = entry.get("function")
        impl = entry.get("impl_file")
        decl = entry.get("decl_file")
        if fun and impl and decl:
            lookup[(fun, impl)] = decl
    return lookup


def read_file(path: Path, cache: dict):
    """Cached file reader."""
    if path in cache:
        return cache[path]
    if not path.is_file():
        cache[path] = None
        return None
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        cache[path] = None
        return None
    cache[path] = text
    return text


def get_static_functions(text: str):
    return set(STATIC_REGEX.findall(text))


# -------------------------------
# Core logic
# -------------------------------

def annotate(vara_map, impl_lookup, src_root: Path):

    file_to_funs = vara_map.get("file_to_defined_functions", {})

    resolved = {}
    static_c = {}
    local_c = {}      # new bucket
    unresolved = {}
    file_cache = {}

    stats = {
        "num_functions": 0,
        "num_resolved": 0,
        "num_static_c": 0,
        "num_local_c": 0,
        "num_unresolved": 0,
        "num_impl_files": len(file_to_funs),
        "num_impl_files_with_unresolved": 0,
    }

    for impl_file, funs in file_to_funs.items():
        impl_path = src_root / impl_file
        text = read_file(impl_path, file_cache)

        static_defs = get_static_functions(text) if text else set()
        func_defs = set(FUNC_DEF_REGEX.findall(text)) if text else set()

        for fun in funs:
            stats["num_functions"] += 1

            # 1) Implement relation works
            decl = impl_lookup.get((fun, impl_file))
            if decl:
                resolved.setdefault(impl_file, []).append({
                    "function": fun,
                    "decl_file": decl,
                })
                stats["num_resolved"] += 1
                continue

            # 2) Static local function in .c
            if fun in static_defs:
                static_c.setdefault(impl_file, []).append(fun)
                stats["num_static_c"] += 1
                continue

            # 3) Non-static function defined in this .c (no header declaration)
            if fun in func_defs:
                local_c.setdefault(impl_file, []).append(fun)
                stats["num_local_c"] += 1
                continue

            # 4) Truly unresolved
            unresolved.setdefault(impl_file, []).append(fun)
            stats["num_unresolved"] += 1

    stats["num_impl_files_with_unresolved"] = len(unresolved)

    return {
        "stats": stats,
        "resolved": resolved,
        "static_c": static_c,
        "local_c": local_c,
        "unresolved": unresolved,
    }



# -------------------------------
# CLI entry
# -------------------------------

def main():
    if len(sys.argv) != 5:
        print(f"Usage: {sys.argv[0]} <vara.json> <impl_map.json> <src_root> <out.json>")
        sys.exit(1)

    vara = load_json(sys.argv[1])
    impl_map = load_json(sys.argv[2])
    src_root = Path(sys.argv[3])
    out = Path(sys.argv[4])

    lookup = build_impl_lookup(impl_map)
    annotated = annotate(vara, lookup, src_root)

    s = annotated["stats"]
    print("Total Impl files            :", s["num_impl_files"])
    print("Impl files w/ unresolved    :", s["num_impl_files_with_unresolved"])
    print("Total functions             :", s["num_functions"])
    print("Resolved (Implement)        :", s["num_resolved"])
    print("Static in .c                :", s["num_static_c"])
    print("Local or .h not found       :", s["num_local_c"])
    print("Unresolved                  :", s["num_unresolved"])

    with out.open("w", encoding="utf-8") as f:
        json.dump(annotated, f, indent=2)


if __name__ == "__main__":
    main()
