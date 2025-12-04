#!/usr/bin/env python3
import json
import sys

def load_json(path):
    with open(path, "r") as f:
        return json.load(f)

def save_json(obj, path):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def filter_cochange(input_path, output_path, threshold=5):
    data = load_json(input_path)
    new_cells = []

    for cell in data.get("cells", []):
        vals = cell.get("values", {})

        # If there's a Cochange value, apply the threshold
        if "Cochange" in vals:
            if vals["Cochange"] <= threshold:
                # remove Cochange from this cell
                del vals["Cochange"]

        # If there are still any relations left in this cell, keep it
        if vals:
            cell["values"] = vals
            new_cells.append(cell)

    data["cells"] = new_cells
    save_json(data, output_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python filter_cochange.py <input_dep.json> <output_dep.json>")
        sys.exit(1)

    filter_cochange(sys.argv[1], sys.argv[2], threshold=10)
