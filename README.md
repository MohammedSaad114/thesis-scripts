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
First, we extract occurrencies of `Implement` dependency that was found in DV8's structural analysis:
* Run **extract_implement.py**
  * Input: DV8 structural JSON (Produced by DV8 structural analysis of a provided repo) 
  * Output: produces `implement_map.json`

---

Next, we extract all occurrencies of unique symbols in the data-flow report provided by VaRA.
* Run **filter_functions_present_DF.py**
  * Input: VaRA YAML (Data-Flow output)  
  * Output: produces `filtered_functions.json`

---

Next, all functions are resolved. These are functions that require a second dependency edge to the header file using `Implement` or private and static function that do not require a second edge.
* Run **resolve_static_local.py** with  
  * Input: `filtered_functions.json`, `implement_map.json` and `<src_root>`  
  * Output: produces `declmap.json` (including any remaining unresolved symbols)
All remaining symbols are put into an cell called "unresolved".

---

* Manually resolve the remaining unresolved entries in `declmap.json` by locating those symbols in the data-flow Yaml file and inspecting the source code for the second dependency edge.

---

* Run **merge_dependencies.py** with  
  * Input: VaRA YAML output, DV8 JSON output and `declmap.json`  
  * Output: produces `combined_output.json` (final merged dependency file)

---

This step is optional to filter co-changes by a specified threshold:
* (optional) Run **filter_cochange.py**
  * Input: `combined_output.json`
  * Output: `combined_output.json`

---

* Feed **combined_output.json** into DV8’s file analysis mode  
  → performs new analysis that contains Data-flow
