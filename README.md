# thesis-scripts
Scripts used in the Bachelor's thesis to preprocess the data

# Analysis Pipeline

Preparing data for DRSpaces analysis

## Requirements
The pipeline needs the following inputs:

- **Project repository/source code**.
- **DV8 (tool) structural JSON** – DV8's analysis on a repository produces a dependency file.
- **VaRA (tool) data-flow YAML** – contains data-flow interactions.

---

## Pipeline Overview

- Run **extract_implement.py** on the DV8 structural JSON  
  → produces `implement_map.json`

- Run **filter_functions_present_DF.py** on the VaRA YAML  
  → produces `filtered_functions.json`

- Run **resolve_static_local.py** with  
  `filtered_functions.json`, `implement_map.json`, and `<src_root>`  
  → produces `declmap.json` (including any remaining unresolved functions)

- Manually resolve the remaining unresolved entries in `declmap.json` by inspecting the source code

- Run **merge_dependencies.py** with  
  VaRA YAML, DV8 JSON, and `declmap.json`  
  → produces `combined_output.json` (final merged dependency graph)
  
- Feed **combined_output.json** into DV8’s file analysis mode  
  → performs new analysis that contains Data-flow
