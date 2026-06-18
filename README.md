# VCA Check

VCA Check reads a VCA Excel workbook, checks the data, and writes JSON files that can be handed to the next step in the workflow.

The main handoff file for VCA Run is:

```text
outputs/vca_run_manifest.json
```

VCA Run is expected to take that manifest, resolve workbook names to real platform identifiers, and then prepare the final payload used to create objects in Zerto.

## What It Does

- Opens the workbook from the `files` folder.
- Extracts the workbook sheets into Python data structures.
- Validates the extracted data against the VCA rules.
- Stops at the first failed validation section.
- Writes JSON output only when validation passes.
- Writes a fresh run log to `outputs/vca_check.log`.

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

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 main.py
```

If validation passes, the program writes:

```text
outputs/vca_check_dump.json
outputs/zerto_api_payload.json
outputs/vca_run_manifest.json
```

It also writes a fresh log file for the run:

```text
outputs/vca_check.log
```

If validation fails, the program prints the failed section and stops. The JSON output files are not regenerated from invalid data.

## Workbook File

The workbook path is set in `main.py`:

```python
excel_file = "files/API Sample - VCA Data - Master.xlsx"
```

Change that value if you want to run VCA Check against a different workbook.

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

### `outputs/zerto_api_payload.json`

This is the older Zerto-shaped payload output. It uses Zerto-style section names such as:

```text
basic
scripting
bootGroups
journal
scratch
recovery
networks
vms
```

This file still contains workbook names in identifier-like fields. Those names are not real Zerto or vCenter identifiers yet.

### `outputs/vca_run_manifest.json`

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

This is the file VCA Run should consume. VCA Run should resolve names such as site names, VM names, host names, datastore names, network names, folder names, boot order groups, volumes, and NICs into real identifiers before calling Zerto.

If a lookup returns more than one match, VCA Run should fail with an ambiguity error instead of guessing.

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

## VM NIC Validation

NIC failover settings are checked in two groups:

```text
Failover Live / Move
Failover Test
```

For each group:

- network names must exist for the VPG recovery site
- IP address fields must be valid IPv4 addresses
- subnet mask fields must be valid IPv4 subnet masks
- default gateway must belong to the same subnet as the IP address and mask

When `Change vNIC IP Config` is `Yes, DHCP`, the IP address, subnet mask, gateway, DNS server, and DNS suffix fields for that group must be blank.

When `Change vNIC IP Config` is `Yes, Static`, those fields must be present.

Example:

```text
IP Address: 192.168.34.55
Subnet Mask: 255.255.255.0
```

Valid gateways would be in the same `192.168.34.x` subnet, such as:

```text
192.168.34.1
192.168.34.254
```

## Notes

- `main.py` is the normal entry point.
- Validation is the gate before JSON generation.
- `payload/manifest_output.py` builds the VCA Run manifest.
- `payload/json_output.py` builds the diagnostic dump and the older Zerto-shaped payload.
- `outputs/vca_check.log` is recreated on each run.
- The project currently checks workbook readiness and prepares handoff JSON. Creating objects in Zerto belongs to the VCA Run side.
