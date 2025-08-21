# Codebase Summary Generator

This Python script creates comprehensive codebase summaries by intelligently analyzing and prioritizing files for better understanding of project structure and architecture. It generates detailed summaries with dependency analysis, file prioritization, and smart filtering.

## Features

- **Intelligent File Prioritization** - Entry points and configuration files first, followed by core logic
- **Comprehensive Dependency Analysis** - Automatically detects frameworks, languages, and project types
- **Smart Auto-Filtering** - Built-in patterns to exclude build artifacts, dependencies, and IDE files
- **Optimized Output** - Files ordered and annotated for better code understanding
- **Tech Stack Detection** - Identifies frameworks like Spring Boot, React, Django, etc.
- **Configuration Analysis** - Recognizes and categorizes config files with descriptions
- **Multiple Language Support** - Java, Python, JavaScript/TypeScript, Go, Rust, C#, and more
- **Gitignore Integration** - Respects .gitignore patterns automatically
- **Large File Handling** - Smart truncation with continuation prompts for very large files

## Requirements

Create a virtual environment and install dependencies:

```bash
# Setup (run once)
./setup.sh

# Activate environment
source myenv/bin/activate
```

### Dependencies (requirements.txt)
```txt
# Core functionality
pathspec>=0.10.0

# Enhanced dependency analysis (optional)
tomli>=2.0.0; python_version < "3.11"
pyyaml>=6.0
```

## Usage

```bash
python summarize.py [directory] [options]
```

### Command-Line Options

| Option                       | Description                                              |
| ---------------------------- | -------------------------------------------------------- |
| `-o, --output <file>`        | Output file path (default: print to console)             |
| `-t, --toc`                  | Generate hierarchical table of contents                  |
| `--ignore-file <file>`       | Custom ignore file path                                  |
| `--ignore-ext <ext> [<ext>]` | Additional file extensions to ignore (e.g., `.log .tmp`) |

### Examples

**Basic usage** - Generate summary of current directory:
```bash
python summarize.py . -o summary.txt -t
```

**Focus on source code only** (run from src/ directory):
```bash
cd src/main/java
python ~/path/to/summarize.py . -o ../../../summary.txt -t
```

**Exclude additional file types**:
```bash
python summarize.py . --ignore-ext .log .properties -o summary.txt
```

## Output Format

The generated summary includes:

### 1. Project Overview
- File count and languages detected
- Entry points and architecture overview  
- Dependency analysis and tech stack

### 2. Prioritized File Contents
Files are intelligently ordered:
1. **Entry Points** - main files, application entry points
2. **Configuration** - build files, framework config, environment settings
3. **Core Logic** - business logic, services, controllers
4. **Supporting Files** - utilities, helpers, remaining code

### 3. Rich Metadata
Each file includes:
- File size and line count
- Role indicators (MAIN ENTRY POINT, CONFIGURATION, API/ROUTES)
- Truncation notices for large files
- Configuration descriptions where applicable

## Supported File Types

**Programming Languages:**
`.java`, `.py`, `.js`, `.ts`, `.go`, `.rs`, `.cs`, `.kt`, `.swift`, `.rb`, `.php`

**Configuration:**
`.json`, `.yaml`, `.yml`, `.toml`, `.xml`, `.properties`, `.ini`, `.conf`

**Infrastructure:**
`.tf`, `.dockerfile`, `.sh`, `.sql`, `.md`

**Web:**
`.html`, `.css`, `.scss`, `.vue`, `.svelte`, `.jsx`, `.tsx`

## Auto-Ignore Patterns

The script automatically excludes common noise:

- **Build artifacts:** `build/`, `dist/`, `target/`, `.gradle/`
- **Dependencies:** `node_modules/`, `vendor/`, `__pycache__/`
- **IDE files:** `.idea/`, `.vscode/`, `.DS_Store`
- **Lock files:** `package-lock.json`, `yarn.lock`, `Cargo.lock`
- **Test coverage:** `coverage/`, `.nyc_output/`

## Bash Helper Script

Global installation for easy access:

```bash
#!/bin/bash
# Save as /usr/local/bin/summarize

SCRIPT_DIR="$HOME/git/personal/summarize-folder-contents"
VENV_DIR="$SCRIPT_DIR/myenv"

DIR="$1"
OUT="${2:-summary.md}"

"$VENV_DIR/bin/python" "$SCRIPT_DIR/summarize.py" "$DIR" -o "$OUT" -t
```

```bash
chmod +x /usr/local/bin/summarize
```

# Usage

```bash
summarize .                    # Current directory → summary.md  
summarize /path/to/project     # Specific directory → summary.md
summarize . my-analysis.txt    # Custom output file
```

## Dependency Analysis

The script automatically detects:

**Project Types:** Backend API, Frontend, Mobile App, Infrastructure, Machine Learning

**Frameworks:** Spring Boot, React, Vue.js, Django, Flask, Express.js, Angular, Next.js

**Languages:** Java, Python, JavaScript, TypeScript, Go, Rust, C#, Kotlin, Swift

**Build Tools:** Maven, Gradle, npm, yarn, pip, cargo, nuget

## Best Practices

### For Code Analysis
- Run from project root to get dependency analysis
- Use `-t` flag for navigation
- Focus on source directories to avoid test noise

### For Code Reviews  
- Run from specific module/package directories
- Include configuration files for deployment context
- Use custom ignore patterns for sensitive files

### For Documentation
- Generate from project root with full context
- Include README and documentation files
- Use descriptive output filenames

## Python Version

This project uses Python 3.11+ (specified in `.python-version`). The virtual environment ensures consistent dependency versions across different systems.