#!/usr/bin/env python3
import os
from pathlib import Path
import argparse
from collections import defaultdict
import re
import json

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
    '.service', '.toml', '.proto', '.cs', '.ts', '.js', '.dockerfile'
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
    '.md': 'text',
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
    '.editorconfig': 'editorconfig',
    '.dockerfile': 'dockerfile'
}

# Entry point patterns - these help AI understand program flow
ENTRY_POINT_PATTERNS = {
    'main_files': [
        'main.py', 'app.py', 'server.py', 'run.py', '__main__.py',
        'index.js', 'app.js', 'server.js', 'main.js',
        'Main.java', 'Application.java', 'App.java',
        'main.go', 'cmd/main.go',
        'Program.cs', 'Main.cs',
        'main.kt', 'Application.kt'
    ],
    'config_files': [
        'docker-compose.yml', 'docker-compose.yaml', 'dockerfile', 'Dockerfile',
        'package.json', 'pom.xml', 'build.gradle', 'requirements.txt',
        'pyproject.toml', 'setup.py', 'go.mod', 'cargo.toml',
        '.env.example', 'config.yaml', 'config.yml', 'settings.py'
    ],
    'startup_scripts': [
        'start.sh', 'run.sh', 'startup.sh', 'deploy.sh',
        'manage.py', 'gradlew', 'mvnw'
    ]
}

def detect_entry_points(files):
    """
    Detect and categorize entry points to help AI understand program architecture.
    Returns a dict with categorized entry points and their roles.
    """
    entry_points = {
        'main_entry': [],
        'config_entry': [],
        'startup_scripts': [],
        'api_routes': [],
        'other_important': []
    }
    
    for file_path in files:
        filename = os.path.basename(file_path).lower()
        
        # Direct filename matches
        if filename in [f.lower() for f in ENTRY_POINT_PATTERNS['main_files']]:
            entry_points['main_entry'].append(file_path)
        elif filename in [f.lower() for f in ENTRY_POINT_PATTERNS['config_files']]:
            entry_points['config_entry'].append(file_path)
        elif filename in [f.lower() for f in ENTRY_POINT_PATTERNS['startup_scripts']]:
            entry_points['startup_scripts'].append(file_path)
        
        # Pattern-based detection for routes/controllers
        elif any(pattern in file_path.lower() for pattern in ['route', 'controller', 'handler', 'endpoint']):
            entry_points['api_routes'].append(file_path)
        
        # Other important patterns
        elif any(pattern in filename for pattern in ['makefile', 'jenkinsfile', 'dockerfile']):
            entry_points['other_important'].append(file_path)
    
    return entry_points

def analyze_file_content_for_entry_patterns(file_path, content):
    """
    Analyze file content to detect if it contains entry point patterns.
    This helps AI understand what each file does.
    """
    patterns = []
    lower_content = content.lower()
    
    # Python patterns
    if file_path.endswith('.py'):
        if 'if __name__ == "__main__"' in content:
            patterns.append('Python main entry')
        if any(pattern in lower_content for pattern in ['flask', 'django', 'fastapi']):
            patterns.append('Web framework entry')
        if 'uvicorn.run' in content or 'app.run' in content:
            patterns.append('Server startup')
    
    # JavaScript/Node patterns
    elif file_path.endswith(('.js', '.ts')):
        if 'express()' in content or 'createserver' in lower_content:
            patterns.append('Web server entry')
        if 'process.argv' in content:
            patterns.append('CLI entry')
    
    # Java patterns
    elif file_path.endswith('.java'):
        if 'public static void main' in content:
            patterns.append('Java main method')
        if '@springbootapplication' in lower_content:
            patterns.append('Spring Boot entry')
    
    # Go patterns
    elif file_path.endswith('.go'):
        if 'func main()' in content:
            patterns.append('Go main function')
    
    # Docker patterns
    elif 'dockerfile' in file_path.lower():
        if 'entrypoint' in lower_content or 'cmd' in lower_content:
            patterns.append('Docker entry')
    
    return patterns

def prioritize_files(files, base_path):
    """
    Prioritize files for AI consumption - most important context first.
    """
    entry_points = detect_entry_points(files)
    
    # Priority order for AI understanding:
    prioritized = []
    
    # 1. Main entry points first - these show program flow
    prioritized.extend(entry_points['main_entry'])
    
    # 2. Configuration files - these show how the system is set up
    prioritized.extend(entry_points['config_entry'])
    
    # 3. Startup scripts - these show deployment/running procedures  
    prioritized.extend(entry_points['startup_scripts'])
    
    # 4. API routes/controllers - these show system interfaces
    prioritized.extend(entry_points['api_routes'])
    
    # 5. Other important files
    prioritized.extend(entry_points['other_important'])
    
    # 6. Remaining files, sorted alphabetically
    remaining = [f for f in files if f not in prioritized]
    prioritized.extend(sorted(remaining))
    
    return prioritized, entry_points

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
    or ignore_extensions, and either print their contents or write to an output file. Prioritizes files
    for better AI understanding.

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
        
        # Prioritize files for AI consumption
        prioritized_files, entry_points = prioritize_files(files_to_include, base_path)

        # Write top-level heading and initial message
        message = "# Codebase Summary\n\nThe following is a complete codebase summary optimized for AI analysis. Files are prioritized by importance - entry points and configuration first, followed by core application logic. This ordering helps establish program flow and architecture context upfront.\n\n"
        if output:
            output.write(message)
        else:
            print(message)

        # Compute project overview with entry point analysis
        lang_counts = {}
        total_lines = 0
        for rel_path in files_to_include:
            ext = os.path.splitext(rel_path)[1].lower()
            lang = EXT_TO_LANG.get(ext, 'unknown')
            lang_counts[lang] = lang_counts.get(lang, 0) + 1
            try:
                with open(base_path / rel_path, 'r', encoding='utf-8') as f:
                    total_lines += sum(1 for _ in f)
            except:
                pass
        
        # Enhanced project overview with entry point information
        dep_files = [f for f in files_to_include if os.path.basename(f) in ('package.json', 'pom.xml', 'requirements.txt', 'build.gradle', 'pyproject.toml', 'go.mod')]
        dep_summary = f"- Dependency files: {', '.join(dep_files)}\n" if dep_files else "- Dependency files: None detected\n"
        
        # Entry points summary for AI context
        entry_summary = "## Entry Points & Architecture\n\n"
        if entry_points['main_entry']:
            entry_summary += f"**Main Entry Points**: {', '.join(entry_points['main_entry'])}\n"
        if entry_points['config_entry']:
            entry_summary += f"**Configuration**: {', '.join(entry_points['config_entry'])}\n"
        if entry_points['startup_scripts']:
            entry_summary += f"**Startup Scripts**: {', '.join(entry_points['startup_scripts'])}\n"
        if entry_points['api_routes']:
            entry_summary += f"**API/Routes**: {', '.join(entry_points['api_routes'])}\n"
        entry_summary += "\n"
        
        overview = f"## Project Overview\n\n- Total files: {len(files_to_include)}\n- Languages used: {', '.join(sorted(lang_counts.keys()))}\n- Approximate total lines: {total_lines}\n{dep_summary}\n{entry_summary}"
        
        if output:
            output.write(overview)
        else:
            print(overview)

        # Generate table of contents if requested
        if toc:
            toc_header = "## Table of Contents (Prioritized Order)\n\n"
            toc_content = build_tree(prioritized_files)
            toc_str = toc_header + toc_content + "\n\n"
            if output:
                output.write(toc_str)
            else:
                print(toc_str)
        
        # Add code files subheading
        code_files_header = "## Code Files (Priority Order)\n\n*Files are ordered by importance for AI analysis: entry points → configuration → core logic → supporting files*\n\n"
        if output:
            output.write(code_files_header)
        else:
            print(code_files_header)
        
        # Output each file's contents in prioritized order
        for relative_path in prioritized_files:
            full_path = base_path / relative_path
            ext = os.path.splitext(relative_path)[1].lower()
            lang = EXT_TO_LANG.get(ext, '')
            
            # Determine file role for AI context
            role_indicators = []
            if relative_path in entry_points['main_entry']:
                role_indicators.append("**MAIN ENTRY POINT**")
            elif relative_path in entry_points['config_entry']:
                role_indicators.append("**CONFIGURATION**")
            elif relative_path in entry_points['startup_scripts']:
                role_indicators.append("**STARTUP SCRIPT**")
            elif relative_path in entry_points['api_routes']:
                role_indicators.append("**API/ROUTES**")
            elif relative_path in entry_points['other_important']:
                role_indicators.append("**BUILD/DEPLOY**")
            
            header = f"\n### {relative_path}\n\n"
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    contents = f.read()
                line_count = len(contents.splitlines())
                file_size = os.path.getsize(full_path)
                
                # Analyze content for entry patterns
                entry_patterns = analyze_file_content_for_entry_patterns(relative_path, contents)
                
                # Enhanced metadata with role and patterns
                metadata_parts = [f"{line_count} lines, {file_size} bytes"]
                if role_indicators:
                    metadata_parts.append(role_indicators[0])
                if entry_patterns:
                    metadata_parts.append(f"Contains: {', '.join(entry_patterns)}")
                
                metadata = f"**Metadata**: {' | '.join(metadata_parts)}\n\n"
                
                if ext in ('.md', '.markdown'):
                    is_valid, error = check_markdown(full_path)
                    if not is_valid:
                        output_str = header + metadata + f"# Warning: Malformed markdown - {error}\n\n```{lang}\n```\n\n"
                    else:
                        output_str = header + metadata + f"```{lang}\n{contents.rstrip()}\n```\n\n"
                else:
                    output_str = header + metadata + f"```{lang}\n{contents.rstrip()}\n```\n\n"
            except Exception as e:
                output_str = header + f"**Metadata**: Error reading file\n\n# Error reading file: {str(e)}\n\n```{lang}\n```\n\n"
            
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
        description="Create AI-optimized codebase summaries with intelligent file prioritization."
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