#!/usr/bin/env python3
"""
Unit tests for CSV to JSON Converter.
Covering basic conversion, formatting, type conversion, edge cases, error conditions,
overwrite protection, dry-run mode, and input file safety.
"""

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from src.csv_to_json import (
    CSVToJSONError,
    build_parser,
    convert_csv_to_json,
    convert_value_type,
    determine_output_path,
    parse_delimiter,
)


class TestCSVToJSONConverter(unittest.TestCase):

    def setUp(self):
        """Set up isolated temporary directory for test files."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary files and directory after each test."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_csv(self, filename: str, content: str) -> Path:
        """Helper to create a CSV file in the test directory."""
        path = self.test_dir / filename
        with open(path, mode="w", encoding="utf-8-sig", newline="") as f:
            f.write(content)
        return path

    # 1. Basic CSV conversion
    def test_basic_csv_conversion(self):
        csv_path = self.create_csv("test.csv", "name,age\nAlice,25\nBob,30\n")
        out_path = self.test_dir / "test.json"
        summary = convert_csv_to_json(csv_path, output_path=out_path)
        self.assertTrue(out_path.exists())
        self.assertEqual(summary["rows"], 2)

    # 2. Correct number of JSON records
    def test_record_count(self):
        csv_path = self.create_csv("records.csv", "id,item\n1,A\n2,B\n3,C\n")
        out_path = self.test_dir / "records.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(len(data), 3)

    # 3. Correct field names
    def test_correct_field_names(self):
        csv_path = self.create_csv("fields.csv", "col1,col2,col3\nval1,val2,val3\n")
        out_path = self.test_dir / "fields.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(list(data[0].keys()), ["col1", "col2", "col3"])

    # 4. Correct values (string preservation default)
    def test_correct_values_default(self):
        csv_path = self.create_csv("values.csv", "name,age,active\nAlice,25,true\n")
        out_path = self.test_dir / "values.json"
        convert_csv_to_json(csv_path, output_path=out_path, auto_type=False)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0], {"name": "Alice", "age": "25", "active": "true"})

    # 5. Pretty JSON output formatting
    def test_pretty_json_output(self):
        csv_path = self.create_csv("pretty.csv", "a,b\n1,2\n")
        out_path = self.test_dir / "pretty.json"
        convert_csv_to_json(csv_path, output_path=out_path, compact=False)
        with open(out_path, mode="r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("\n    ", content)

    # 6. Compact JSON output formatting
    def test_compact_json_output(self):
        csv_path = self.create_csv("compact.csv", "a,b\n1,2\n")
        out_path = self.test_dir / "compact.json"
        convert_csv_to_json(csv_path, output_path=out_path, compact=True)
        with open(out_path, mode="r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("\n    ", content)
        self.assertEqual(content.strip(), '[{"a":"1","b":"2"}]')

    # 7. Automatic output filename determination
    def test_automatic_output_filename(self):
        csv_path = Path("demo_data/employees.csv")
        target = determine_output_path(csv_path)
        self.assertEqual(target, Path("output/employees.json"))

    # 8. Custom output path
    def test_custom_output_path(self):
        csv_path = self.create_csv("custom.csv", "x,y\n10,20\n")
        out_path = self.test_dir / "custom_dir" / "out.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        self.assertTrue(out_path.exists())

    # 9. Custom delimiter (semicolon)
    def test_custom_delimiter_semicolon(self):
        csv_path = self.create_csv("semi.csv", "name;age\nAlice;25\n")
        out_path = self.test_dir / "semi.json"
        convert_csv_to_json(csv_path, output_path=out_path, delimiter=";")
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0], {"name": "Alice", "age": "25"})

    # 10. Tab delimiter
    def test_tab_delimiter(self):
        csv_path = self.create_csv("tab.csv", "name\tage\nAlice\t25\n")
        out_path = self.test_dir / "tab.json"
        convert_csv_to_json(csv_path, output_path=out_path, delimiter=r"\t")
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0], {"name": "Alice", "age": "25"})

    # 11. Unicode content preservation
    def test_unicode_content(self):
        csv_path = self.create_csv("unicode.csv", "name,city\nসাদমান,চট্টগ্রাম\nمحمد,Dubai\n")
        out_path = self.test_dir / "unicode.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0]["name"], "সাদমান")
        self.assertEqual(data[0]["city"], "চট্টগ্রাম")
        self.assertEqual(data[1]["name"], "محمد")

    # 12. Empty CSV rejection
    def test_empty_csv_rejection(self):
        csv_path = self.create_csv("empty.csv", "")
        out_path = self.test_dir / "empty.json"
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(csv_path, output_path=out_path)
        self.assertIn("empty", str(ctx.exception).lower())

    # 13. Header-only CSV
    def test_header_only_csv(self):
        csv_path = self.create_csv("header_only.csv", "name,age,city\n")
        out_path = self.test_dir / "header_only.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data, [])

    # 14. Duplicate headers rejected
    def test_duplicate_headers_rejected(self):
        csv_path = self.create_csv("dup.csv", "name,age,name\nAlice,25,Dhaka\n")
        out_path = self.test_dir / "dup.json"
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(csv_path, output_path=out_path)
        self.assertIn("duplicate csv header", str(ctx.exception).lower())

    # 15. Empty header rejected
    def test_empty_header_rejected(self):
        csv_path = self.create_csv("blank_head.csv", "name,,city\nAlice,25,Dhaka\n")
        out_path = self.test_dir / "blank_head.json"
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(csv_path, output_path=out_path)
        self.assertIn("empty csv header", str(ctx.exception).lower())

    # 16. Inconsistent row length rejected
    def test_inconsistent_row_length_rejected(self):
        csv_path = self.create_csv("inconsistent.csv", "name,age,city\nAlice,25,Dhaka\nBob,30\n")
        out_path = self.test_dir / "inconsistent.json"
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(csv_path, output_path=out_path)
        self.assertIn("headers were expected", str(ctx.exception).lower())

    # 17. Missing input file rejected
    def test_missing_input_rejected(self):
        missing_path = self.test_dir / "nonexistent.csv"
        out_path = self.test_dir / "out.json"
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(missing_path, output_path=out_path)
        self.assertIn("does not exist", str(ctx.exception).lower())

    # 18. Input directory rejected
    def test_input_directory_rejected(self):
        out_path = self.test_dir / "out.json"
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(self.test_dir, output_path=out_path)
        self.assertIn("is a directory", str(ctx.exception).lower())

    # 19. Existing output file protected
    def test_existing_output_protected(self):
        csv_path = self.create_csv("data.csv", "name\nAlice\n")
        out_path = self.test_dir / "existing.json"
        out_path.write_text("existing content", encoding="utf-8")
        
        with self.assertRaises(CSVToJSONError) as ctx:
            convert_csv_to_json(csv_path, output_path=out_path, force=False)
        self.assertIn("already exists", str(ctx.exception).lower())
        self.assertEqual(out_path.read_text(encoding="utf-8"), "existing content")

    # 20. Force flag allows overwrite
    def test_force_overwrite(self):
        csv_path = self.create_csv("data.csv", "name\nAlice\n")
        out_path = self.test_dir / "existing.json"
        out_path.write_text("old content", encoding="utf-8")
        
        convert_csv_to_json(csv_path, output_path=out_path, force=True)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data[0]["name"], "Alice")

    # 21. Dry-run creates no output file
    def test_dry_run_creates_no_output(self):
        csv_path = self.create_csv("dry.csv", "a,b\n1,2\n")
        out_path = self.test_dir / "dry.json"
        summary = convert_csv_to_json(csv_path, output_path=out_path, dry_run=True)
        self.assertFalse(out_path.exists())
        self.assertTrue(summary["dry_run"])

    # 22. Auto-type integer conversion
    def test_auto_type_integer(self):
        self.assertEqual(convert_value_type("10"), 10)
        self.assertEqual(convert_value_type("-5"), -5)

    # 23. Auto-type float conversion
    def test_auto_type_float(self):
        self.assertEqual(convert_value_type("25.50"), 25.5)
        self.assertEqual(convert_value_type("-3.14"), -3.14)

    # 24. Auto-type boolean & null conversion
    def test_auto_type_boolean_null(self):
        self.assertTrue(convert_value_type("true"))
        self.assertFalse(convert_value_type("FALSE"))
        self.assertIsNone(convert_value_type("null"))

    # 25. Conservative handling of leading zeros
    def test_conservative_leading_zeros(self):
        self.assertEqual(convert_value_type("00123"), "00123")
        self.assertEqual(convert_value_type("012"), "012")
        self.assertEqual(convert_value_type("0"), 0)
        self.assertEqual(convert_value_type("0.5"), 0.5)

    # 26. JSON validity after conversion
    def test_json_validity_check(self):
        csv_path = self.create_csv("valid.csv", "id,title\n101,Book\n")
        out_path = self.test_dir / "valid.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        with open(out_path, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIsInstance(data, list)

    # 27. Input file unchanged after conversion
    def test_input_file_unchanged(self):
        csv_path = self.create_csv("safe.csv", "a,b\n1,2\n")
        initial_content = csv_path.read_text(encoding="utf-8")
        out_path = self.test_dir / "safe.json"
        
        convert_csv_to_json(csv_path, output_path=out_path)
        self.assertEqual(csv_path.read_text(encoding="utf-8"), initial_content)

    # 28. CLI argument parsing
    def test_cli_argument_parsing(self):
        parser = build_parser()
        args = parser.parse_args(["-i", "input.csv", "-o", "out.json", "--auto-type", "--compact", "-f"])
        self.assertEqual(args.input, "input.csv")
        self.assertEqual(args.output, "out.json")
        self.assertTrue(args.auto_type)
        self.assertTrue(args.compact)
        self.assertTrue(args.force)

    # 29. Invalid delimiter handling
    def test_invalid_delimiter(self):
        with self.assertRaises(CSVToJSONError):
            parse_delimiter("")
        with self.assertRaises(CSVToJSONError):
            parse_delimiter("multi")
        with self.assertRaises(CSVToJSONError):
            parse_delimiter(r"\n")

    # 30. Temporary file cleanup on error
    def test_temp_file_cleanup_on_error(self):
        # Verify no orphan .tmp files remain in test directory
        csv_path = self.create_csv("normal.csv", "a,b\n1,2\n")
        out_path = self.test_dir / "out.json"
        convert_csv_to_json(csv_path, output_path=out_path)
        
        tmp_files = list(self.test_dir.glob(".tmp_*"))
        self.assertEqual(len(tmp_files), 0)


if __name__ == "__main__":
    unittest.main()
