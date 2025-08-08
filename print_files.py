#!/usr/bin/env python3
import os
from pathlib import Path
import argparse
from collections import defaultdict

try:
    import pathspec
except ImportError:
    pathspec = None

# Define allowed file extensions (modify as needed)
ALLOWED_EXTENSIONS = [
    '.tf', '.tfvars', '.py', '.sh', '.java', '.yaml', '.yml', '.json',
    '.md', '.txt', '.kt', '.groovy', '.kts', '.gradle', '.properties',
    '.xml', '.sql', '.csv', '.ini', '.sh', '.conf', '.cfg', '.log', '.gitignore',
    '.dockerignore', '.editorconfig', '.yml.example', '.yaml.example', '.go',
    '.service', '.toml', '.proto', '.cs', '.ts', '.js'
]

# Map extensions to syntax highlighting languages
EXT_TO_LANG = {
    '.py': 'python',
    '.java': 'java',
    '.cs': 'csharp',
    '.ts': 'typescript',
    '.js': 'javascript',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.json': 'json',
    '.md': 'text',  # Use 'text' to avoid markdown rendering
    '.txt': 'text',
    '.sh': 'bash',
    '.sql': 'sql',
    '.csv': 'csv',
    '.xml': 'xml',
    '.toml': 'toml',
    '.proto': 'protobuf',
    '.go': 'go',
    '.kt': 'kotlin',
    '.groovy': 'groovy',
    '.gradle': 'gradle',
    '.properties': 'properties',
    '.ini': 'ini',
    '.conf': 'ini',
    '.cfg': 'ini',
    '.log': 'log',
    '.gitignore': 'gitignore',
    '.dockerignore': 'dockerignore',
    '.editorconfig': 'editorconfig'
}

def check_markdown(file_path):
    """
    Check if a markdown file has balanced triple backticks.
    Returns (is_valid, error_message).
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        if content.count('```') % 2 != 0:
            return False, "Unclosed triple backticks detected"
        return True, None
    except Exception as e:
        return False, str(e)

def build_tree(files):
    """
    Build a hierarchical tree representation of file paths for TOC.
    """
    tree = defaultdict(dict)
    for path in files:
        parts = path.split('/')
        current = tree
        for part in parts[:-1]:
            current = current.setdefault(part, defaultdict(dict))
        current.setdefault('__files__', []).append(parts[-1])
    
    def print_tree(node, prefix=''):
        lines = []
        dirs = sorted(k for k in node if k != '__files__')
        files = sorted(node.get('__files__', []))
        items = dirs + files
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            line_prefix = prefix + ('└── ' if is_last else '├── ')
            lines.append(line_prefix + item)
            if item in dirs:
                new_prefix = prefix + ('    ' if is_last else '│   ')
                lines.extend(print_tree(node[item], new_prefix))
        return lines
    
    return '\n'.join(print_tree(tree))

def print_file_contents(starting_dir='.', output_file=None, toc=False, ignore_spec=None, ignore_extensions=None):
    """
    Recursively process files with allowed extensions from starting_dir, excluding those matching ignore_spec
    or ignore_extensions, and either print their contents or write to an output file. Optionally generate
    a table of contents and project overview.

    Args:
        starting_dir (str): Directory to start processing from (default: current directory).
        output_file (str): Path to output file (if None, prints to console).
        toc (bool): If True, generates a table of contents.
        ignore_spec (pathspec.PathSpec): Patterns to exclude files/directories (optional).
        ignore_extensions (set): File extensions to exclude (optional).
    """
    base_path = Path(starting_dir).resolve()
    output = open(output_file, 'w', encoding='utf-8') if output_file else None
    files_to_include = []
    ignore_extensions = set(ignore_extensions or [])

    try:
        for root, dirs, files in os.walk(starting_dir):
            relative_root = os.path.relpath(root, base_path).replace(os.sep, '/')
            if ignore_spec and ignore_spec.match_file(relative_root + '/'):
                dirs[:] = []  # Skip this directory and its subdirectories
                continue
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext not in ALLOWED_EXTENSIONS or ext in ignore_extensions:
                    continue
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, base_path).replace(os.sep, '/')
                if ignore_spec and ignore_spec.match_file(relative_path):
                    continue
                if output_file and Path(full_path).resolve() == Path(output_file).resolve():
                    continue
                files_to_include.append(relative_path)
        
        # Sort files for consistent output
        sorted_files = sorted(files_to_include)

        # Write top-level heading and initial message
        message = "# Codebase Summary\n\nThe following is a list of all code files in the root directory. It begins with a project overview and a table of contents showing the directory structure. The code in this file should be loaded into your context and treated as if I provided the actual source files.\n\n"
        if output:
            output.write(message)
        else:
            print(message)

        # Compute project overview
        lang_counts = {}
        total_lines = 0
        for rel_path in sorted_files:
            ext = os.path.splitext(rel_path)[1].lower()
            lang = EXT_TO_LANG.get(ext, 'unknown')
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            try:
                with open(base_path / rel_path, 'r', encoding='utf-8') as f:
                    total_lines += sum(1 for _ in f)
            except:
                pass
        
        # In print_file_contents, after computing lang_counts:
        dep_files = [f for f in sorted_files if f in ('package.json', 'pom.xml', 'requirements.txt', 'build.gradle')]
        dep_summary = f"- Dependency files: {', '.join(dep_files) if dep_files else 'None'}\n" if dep_files else ""
        overview = f"## Project Overview\n\n- Total files: {len(sorted_files)}\n- Languages used: {', '.join(sorted(lang_counts.keys()))}\n- Approximate total lines: {total_lines}\n{dep_summary}\n"

        overview = f"## Project Overview\n\n- Total files: {len(sorted_files)}\n- Languages used: {', '.join(sorted(lang_counts.keys()))}\n- Approximate total lines: {total_lines}\n\n"
        if output:
            output.write(overview)
        else:
            print(overview)

        # Generate table of contents if requested
        if toc:
            toc_header = "## Table of Contents\n\n"
            toc_content = build_tree(sorted_files)
            toc_str = toc_header + toc_content + "\n\n"
            if output:
                output.write(toc_str)
            else:
                print(toc_str)
        
        # Add code files subheading
        code_files_header = "## Code Files\n"
        if output:
            output.write(code_files_header)
        else:
            print(code_files_header)
        
        # Output each file's contents
        for relative_path in sorted_files:
            full_path = base_path / relative_path
            ext = os.path.splitext(relative_path)[1].lower()
            lang = EXT_TO_LANG.get(ext, '')
            header = f"\n### {relative_path}\n\n"
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    contents = f.read()
                line_count = len(contents.splitlines())
                file_size = os.path.getsize(full_path)
                metadata = f"**Metadata**: {line_count} lines, {file_size} bytes\n\n"
                if ext in ('.md', '.markdown'):
                    is_valid, error = check_markdown(full_path)
                    if not is_valid:
                        output_str = header + metadata + f"# Warning: Malformed markdown - {error}\n\n```{lang}\n```\n\n"
                    else:
                        output_str = header + metadata + f"```{lang}\n{contents.rstrip()}\n```\n\n"
                else:
                    output_str = header + metadata + f"```{lang}\n{contents.rstrip()}\n```\n\n"
            except Exception as e:
                output_str = header + f"**Metadata**: Error\n\n# Error reading file: {str(e)}\n\n```{lang}\n```\n\n"
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
        description="Print contents of files with allowed extensions, excluding ignored patterns or extensions."
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
        help="Path to ignore file (default: 'ignore' in script directory)"
    )
    parser.add_argument(
        '--ignore-ext',
        nargs='+',
        help="File extensions to ignore (e.g., .log .txt)"
    )

    args = parser.parse_args()

    # Handle ignore file logic
    ignore_spec = None
    if args.ignore_file:
        ignore_file = args.ignore_file
        if not os.path.isabs(ignore_file):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            ignore_file = os.path.join(script_dir, ignore_file)
        if os.path.exists(ignore_file):
            if pathspec is None:
                print("Warning: 'pathspec' module not installed. Ignoring patterns skipped.")
            else:
                try:
                    with open(ignore_file, 'r', encoding='utf-8') as f:
                        ignore_patterns = f.read().splitlines()
                    ignore_spec = pathspec.PathSpec.from_lines('gitwildmatch', ignore_patterns)
                except Exception as e:
                    print(f"Error parsing ignore file: {str(e)}. Proceeding without ignoring.")
        else:
            print(f"Warning: Ignore file '{ignore_file}' not found. Proceeding without ignoring.")
    
    # Normalize output file path
    if args.output and not os.path.isabs(args.output):
        output_path = os.path.join(os.getcwd(), args.output)
    else:
        output_path = args.output

    # Normalize ignore extensions
    ignore_extensions = {ext.lower() for ext in args.ignore_ext or []}
    if ignore_extensions:
        ignore_extensions = {ext if ext.startswith('.') else f'.{ext}' for ext in ignore_extensions}

    # Run the main function
    print_file_contents(args.directory, output_path, args.toc, ignore_spec, ignore_extensions)