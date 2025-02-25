#!/usr/bin/env python3
import os
from pathlib import Path
import argparse

try:
    import pathspec
except ImportError:
    pathspec = None

# Define allowed file extensions (modify as needed)
ALLOWED_EXTENSIONS = ['.tf', '.tfvars', '.py', '.sh', '.txt']

def print_file_contents(starting_dir='.', output_file=None, toc=False, ignore_spec=None):
    """
    Recursively process files with allowed extensions from starting_dir, excluding those matching ignore_spec,
    and either print their contents or write to an output file. Optionally generate a table of contents.

    Args:
        starting_dir (str): Directory to start processing from (default: current directory).
        output_file (str): Path to output file (if None, prints to console).
        toc (bool): If True, generates a table of contents.
        ignore_spec (pathspec.PathSpec): Patterns to exclude files/directories (optional).
    """
    base_path = Path(starting_dir).resolve()
    output = open(output_file, 'w', encoding='utf-8') if output_file else None
    files_to_include = []

    try:
        for root, dirs, files in os.walk(starting_dir):
            # Check if the current directory should be ignored
            relative_root = os.path.relpath(root, base_path).replace(os.sep, '/')
            if ignore_spec and ignore_spec.match_file(relative_root + '/'):
                dirs[:] = []  # Skip this directory and its subdirectories
                continue
            for file in files:
                # Skip files not matching allowed extensions
                if os.path.splitext(file)[1].lower() not in ALLOWED_EXTENSIONS:
                    continue
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, base_path).replace(os.sep, '/')
                # Skip files matching ignore patterns
                if ignore_spec and ignore_spec.match_file(relative_path):
                    continue
                files_to_include.append(relative_path)
        
        # Sort files for consistent output
        sorted_files = sorted(files_to_include)
        
        # Generate table of contents if requested
        if toc:
            toc_header = "\n**Table of Contents**\n"
            toc_content = "\n".join([f"- /{path}" for path in sorted_files])
            toc_str = toc_header + toc_content + "\n"
            if output:
                output.write(toc_str)
            else:
                print(toc_str)
        
        # Output each file's contents
        for relative_path in sorted_files:
            full_path = base_path / relative_path
            header = f"\n/{relative_path}\n```\n"
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    contents = f.read()
                output_str = header + contents.rstrip() + "\n```\n"
            except Exception as e:
                output_str = header + f"# Error reading file: {str(e)}\n```\n"
            if output:
                output.write(output_str)
            else:
                print(output_str)
    finally:
        if output:
            output.close()

if __name__ == "__main__":
    # Set up command-line arguments
    parser = argparse.ArgumentParser(
        description="Print contents of files with allowed extensions, excluding ignored patterns."
    )
    parser.add_argument(
        'directory',
        nargs='?',
        default='.',
        help="Starting directory (default: current directory)"
    )
    parser.add_argument(
        '-o',
        '--output',
        help="Output file path (default: print to console)"
    )
    parser.add_argument(
        '-t',
        '--toc',
        action='store_true',
        help="Generate a table of contents"
    )
    parser.add_argument(
        '--ignore-file',
        help="Path to ignore file (default: .scriptignore in script's directory)"
    )
    
    args = parser.parse_args()
    
    # Determine ignore file location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_ignore_file = os.path.join(script_dir, '.scriptignore')
    ignore_file = args.ignore_file or default_ignore_file
    
    # Load ignore patterns if file exists
    if ignore_file and os.path.exists(ignore_file):
        if pathspec is None:
            print("Warning: 'pathspec' module not installed. Ignoring patterns skipped.")
            ignore_spec = None
        else:
            try:
                with open(ignore_file, 'r', encoding='utf-8') as f:
                    ignore_patterns = f.read().splitlines()
                ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
            except Exception as e:
                print(f"Error parsing ignore file '{ignore_file}': {str(e)}. Proceeding without ignoring.")
                ignore_spec = None
    else:
        if args.ignore_file:
            print(f"Warning: Ignore file '{args.ignore_file}' not found. Proceeding without ignoring.")
        ignore_spec = None
    
    # Run the main function
    print_file_contents(args.directory, args.output, args.toc, ignore_spec)