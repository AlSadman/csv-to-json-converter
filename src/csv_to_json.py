#!/usr/bin/env python3
"""
CSV to JSON Converter

A robust, zero-dependency Python CLI utility for converting CSV files into JSON
with automatic type conversion, header validation, delimiter support, Unicode support,
dry-run preview mode, and overwrite protection.
"""

import argparse
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


class CSVToJSONError(Exception):
    """Custom exception class for CSV to JSON conversion errors."""
    pass


def parse_delimiter(delim_str: str) -> str:
    """
    Parse delimiter string, converting escaped sequences like '\\t' to actual characters.
    
    Args:
        delim_str: Raw delimiter input string.
        
    Returns:
        Unescaped delimiter string.
        
    Raises:
        CSVToJSONError: If delimiter is invalid or empty.
    """
    if not delim_str:
        raise CSVToJSONError("Delimiter cannot be empty.")
    
    # Handle literal backslash-t representation
    if delim_str == r"\t" or delim_str == "\\t":
        return "\t"
    elif delim_str == r"\n" or delim_str == "\\n":
        raise CSVToJSONError("Newline cannot be used as a CSV field delimiter.")
    elif delim_str == r"\r" or delim_str == "\\r":
        raise CSVToJSONError("Carriage return cannot be used as a CSV field delimiter.")
    
    if len(delim_str) > 1:
        raise CSVToJSONError(f"Multi-character delimiters are not supported: '{delim_str}'")
        
    return delim_str


def convert_value_type(val: str) -> Union[str, int, float, bool, None]:
    """
    Safely convert a string value to a Python native type (int, float, bool, None).
    
    Rules:
    - Boolean: 'true'/'false' (case-insensitive) -> True/False
    - Null: 'null' (case-insensitive) -> None
    - Integer: numeric digits, preserves leading zeros (e.g. '00123' stays str '00123')
    - Float: standard decimal representation, preserves leading zeros if applicable
    
    Args:
        val: String cell value from CSV.
        
    Returns:
        Converted value or original string.
    """
    if val is None:
        return None
        
    val_lower = val.strip().lower()
    
    # Boolean conversion
    if val_lower == "true":
        return True
    if val_lower == "false":
        return False
        
    # Null conversion
    if val_lower == "null":
        return None

    # Check for leading zero integer/numeric strings that should remain strings (e.g., ZIP codes, IDs: "00123", "01")
    # Exception: pure "0" or "0.123"
    trimmed_val = val.strip()
    
    # Integer check
    if trimmed_val.lstrip("-").isdigit():
        # Check if leading zero would be lost (e.g. "0123" vs "123", but "0" or "-0" is fine)
        digits_only = trimmed_val.lstrip("-")
        if len(digits_only) > 1 and digits_only.startswith("0"):
            return val  # Preserve as string
        try:
            return int(trimmed_val)
        except ValueError:
            pass
            
    # Float check
    try:
        float_val = float(trimmed_val)
        # Verify it looks like a valid float string and check for leading zero issues
        if "." in trimmed_val or "e" in trimmed_val.lower():
            # Check integer part before decimal for unwanted leading zeros (e.g., "007.85")
            parts = trimmed_val.lstrip("-").split(".")
            int_part = parts[0]
            if len(int_part) > 1 and int_part.startswith("0"):
                return val  # Preserve as string
            return float_val
    except ValueError:
        pass
        
    return val


def parse_and_validate_csv(
    file_path: Path, delimiter: str = ",", auto_type: bool = False
) -> Tuple[List[str], List[Dict[str, Any]], int]:
    """
    Read, parse, and strictly validate a CSV file.
    
    Args:
        file_path: Path to the input CSV file.
        delimiter: CSV field delimiter.
        auto_type: Whether to attempt automatic type conversion.
        
    Returns:
        Tuple of (headers list, list of row dictionaries, row count).
        
    Raises:
        CSVToJSONError: On missing file, directory input, empty CSV, duplicate/empty headers,
                        or row length mismatch.
    """
    if not file_path.exists():
        raise CSVToJSONError(f"Input CSV file does not exist: {file_path}")
        
    if file_path.is_dir():
        raise CSVToJSONError(f"Input path is a directory. Please provide a CSV file: {file_path}")
        
    try:
        # Use utf-8-sig to automatically handle and strip UTF-8 BOM if present
        with open(file_path, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.reader(f, delimiter=delimiter)
            
            try:
                headers = next(reader)
            except StopIteration:
                raise CSVToJSONError("CSV file is empty.")
                
            if not headers:
                raise CSVToJSONError("CSV file is empty.")
                
            # Check for completely empty header row or blank header names
            seen_headers = set()
            for idx, h in enumerate(headers):
                h_stripped = h.strip()
                if not h:
                    raise CSVToJSONError(f"Empty CSV header detected at column position {idx + 1}.")
                if h in seen_headers:
                    raise CSVToJSONError(f"Duplicate CSV header detected: '{h}'")
                seen_headers.add(h)
                
            rows: List[Dict[str, Any]] = []
            expected_col_count = len(headers)
            
            for row_idx, row in enumerate(reader, start=2):
                # Skip trailing completely blank lines
                if not row:
                    continue
                    
                if len(row) != expected_col_count:
                    raise CSVToJSONError(
                        f"Row {row_idx} contains {len(row)} fields, but {expected_col_count} headers were expected."
                    )
                    
                row_dict = {}
                for h, val in zip(headers, row):
                    if auto_type:
                        row_dict[h] = convert_value_type(val)
                    else:
                        row_dict[h] = val
                rows.append(row_dict)
                
            return headers, rows, len(rows)

    except UnicodeDecodeError as e:
        raise CSVToJSONError(f"Failed to decode file using UTF-8 encoding: {e}")
    except OSError as e:
        raise CSVToJSONError(f"Error accessing input file: {e}")


def determine_output_path(input_path: Path, custom_output: Optional[Union[str, Path]] = None) -> Path:
    """
    Determine the target JSON output path.
    
    If custom_output is provided, use it.
    Otherwise, default to 'output/<input_stem>.json' inside current working directory or relative to input.
    """
    if custom_output:
        out_p = Path(custom_output)
        # If output path given is a directory, append input filename with .json
        if out_p.is_dir():
            out_p = out_p / f"{input_path.stem}.json"
        return out_p
    else:
        # Default output directory: project-local output/ folder
        out_dir = Path("output")
        return out_dir / f"{input_path.stem}.json"


def convert_csv_to_json(
    input_path: Path,
    output_path: Optional[Path] = None,
    delimiter: str = ",",
    auto_type: bool = False,
    compact: bool = False,
    dry_run: bool = False,
    force: bool = False,
) -> Dict[str, Any]:
    """
    Execute CSV to JSON conversion safely.
    
    Returns:
        Summary dict containing conversion details.
    """
    parsed_delim = parse_delimiter(delimiter)
    headers, rows, row_count = parse_and_validate_csv(input_path, delimiter=parsed_delim, auto_type=auto_type)
    
    target_output = determine_output_path(input_path, output_path)
    
    # Overwrite protection check
    if target_output.exists() and not force:
        raise CSVToJSONError(f"Output file already exists: {target_output}\nUse --force to overwrite.")
        
    summary = {
        "input_path": str(input_path.resolve()),
        "output_path": str(target_output.resolve()),
        "rows": row_count,
        "columns": len(headers),
        "delimiter": repr(delimiter),
        "auto_type": auto_type,
        "format": "Compact" if compact else "Pretty",
        "dry_run": dry_run,
        "validation_passed": False
    }
    
    if dry_run:
        return summary

    # Ensure parent output directory exists
    target_output.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic creation via temporary file in target directory
    temp_fd, temp_path_str = tempfile.mkstemp(dir=target_output.parent, prefix=".tmp_conv_", suffix=".json")
    temp_path = Path(temp_path_str)
    
    try:
        with os.fdopen(temp_fd, mode="w", encoding="utf-8") as f:
            if compact:
                json.dump(rows, f, ensure_ascii=False, separators=(",", ":"))
            else:
                json.dump(rows, f, ensure_ascii=False, indent=4)
                
        # Validate generated JSON by attempting to parse it back
        with open(temp_path, mode="r", encoding="utf-8") as f:
            json.load(f)
            
        summary["validation_passed"] = True
        
        # Replace target output atomically
        temp_path.replace(target_output)
        
    except Exception as e:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise CSVToJSONError(f"Failed to create valid JSON output: {e}")
        
    return summary


def format_summary(summary: Dict[str, Any]) -> str:
    """Format the conversion summary for CLI output."""
    lines = [
        "=" * 40,
        "CSV TO JSON CONVERTER",
        "=" * 40,
        "",
        f"Input:\n  {summary['input_path']}",
        f"Output:\n  {summary['output_path']}",
        "",
        f"Rows: {summary['rows']}",
        f"Columns: {summary['columns']}",
        f"Delimiter: {summary['delimiter']}",
        f"Auto type: {'ON' if summary['auto_type'] else 'OFF'}",
        f"Format: {summary['format']}",
    ]
    
    if summary["dry_run"]:
        lines.extend([
            "",
            "DRY RUN: Validation passed. No JSON file was created.",
            "=" * 40,
        ])
    else:
        lines.extend([
            f"JSON validation: {'PASSED' if summary['validation_passed'] else 'FAILED'}",
            "",
            "Conversion completed successfully.",
            "=" * 40,
        ])
        
    return "\n".join(lines)


def run_interactive_mode():
    """Run interactive mode prompting the user for input parameters."""
    print("=" * 40)
    print("CSV to JSON Converter - Interactive Mode")
    print("=" * 40)
    
    try:
        input_str = input("Enter input CSV file: ").strip()
        if not input_str:
            print("ERROR: Input file path is required.")
            sys.exit(1)
            
        input_path = Path(input_str)
        
        output_str = input("Enter output JSON file (press Enter for automatic name): ").strip()
        output_path = Path(output_str) if output_str else None
        
        auto_type_str = input("Use automatic type conversion? [y/N]: ").strip().lower()
        auto_type = auto_type_str in ["y", "yes"]
        
        compact_str = input("Use compact JSON? [y/N]: ").strip().lower()
        compact = compact_str in ["y", "yes"]
        
        delim_str = input("Delimiter (press Enter for comma): ").strip()
        delimiter = delim_str if delim_str else ","
        
        summary = convert_csv_to_json(
            input_path=input_path,
            output_path=output_path,
            delimiter=delimiter,
            auto_type=auto_type,
            compact=compact,
            dry_run=False,
            force=False
        )
        print("\n" + format_summary(summary))
        
    except CSVToJSONError as e:
        print(f"\nERROR: {e}\nNo files were modified.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.\nNo input files were modified.")
        sys.exit(130)


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Convert CSV files to clean, structured JSON with validation and custom options."
    )
    parser.add_argument(
        "-i", "--input", type=str, help="Path to input CSV file"
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Path to output JSON file (default: output/<filename>.json)"
    )
    parser.add_argument(
        "-d", "--delimiter", type=str, default=",", help="CSV field delimiter (default: ',')"
    )
    parser.add_argument(
        "-a", "--auto-type", action="store_true", help="Automatically convert numbers, booleans, and nulls"
    )
    parser.add_argument(
        "-c", "--compact", action="store_true", help="Output compact JSON without indentation"
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Validate input and simulate conversion without creating files"
    )
    parser.add_argument(
        "-f", "--force", action="store_true", help="Allow replacing existing output JSON file"
    )
    return parser


def main():
    """Main entrypoint for CLI execution."""
    parser = build_parser()
    
    # If no arguments passed, launch interactive mode
    if len(sys.argv) == 1:
        run_interactive_mode()
        return

    args = parser.parse_args()
    
    if not args.input:
        print("ERROR: --input file parameter is required in CLI mode.")
        parser.print_help()
        sys.exit(1)
        
    try:
        summary = convert_csv_to_json(
            input_path=Path(args.input),
            output_path=Path(args.output) if args.output else None,
            delimiter=args.delimiter,
            auto_type=args.auto_type,
            compact=args.compact,
            dry_run=args.dry_run,
            force=args.force,
        )
        print(format_summary(summary))
        sys.exit(0)
        
    except CSVToJSONError as e:
        print(f"ERROR: {e}\nNo files were modified.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.\nNo input files were modified.")
        sys.exit(130)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
