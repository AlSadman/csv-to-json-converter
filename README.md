# CSV to JSON Converter

A lightweight, zero-dependency Python command-line utility for converting CSV files into clean, structured JSON with automatic type conversion, header validation, custom delimiter support, full UTF-8 Unicode preservation, dry-run simulation, atomic output creation, and overwrite protection.

---

## 🌟 Overview

The **CSV to JSON Converter** is designed for developers, data analysts, and CSE students who need a reliable, standard-library-only tool to convert tabular CSV data into JSON files safely. Built with Python 3.10+, it enforces strict data integrity rules while offering flexible CLI flags and interactive prompts.

---

## ✨ Key Features

- **Zero Third-Party Dependencies:** Powered strictly by Python's built-in standard library (`csv`, `json`, `pathlib`, `argparse`).
- **Automatic & Custom Output Paths:** Auto-generates `output/<filename>.json` or accepts custom file/directory output paths.
- **Pretty & Compact JSON:** Choice between formatted 4-space indented JSON or condensed single-line JSON (`--compact`).
- **Safe Automatic Type Conversion (`--auto-type`):** Recognizes integers, floats, booleans (`true`/`false`), and `null` values while conservatively preserving leading-zero numeric strings (e.g. ZIP codes like `"00123"`).
- **Strict Data Validation:** Validates headers (detects empty or duplicate keys), checks row length consistency, and verifies generated JSON validity.
- **UTF-8 & Unicode Support:** Native UTF-8 and UTF-8-BOM (`utf-8-sig`) handling for multilingual content (Bangla, Arabic, English, etc.) without unescaped ASCII sequences (`ensure_ascii=False`).
- **Custom Delimiters:** Supports comma `,`, semicolon `;`, tab `\t`, pipe `|`, or custom single-character delimiters (`--delimiter`).
- **Dry-Run Preview (`--dry-run`):** Inspect file metadata, headers, delimiter, and row counts without creating output files.
- **Data & File Safety:** Input files are strictly read-only. Existing JSON output files are protected against accidental overwrites unless `--force` is specified. Atomic file creation prevents corrupted output files on interruption.

---

## 📋 Requirements

- **Python 3.10+** (Tested on Python 3.14)
- **Standard Library Only** (No `pandas`, `numpy`, or `pip` packages required)

---

## 🚀 Installation & Setup

1. **Clone or Download the Repository:**
   ```powershell
   git clone https://github.com/turzo/csv-to-json-converter.git
   cd csv-to-json-converter
   ```

2. **Verify Python Installation:**
   ```powershell
   python --version
   ```

---

## 💡 Usage Guide

### 1. Interactive Mode
Run the script without arguments to launch the interactive prompt:
```powershell
python src/csv_to_json.py
```

### 2. Basic Conversion
Convert a CSV file to JSON using default settings (creates `output/employees.json`):
```powershell
python src/csv_to_json.py --input demo_data/employees.csv
```

### 3. Custom Output File
Specify an explicit destination path:
```powershell
python src/csv_to_json.py --input demo_data/products.csv --output output/my_products.json
```

### 4. Automatic Type Conversion
Convert numeric strings to numbers and boolean strings to booleans:
```powershell
python src/csv_to_json.py --input demo_data/products.csv --auto-type
```

### 5. Compact JSON Output
Produce minified JSON without line breaks or indentations:
```powershell
python src/csv_to_json.py --input demo_data/products.csv --compact
```

### 6. Custom Delimiters (Semicolon or Tab)
Convert semicolon-separated or tab-separated CSV files:
```powershell
python src/csv_to_json.py --input demo_data/products.csv --delimiter ";"
python src/csv_to_json.py --input demo_data/products.csv --delimiter "\t"
```

### 7. Dry-Run / Preview Mode
Validate the input CSV and view record metadata without writing any output:
```powershell
python src/csv_to_json.py --input demo_data/employees.csv --dry-run
```

### 8. Force Overwrite Existing Output
By default, the converter aborts if the output file already exists. Use `--force` to overwrite:
```powershell
python src/csv_to_json.py --input demo_data/employees.csv --force
```

---

## 📄 Example Input & Output

### Input CSV (`demo_data/products.csv`)
```csv
id,name,price,stock
1,Keyboard,25.50,10
2,Mouse,15.99,25
3,Monitor,199.99,5
```

### Default JSON Output (`--auto-type` disabled)
```json
[
    {
        "id": "1",
        "name": "Keyboard",
        "price": "25.50",
        "stock": "10"
    },
    {
        "id": "2",
        "name": "Mouse",
        "price": "15.99",
        "stock": "25"
    },
    {
        "id": "3",
        "name": "Monitor",
        "price": "199.99",
        "stock": "5"
    }
]
```

### Converted JSON Output (`--auto-type` enabled)
```json
[
    {
        "id": 1,
        "name": "Keyboard",
        "price": 25.5,
        "stock": 10
    },
    {
        "id": 2,
        "name": "Mouse",
        "price": 15.99,
        "stock": 25
    },
    {
        "id": 3,
        "name": "Monitor",
        "price": 199.99,
        "stock": 5
    }
]
```

---

## 🔒 Safety & Validation Rules

- **Input Preservation:** The input CSV file is opened in read-only mode and is never modified, renamed, or deleted.
- **Atomic Creation:** Output is written to a temporary file (`.tmp_conv_*.json`) inside the destination directory, verified for valid JSON syntax, and then atomically renamed to the final output file.
- **Overwrite Protection:** Returns a clear error if the destination file exists unless explicitly bypassed with `--force`.
- **Header Integrity:** Rejects CSV files containing duplicate header names or blank header names to prevent silent data loss.
- **Row Consistency:** Ensures all data rows match the expected column count established by the header row.

---

## 🧪 Automated Unit Testing

The project includes an extensive suite of 30 unit tests covering edge cases, formatting options, type conversions, CLI parsing, and safety guarantees.

Run the test suite using Python's built-in test runner:
```powershell
python -m unittest discover -s tests -v
```

---

## 📁 Project Structure

```text
C:\CSVToJSONConverter
│
├── src
│   └── csv_to_json.py         # Main CLI application module
│
├── tests
│   └── test_csv_to_json.py     # Automated unit tests suite (30 test cases)
│
├── demo_data
│   ├── README.md              # Documentation for sample datasets
│   ├── employees.csv          # Sample employee dataset
│   ├── products.csv           # Sample product dataset for type conversion
│   ├── unicode_data.csv       # Sample multilingual UTF-8 dataset
│   └── empty.csv              # Empty CSV file for edge case testing
│
├── output
│   └── README.md              # Output folder notice (.gitignore protected)
│
├── screenshots
│   └── README.md              # Visual assets placeholder
│
├── README.md                  # Main repository documentation
├── requirements.txt           # Dependency specification (Standard library only)
├── .gitignore                 # Git ignore rules for cache & generated JSON
└── LICENSE                    # MIT License
```

---

## ⚠️ Limitations

- **Schema Inference:** Flat CSV structures map directly to JSON arrays of objects. Complex nested JSON hierarchies (deeply nested objects/arrays) are not automatically inferred.
- **Memory Footprint:** The entire CSV dataset and generated JSON objects are loaded into memory during parsing. Extremely large files (multi-gigabyte) may require streaming optimizations.

---

## 🔮 Future Improvements

- Streaming JSON Lines (`NDJSON`) output support for massive datasets.
- Column filtering (`--include-cols` / `--exclude-cols`).
- Custom field mapping and schema transformation rules via JSON config.
- Batch directory conversion mode (`--input-dir`).

---

## 📜 License

Distributed under the **MIT License**. See [LICENSE](file:///C:/CSVToJSONConverter/LICENSE) for details.

Developed by **Turzo** (2026).
