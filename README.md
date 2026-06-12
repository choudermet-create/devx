# VCA Workbook Validator

This project reads a VCA Excel workbook, validates the workbook data, and generates a JSON payload that can be used as the starting point for Zerto API automation.

## What It Does

- Loads the VCA workbook from the `files` folder.
- Extracts data from the workbook sheets.
- Validates the workbook data against the VCA rules.
- Prints user-friendly validation results in the terminal.
- Generates JSON output files every time `main.py` runs.

## Validated Sheets

- `Zerto Data`
- `Hypervisor Data`
- `Default VPG Settings`
- `Recovery ZVM Sites`
- `VPGs`
- `VM Replication`
- `VM Storage`
- `VM NICs`

## Project Structure

```text
.
├── config.py
├── extraction/
├── files/
├── json_output.py
├── ingestion/
├── main.py
├── outputs/
├── requirements.txt
└── validation/
```

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run

```bash
python3 main.py
```

The script prints validation results and writes the JSON output to:

```text
outputs/vca_check_dump.json
outputs/zerto_api_payload.json
```

It also appends detailed run logs to:

```text
outputs/vca_check.log
```

## Changing the Workbook File

If the Excel file name changes, update the workbook path in both files:

```text
main.py
json_output.py
```

Current pattern:

```python
excel_file = "files/API Sample - VCA Data - Master.xlsx"
```

## VM NICs Validation

The `VM NICs` sheet is validated after workbook defaults are applied. Blank NIC-level failover values can inherit from the matching VPG, `Recovery ZVM Sites`, and then `Default VPG Settings`.

Because of this, a validation error may be reported against a `VM_NICs` table row even when the visible cell on the `VM NICs` sheet is blank. In that case, check the inherited value in the VPG's recovery site row on `Recovery ZVM Sites`, or in `Default VPG Settings`.

NIC failover settings are validated as two parallel groups:

- `Failover Live / Move`
- `Failover Test`

For each group, network names must exist in the recovery networks for the VPG's recovery site. IP address, gateway, and DNS server fields must be valid IPv4 addresses. Subnet mask fields must be valid IPv4 subnet masks.

When `Change vNIC IP Config` is `Yes, DHCP`, the IP address, subnet mask, default gateway, DNS server, and DNS suffix fields for that group must be blank.

When `Change vNIC IP Config` is `Yes, Static`, the IP address, subnet mask, default gateway, DNS server, and DNS suffix fields for that group must be present. The default gateway must also be valid for the IP address and subnet mask. For example, `192.168.34.55` with subnet mask `255.255.255.0` needs a gateway in the `192.168.34.x` subnet, such as `192.168.34.1` or `192.168.34.254`.

## Output

The project writes two JSON files.

`outputs/vca_check_dump.json` is the full diagnostic dump. It includes validation status, validation messages, reference data, raw workbook candidate payloads, and defaults-applied candidate payloads.

`outputs/zerto_api_payload.json` is the cleaner API handoff file. It is shaped around the Zerto 10.9 Swagger `VpgSettingsApi` grammar. It contains a `vpgSettings` list, where each item uses Zerto-style sections such as `basic`, `scripting`, `bootGroups`, `journal`, `scratch`, `recovery`, `networks`, and `vms`.

Internal validation metadata, such as table row IDs and table names, is used only for terminal error messages and the diagnostic dump. It is not included in the clean API payload file.

Important: the JSON dump uses literal names from the workbook, such as site names, VM names, host names, datastore names, network names, folder names, and boot order group names. The API program must resolve those names to Zerto, vCenter, or hypervisor internal identifiers before creating objects. If a name lookup returns multiple matching objects, the API program must fail with an ambiguity error instead of choosing one automatically.

The diagnostic dump includes both raw workbook candidate payloads and resolved candidate payloads. The resolved section applies workbook defaults where possible so blank inherited fields have effective values for API handoff.

The API payload keeps literal names in Zerto identifier-shaped fields such as `protectedSiteIdentifier`, `recoverySiteIdentifier`, `defaultHostIdentifier`, `datastoreIdentifier`, `networkIdentifier`, `vmIdentifier`, `volumeIdentifier`, and `nicIdentifier`. The downstream API program must replace those literal names with real identifiers before making Zerto API calls.

The API payload also converts workbook values into Zerto-style units where the Swagger expects them, such as RPO in seconds, journal history in hours, journal size limits in MB, and Yes/No values as booleans.

## Notes

- Validation errors are reported with the exact workbook table name and table row ID where possible.
- The JSON output is generated every time `main.py` runs.
- The log file records extraction counts, validation pass/fail status, detailed validation errors, and JSON output generation.
- The project currently validates workbook readiness; the Zerto API creation workflow is the next implementation phase.
