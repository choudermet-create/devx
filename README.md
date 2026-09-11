# VCA Check

VCA Check reads a VCA Excel workbook, checks the data, and writes JSON files that can be handed to the next step in the workflow.

The main handoff file for VCA Run is:

```text
outputs/VCA.json
```

VCA Run is expected to take that manifest, resolve workbook names to real platform identifiers, and then prepare the final payload used to create objects in Zerto.

## What It Does

- Opens the workbook from the `files` folder.
- Extracts the workbook sheets into Python data structures.
- Validates the extracted data against the VCA rules.
- Stops at the first failed validation section.
- Writes JSON output only when validation passes.

## Validated Sheets

Validation currently runs in this order:

```text
Zerto Data
Hypervisor Data
Default VPG Settings
Recovery ZVM Sites
VPGs
VM Replication
VM Storage
VM NICs
```

The order matters. Later sheets often depend on reference data from earlier sheets, so the program stops when a section fails instead of continuing with validations that are likely to cascade.

## Project Structure

```text
.
├── config.py
├── extraction/
├── files/
├── ingestion/
├── main.py
├── outputs/
├── payload/
├── requirements.txt
└── validation/
```

The important folders are:

```text
ingestion/    workbook loading and required sheet checks
extraction/   reading workbook data into Python dictionaries/lists
validation/   workbook validation rules
payload/      JSON output builders
outputs/      generated files
```

## Setup

### Linux

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Windows

Install Python if it is not already installed, then open PowerShell in the project directory.

Create and activate a virtual environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
py -m pip install -r requirements.txt
```

## Run

### Linux

Supply the workbook with the required `--input-file` option:

```bash
python3 main.py --input-file "files/your-workbook.xlsx"
```

You can also supply just a filename or an absolute path:

```bash
python3 main.py --input-file "VCA Data - v0.111.xlsx"
python3 main.py --input-file "/path/to/VCA Data.xlsx"
```

### Windows

Supply the workbook with the required `--input-file` option:

```powershell
py main.py --input-file "files\your-workbook.xlsx"
```

You can also supply just a filename or an absolute path:

```powershell
py main.py --input-file "VCA Data - v0.111.xlsx"
py main.py --input-file "C:\path\to\VCA Data.xlsx"
```

The `--input-file` option is required. Use `python3 main.py --help` on Linux or
`py main.py --help` on Windows to show the command-line usage. If the selected
workbook does not exist, the program reports the resolved path and exits before
validation starts.

If validation passes, the program writes:

```text
outputs/vca_check_dump.json
outputs/VCA.json
```

If validation fails, the program prints the failed section and stops. The JSON output files are not regenerated from invalid data.

## Workbook File

VCA Check takes its workbook only from the required `--input-file` option. Supply
either a filename in the `files` folder or a relative or absolute path; no
source-code change is required.

## Output Files

### `outputs/vca_check_dump.json`

This is the diagnostic dump. It is useful when you need to understand what the program extracted and how defaults were applied.

It includes:

- source workbook name
- validation status
- validation details
- reference data
- raw candidate payload data
- resolved candidate payload data

The resolved data is important because some workbook fields can be blank and still have an effective value inherited from another sheet.

### `outputs/VCA.json`

This is the VCA Run manifest. It uses PascalCase section names and is written as a list of VPG definitions.

Example section names:

```text
Basic
BootGroup
Scripting
Recovery
Journal
Scratch
Networks
VMs
```

This is the file VCA Run should consume. It contains the validated VPG definitions from the workbook. VCA Run should resolve names such as sites, VMs, hosts, datastores, networks, folders, volumes, and NICs into real identifiers before making the POST/PUT API calls to Zerto.

## Defaults and Effective Values

Some sheets allow values to be inherited.

For example, a VPG row may inherit defaults from:

```text
Recovery ZVM Sites
Default VPG Settings
```

VM-level rows can also inherit values from the VPG they belong to.

That means a validation error may sometimes appear for a row even when the visible cell on that sheet is blank. In that case, check:

```text
outputs/vca_check_dump.json
```

Look at the resolved candidate payload section first, then trace the value back to the workbook default row it came from.

## Notes

- `main.py` is the normal entry point.
- Validation is the gate before JSON generation.
- `payload/manifest_output.py` builds the VCA Run manifest.
- `payload/json_output.py` builds the diagnostic dump.
- The project currently checks workbook readiness and prepares handoff JSON. Creating objects in Zerto belongs to the VCA Run side.
