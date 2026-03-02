# thesis-scripts
Scripts used in the Bachelor's thesis to preprocess the data

# Analysis Pipeline

Preparing data for DRSpaces analysis

## Requirements
The pipeline needs the following inputs:

- **Project repository/source code**.
- **DV8 (tool) JSON file** – DV8's analysis on a repository produces a dependency file.
- **VaRA (tool) YAML file** – contains data-flow interactions produced by VaRA analysis.

---

## Pipeline Overview
### Step 1:
We extract all occurrencies of `Implement` dependency that were found in DV8's structural analysis to build a lookup table:
* Run **extract_implement.py**
  * Input: DV8 JSON file (Produced by DV8 structural analysis of a provided repo) 
  * Output: produces `implement_map.json`
```console
   python extract_implement.py dv8_dep.json implement_map.json  
```
---
### Step 2:
We extract all occurrencies of unique symbols in the data-flow report provided by VaRA. These symbols will be looked up.
* Run **filter_functions_present_DF.py**
  * Input: VaRA YAML (Data-Flow output)  
  * Output: produces `filtered_functions.json`
```console
   python filer_functions_present_DF.py vara_DF.yaml filtered_functions.json
```
---
### Step 3:
All functions are resolved. These are functions that require a second dependency edge to the header file using `Implement`, as well as private and static function that do not require a second edge.
* Run **resolve_static_local.py** with  
  * Input: `filtered_functions.json`, `implement_map.json` and `<src_root>`  
  * Output: produces `declmap.json` (including any remaining unresolved symbols)
All remaining symbols are put into an cell called "unresolved".
```console
   python resolve_static_local.py filtered_functions.json implement_map.json 'path to src root' declmap.json
```
---
### Step 4:
* Manually resolve the remaining unresolved entries in `declmap.json` by locating those symbols in the data-flow Yaml file and inspecting the source code for the second dependency edge.

---
### Step 5:
This step is optional. It is to trim co-changes by a specified threshold for when the history data is too large:
* (optional) Run **filter_cochange.py**
  * Input: DV8 JSON file
  * Output: `output.json`
```console
   python filter_cochange.py dv8_dep.json output.json    
```
---
### Step 6:
* Run **merge_dependencies.py** with  
  * Input: VaRA YAML file, DV8 JSON file/Modified file after co-change filter (optional step) and `declmap.json`  
  * Output: produces `combined_output.json` (final merged dependency file)
```console
  python merge_dependencies.py vara_DF.yaml dv8_dep.json combined_output.json 
```
---
### Step 7:
* Feed **combined_output.json** into DV8’s file analysis mode  
  → performs new analysis that contains Data-flow

---

## Remarks On DV8
DV8 preforms an analysis that extracts the structural dependencies of a system and co-changes between files.
It contains two analysis modes:
* **Analyze Software From a Repo**:
  * This analysis mode requires a repository that gives DV8 access to the system and its history.
  * It outputs a folder that contains:
    - `.dv8_proj`: a file that can be used to access this analysis in DV8 directly later
    - `dv8-analysis-result`: A folder containing various analysis results
    - `depends-output`: A folder containing dependency files of the system, the json file in this folder is the one mentioned as "DV8 JSON file" in the pipeline above (also `dv8_dep.json`).

* **Analyze Software From Files**:
  * This analysis mode requires a dependency JSON file that contains all the dependencies of the system. This is the mode we used in the final step of the pipeline after we merge data-flow with the structural dependencies.
  * Its output is similar to the other mode.

