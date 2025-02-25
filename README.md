# File Contents Printer Script

This Python script recursively processes files from a specified directory, filters them based on allowed file extensions, and outputs their contents with headers showing their relative paths. It supports ignoring specific files or directories using patterns similar to a .gitignore file and can generate a table of contents (TOC) for easy navigation.

## Features

- Recursively traverses a directory and its subdirectories.
- Filters files based on allowed extensions (e.g., .tf, .tfvars, .py, .sh, .txt).
- Outputs each file's relative path and contents wrapped in triple backticks () for easy reading. 
- Supports an optional ignore file (`.scriptignore` by default) to exclude files or directories using patterns. 
- Can write output to a file or print to the console. 
- Optionally generates a table of contents listing all included files.  
  
## Requirements  
- **Python 3.x** 
- **pathspec** library (for ignore file support): Install with `pip install pathspec`  
  - If `pathspec` is not installed, the script will still run but will skip ignore patterns and print a warning.  
  
## Usage  Run the script from the command line using:  
```bash
python3 print_files.py [directory] [options]
```
 - **`[directory]`**: The starting directory to process (default: current directory `.`).  
  
### Command-Line Options  

| Option                 | Description                                                                                  |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| `-o, --output <file>`  | Specify an output file to write the results to (default: print to console)                   |
| `-t, --toc`            | Generate a table of contents at the beginning of the output.                                 |
| `--ignore-file <file>` | Specify a custom path to an ignore file (default: `.scriptignore` in the script's directory) |
-------------

### Examples  
- **Basic usage** (process current directory, print to console):   
```bash
python3 print_files.py
```
**Specify a directory**:   
```bash
python3 print_files.py /path/to/repo
```
**Write output to a file**:   
```bash
python3 print_files.py -o output.txt
```
**Generate a table of contents**:   
```bash
python3 print_files.py -t
```
**Use a custom ignore file**:   
```bash
python3 print_files.py --ignore-file custom.ignore
```
**Combine options** (e.g., specify directory, output file, and TOC):   
```bash
python3 print_files.py /path/to/repo -o repo_contents.txt -t
```

## Ignore File  

The script supports an optional ignore file to exclude specific files or directories: 

- **Default location**: `.scriptignore` in the same directory as the script. 
- **Custom location**: Specify with `--ignore-file <file>`.  The ignore file uses the same syntax as `.gitignore`: 
  - Patterns like `*.pyc` to ignore all `.pyc` files. 
  - Directory patterns like `dir/` to ignore entire directories. 
  - Negation with `!` to include specific files (e.g., `!important.tf`).  If the ignore file is present but cannot be parsed, the script will print an error and proceed without ignoring.  
  
## Allowed File Extensions  

The script only processes files with extensions listed in `ALLOWED_EXTENSIONS` (defined in the script): 
  - Default extensions: `.tf`, `.tfvars`, `.py`, `.sh`, `.txt` 
  - To modify, edit the `ALLOWED_EXTENSIONS` list in the script.  

## Output Format  

The output consists of: - **Optional Table of Contents** (if `-t` is used): 
``` 
  Table of Contents
  - /relative/path/to/file1.tf
  - /relative/path/to/file2.py
  - **File Contents**:  
  /relative/path/to/file1.tf
    
  # Contents of file1.tf  
  /relative/path/to/file2.py

  # Contents of file2.py

```

## Error Handling


- If a file cannot be read (e.g., due to permissions), an error message is included:`Error reading file: [error details]`

- Ignore File Errors: If the ignore file exists but fails to parse, a warning is printed, and the script proceeds without ignoring.
- File Reading Errors: If a file cannot be read, an error message is included in the output instead of the file's contents.
