#!/usr/bin/env python3
import os
from pathlib import Path
import argparse
from collections import defaultdict
import re
import json
import xml.etree.ElementTree as ET

try:
    import pathspec
except ImportError:
    pathspec = None

# allowed file extensions
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

# Entry point patterns
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

# Configuration and framework detection files
CONFIG_FILE_PATTERNS = {
    # Build/Package Management
    'package.json': 'npm/Node.js configuration',
    'pom.xml': 'Maven configuration', 
    'build.gradle': 'Gradle build configuration',
    'build.gradle.kts': 'Gradle Kotlin build configuration',
    'cargo.toml': 'Rust package configuration',
    'go.mod': 'Go module configuration',
    'pyproject.toml': 'Python project configuration',
    'requirements.txt': 'Python dependencies',
    'gemfile': 'Ruby dependencies',
    'pubspec.yaml': 'Flutter/Dart configuration',
    'composer.json': 'PHP dependencies',
    
    # Web Frameworks
    'next.config.js': 'Next.js configuration',
    'next.config.mjs': 'Next.js configuration',
    'next.config.ts': 'Next.js TypeScript configuration',
    'nuxt.config.js': 'Nuxt.js configuration',
    'nuxt.config.ts': 'Nuxt.js TypeScript configuration',
    'angular.json': 'Angular workspace configuration',
    'vue.config.js': 'Vue.js configuration',
    'vite.config.js': 'Vite configuration',
    'vite.config.ts': 'Vite TypeScript configuration',
    'svelte.config.js': 'Svelte configuration',
    'webpack.config.js': 'Webpack configuration',
    'rollup.config.js': 'Rollup configuration',
    'snowpack.config.js': 'Snowpack configuration',
    
    # Language Configuration
    'tsconfig.json': 'TypeScript configuration',
    'tsconfig.node.json': 'TypeScript Node configuration', 
    'jsconfig.json': 'JavaScript configuration',
    '.babelrc': 'Babel configuration',
    'babel.config.js': 'Babel configuration',
    'eslint.config.js': '.eslintrc configuration',
    '.eslintrc.json': 'ESLint configuration',
    '.eslintrc.js': 'ESLint configuration',
    'prettier.config.js': 'Prettier configuration',
    '.prettierrc': 'Prettier configuration',
    
    # Styling
    'tailwind.config.js': 'Tailwind CSS configuration',
    'tailwind.config.ts': 'Tailwind CSS TypeScript configuration',
    'postcss.config.js': 'PostCSS configuration',
    'sass.config.js': 'Sass configuration',
    
    # Testing
    'jest.config.js': 'Jest testing configuration',
    'vitest.config.js': 'Vitest configuration',
    'cypress.config.js': 'Cypress testing configuration',
    'playwright.config.js': 'Playwright testing configuration',
    
    # Infrastructure/DevOps
    'docker-compose.yml': 'Docker Compose configuration',
    'docker-compose.yaml': 'Docker Compose configuration',
    'dockerfile': 'Docker container configuration',
    'Dockerfile': 'Docker container configuration',
    '.dockerignore': 'Docker ignore configuration',
    'terraform.tf': 'Terraform infrastructure',
    'main.tf': 'Terraform main configuration',
    'variables.tf': 'Terraform variables',
    'outputs.tf': 'Terraform outputs',
    'kubernetes.yaml': 'Kubernetes configuration',
    'k8s.yaml': 'Kubernetes configuration',
    'helm-chart.yaml': 'Helm chart configuration',
    'serverless.yml': 'Serverless framework configuration',
    'serverless.yaml': 'Serverless framework configuration',
    
    # CI/CD
    '.github/workflows/*.yml': 'GitHub Actions workflow',
    '.github/workflows/*.yaml': 'GitHub Actions workflow',
    '.gitlab-ci.yml': 'GitLab CI configuration',
    'azure-pipelines.yml': 'Azure DevOps pipeline',
    'jenkinsfile': 'Jenkins pipeline configuration',
    'buildspec.yml': 'AWS CodeBuild configuration',
    'appspec.yml': 'AWS CodeDeploy configuration',
    'cloudbuild.yaml': 'Google Cloud Build configuration',
    
    # Environment/Settings
    '.env.example': 'Environment variables template',
    '.env.local': 'Local environment variables',
    '.env.development': 'Development environment variables',
    '.env.production': 'Production environment variables',
    'config.json': 'Application configuration',
    'config.yaml': 'Application configuration',
    'config.yml': 'Application configuration',
    'settings.json': 'Application settings',
    'settings.yaml': 'Application settings',
    'appsettings.json': '.NET application settings',
    'web.config': 'IIS/ASP.NET configuration',
    
    # Database
    'migrations/*.sql': 'Database migration',
    'schema.sql': 'Database schema',
    'database.yml': 'Database configuration',
    'prisma.schema': 'Prisma database schema',
    'sequelize.config.js': 'Sequelize configuration',
    
    # Mobile
    'pubspec.yaml': 'Flutter configuration',
    'android/build.gradle': 'Android build configuration',
    'ios/Podfile': 'iOS CocoaPods configuration',
    'react-native.config.js': 'React Native configuration',
    'metro.config.js': 'Metro bundler configuration',
    'expo.json': 'Expo configuration',
    'app.json': 'React Native/Expo app configuration',
    
    # Editor/IDE
    '.vscode/settings.json': 'VS Code workspace settings',
    '.vscode/launch.json': 'VS Code debug configuration',
    '.vscode/tasks.json': 'VS Code tasks configuration',
    '.idea/': 'IntelliJ IDEA configuration',
    'workspace.xml': 'IDE workspace configuration',
    
    # Other
    'makefile': 'Build automation',
    'Makefile': 'Build automation',
    'CMakeLists.txt': 'CMake build configuration',
    'configure.ac': 'Autotools configuration',
    'setup.py': 'Python package setup',
    'setup.cfg': 'Python package configuration',
    'tox.ini': 'Python testing configuration',
    'pytest.ini': 'Pytest configuration',
    'coverage.ini': 'Code coverage configuration',
    '.gitignore': 'Git ignore configuration',
    '.gitattributes': 'Git attributes configuration',
    'README.md': 'Project documentation',
    'readme.md': 'Project documentation',
    'README.rst': 'Project documentation',
    'CHANGELOG.md': 'Project changelog',
    'LICENSE': 'License file',
    'LICENSE.md': 'License file',
}

AUTO_IGNORE_PATTERNS = [
    # IDE and editor files (from your ignore file)
    '.idea/',
    '.vscode/',
    '.DS_Store',
    'Thumbs.db',
    
    # Build artifacts and dependencies (enhanced from your patterns)
    '.gradle/',
    'build/',
    'dist/',
    'out/',
    'META-INF/',
    'buildSrc/',
    'pkg/',
    '.github/',
    'venv/',
    '.venv/',
    'target/',          # Maven/Java
    'bin/',            # Various
    'obj/',            # .NET
    
    # Node.js and TypeScript (from your patterns + additions)
    'node_modules/',
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    '.next/',
    '.next-env.d.ts',
    
    # Python
    '__pycache__/',
    '.pytest_cache/',
    '*.pyc',
    
    # Testing and coverage
    'coverage/',
    '.nyc_output/',
    '.coverage',
    'htmlcov/',
    
    # Logs and temporary files
    '*.log',
    '*.tmp',
    '*.temp',
    '.env.local',
    '.env.development.local',
    '.env.production.local',
    
    # Version control
    '.git/',
    '.svn/',
    
    # Additional common build artifacts
    'vendor/',          # PHP/Go dependencies
    'Cargo.lock',       # Rust
    'composer.lock',    # PHP
    '.terraform/',      # Terraform
    'terraform.tfstate',
    'terraform.tfstate.backup',
]


def detect_entry_points(files):
    """
    Detect and categorize entry points to help understand program architecture.
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
    This helps understand what each file does.
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
    Prioritize files for consumption - most important context first.
    """
    entry_points = detect_entry_points(files)
    
    # Priority order for understanding:
    prioritized = []
    
    # 1. Main entry points first - these show program flow
    prioritized.extend(entry_points['main_entry'])
    
    # 2. Critical configuration files - these show how the system is set up
    critical_config = detect_critical_config_files(files)
    prioritized.extend(critical_config)
    
    # 3. Other configuration files - framework setup, environment config
    other_config = detect_other_config_files(files, critical_config)
    prioritized.extend(other_config)
    
    # 4. Startup scripts - these show deployment/running procedures  
    prioritized.extend(entry_points['startup_scripts'])
    
    # 5. API routes/controllers - these show system interfaces
    prioritized.extend(entry_points['api_routes'])
    
    # 6. Other important files
    prioritized.extend(entry_points['other_important'])
    
    # 7. Remaining files, sorted alphabetically
    remaining = [f for f in files if f not in prioritized]
    prioritized.extend(sorted(remaining))
    
    return prioritized, entry_points

def detect_critical_config_files(files):
    """
    Detect critical configuration files that should appear very early.
    These are the most important for understanding project setup.
    """
    critical_files = []
    
    # Order of criticality for configuration files
    critical_patterns = [
        # Package/dependency management (highest priority)
        'package.json', 'pom.xml', 'build.gradle', 'build.gradle.kts', 
        'cargo.toml', 'go.mod', 'pyproject.toml', 'requirements.txt',
        
        # Docker and infrastructure
        'docker-compose.yml', 'docker-compose.yaml', 'dockerfile', 'Dockerfile',
        
        # Main framework config
        'next.config.js', 'vite.config.js', 'vite.config.ts', 'angular.json',
        'tailwind.config.js', 'tailwind.config.ts',
        
        # Core language config
        'tsconfig.json', 'jsconfig.json',
        
        # Environment and app settings
        '.env.example', 'config.json', 'config.yaml', 'config.yml',
        'appsettings.json', 'settings.json'
    ]
    
    for pattern in critical_patterns:
        for file_path in files:
            filename = os.path.basename(file_path).lower()
            if filename == pattern.lower():
                critical_files.append(file_path)
                break
    
    return critical_files

def detect_other_config_files(files, already_added):
    """
    Detect other configuration files that should appear before core code.
    """
    config_files = []
    
    for file_path in files:
        if file_path in already_added:
            continue
            
        filename = os.path.basename(file_path).lower()
        filepath_lower = file_path.lower()
        
        # Check against our comprehensive config patterns
        for pattern, description in CONFIG_FILE_PATTERNS.items():
            pattern_lower = pattern.lower()
            
            # Handle wildcard patterns like .github/workflows/*.yml
            if '*' in pattern_lower:
                pattern_parts = pattern_lower.split('*')
                if (len(pattern_parts) == 2 and 
                    filepath_lower.startswith(pattern_parts[0]) and 
                    filepath_lower.endswith(pattern_parts[1])):
                    config_files.append(file_path)
                    break
            # Handle directory patterns like .idea/
            elif pattern_lower.endswith('/'):
                if pattern_lower[:-1] in filepath_lower:
                    config_files.append(file_path)
                    break
            # Handle exact filename matches
            elif filename == pattern_lower:
                config_files.append(file_path)
                break
    
    return config_files

def get_config_file_description(file_path):
    """
    Get a description of what a configuration file does.
    """
    filename = os.path.basename(file_path).lower()
    filepath_lower = file_path.lower()
    
    # Check exact matches first
    for pattern, description in CONFIG_FILE_PATTERNS.items():
        pattern_lower = pattern.lower()
        
        if '*' in pattern_lower:
            pattern_parts = pattern_lower.split('*')
            if (len(pattern_parts) == 2 and 
                filepath_lower.startswith(pattern_parts[0]) and 
                filepath_lower.endswith(pattern_parts[1])):
                return description
        elif pattern_lower.endswith('/'):
            if pattern_lower[:-1] in filepath_lower:
                return description
        elif filename == pattern_lower:
            return description
    
    return None

def analyze_dependencies(files, base_path):
    """
    Analyze project dependencies and frameworks to help understand the tech stack.
    Returns a dict with framework info, dependencies, and project type.
    """
    analysis = {
        'project_types': set(),
        'frameworks': set(),
        'languages': set(),
        'dependencies': {},
        'package_managers': set(),
        'build_tools': set(),
        'key_files': []
    }
    
    for file_path in files:
        filename = os.path.basename(file_path).lower()
        file_full_path = base_path / file_path
        
        # Package managers and dependency files
        if filename == 'package.json':
            analyze_package_json(file_full_path, analysis)
        elif filename == 'pom.xml':
            analyze_maven_pom(file_full_path, analysis)
        elif filename in ('build.gradle', 'build.gradle.kts'):
            analyze_gradle(file_full_path, analysis)
        elif filename == 'requirements.txt':
            analyze_requirements_txt(file_full_path, analysis)
        elif filename == 'pyproject.toml':
            analyze_pyproject_toml(file_full_path, analysis)
        elif filename == 'cargo.toml':
            analyze_cargo_toml(file_full_path, analysis)
        elif filename == 'go.mod':
            analyze_go_mod(file_full_path, analysis)
        elif filename in ('*.csproj', '*.fsproj', '*.vbproj') or file_path.endswith(('.csproj', '.fsproj', '.vbproj')):
            analyze_dotnet_project(file_full_path, analysis)
        elif filename == 'packages.config':
            analyze_nuget_packages(file_full_path, analysis)
        elif filename == 'gemfile':
            analyze_gemfile(file_full_path, analysis)
        elif filename == 'pubspec.yaml':
            analyze_flutter_pubspec(file_full_path, analysis)
        elif filename in ('podfile', 'package.swift'):
            analyze_ios_dependencies(file_full_path, analysis, filename)
        elif filename == 'cmakelists.txt':
            analyze_cmake(file_full_path, analysis)
        elif filename == 'makefile':
            analyze_makefile(file_full_path, analysis)
        elif filename in ('next.config.js', 'next.config.mjs', 'next.config.ts'):
            analysis['frameworks'].add('Next.js')
            analysis['project_types'].add('Frontend')
            analysis['key_files'].append(file_path)
        elif filename in ('nuxt.config.js', 'nuxt.config.ts'):
            analysis['frameworks'].add('Nuxt.js')
            analysis['project_types'].add('Frontend')
        elif filename == 'angular.json':
            analysis['frameworks'].add('Angular')
            analysis['project_types'].add('Frontend')
        elif filename in ('vue.config.js', 'vite.config.js', 'vite.config.ts'):
            analysis['frameworks'].add('Vue.js')
            analysis['project_types'].add('Frontend')
        elif filename in ('svelte.config.js', 'svelte.config.mjs'):
            analysis['frameworks'].add('Svelte')
            analysis['project_types'].add('Frontend')
        elif filename == 'webpack.config.js':
            analysis['build_tools'].add('Webpack')
        elif filename in ('docker-compose.yml', 'docker-compose.yaml', 'dockerfile'):
            analysis['frameworks'].add('Docker')
            analysis['key_files'].append(file_path)
        elif filename in ('terraform.tf', 'main.tf') or file_path.endswith('.tf'):
            analysis['frameworks'].add('Terraform')
            analysis['project_types'].add('Infrastructure')
        elif filename in ('ansible.yml', 'playbook.yml') or 'ansible' in file_path:
            analysis['frameworks'].add('Ansible')
            analysis['project_types'].add('Infrastructure')
        elif filename == 'serverless.yml':
            analysis['frameworks'].add('Serverless Framework')
            analysis['project_types'].add('Cloud/Serverless')
    
    # Detect project types based on file patterns
    detect_project_patterns(files, analysis)
    
    return analysis

def analyze_package_json(file_path, analysis):
    """Parse package.json for Node.js/frontend dependencies"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis['package_managers'].add('npm/yarn')
        analysis['languages'].add('JavaScript')
        analysis['key_files'].append(str(file_path.name))
        
        # Combine dependencies
        all_deps = {}
        all_deps.update(data.get('dependencies', {}))
        all_deps.update(data.get('devDependencies', {}))
        analysis['dependencies']['npm'] = all_deps
        
        # Framework detection
        frameworks_map = {
            'react': 'React',
            'next': 'Next.js',
            'vue': 'Vue.js',
            'nuxt': 'Nuxt.js',
            'angular': 'Angular',
            'svelte': 'Svelte',
            'express': 'Express.js',
            'fastify': 'Fastify',
            'nest': 'NestJS',
            'gatsby': 'Gatsby',
            'remix': 'Remix',
            'electron': 'Electron',
            'react-native': 'React Native',
            'expo': 'Expo',
            'ionic': 'Ionic',
            'typescript': 'TypeScript'
        }
        
        for dep_name, framework in frameworks_map.items():
            if any(dep_name in dep.lower() for dep in all_deps.keys()):
                analysis['frameworks'].add(framework)
        
        # Project type detection
        if any(dep in all_deps for dep in ['react-native', 'expo']):
            analysis['project_types'].add('Mobile App')
        elif any(dep in all_deps for dep in ['react', 'vue', 'angular', 'svelte']):
            analysis['project_types'].add('Frontend')
        elif any(dep in all_deps for dep in ['express', 'fastify', 'nest']):
            analysis['project_types'].add('Backend API')
            
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_maven_pom(file_path, analysis):
    """Parse Maven pom.xml for Java dependencies"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        analysis['package_managers'].add('Maven')
        analysis['languages'].add('Java')
        analysis['key_files'].append('pom.xml')
        
        # Handle XML namespaces
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'} if 'maven.apache.org' in str(root.tag) else {}
        
        deps = {}
        for dep in root.findall('.//dependency' if not ns else './/m:dependency', ns):
            group_id = dep.find('groupId' if not ns else 'm:groupId', ns)
            artifact_id = dep.find('artifactId' if not ns else 'm:artifactId', ns)
            version = dep.find('version' if not ns else 'm:version', ns)
            
            if group_id is not None and artifact_id is not None:
                key = f"{group_id.text}:{artifact_id.text}"
                deps[key] = version.text if version is not None else "unknown"
        
        analysis['dependencies']['maven'] = deps
        
        # Framework detection
        framework_patterns = {
            'spring': 'Spring Framework',
            'spring-boot': 'Spring Boot',
            'quarkus': 'Quarkus',
            'micronaut': 'Micronaut',
            'junit': 'JUnit',
            'hibernate': 'Hibernate',
            'jackson': 'Jackson',
            'apache-kafka': 'Apache Kafka',
            'vertx': 'Vert.x'
        }
        
        for dep_key in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_key.lower():
                    analysis['frameworks'].add(framework)
        
        analysis['project_types'].add('Java Application')
        
    except (ET.ParseError, FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_gradle(file_path, analysis):
    """Parse Gradle build files"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis['package_managers'].add('Gradle')
        analysis['build_tools'].add('Gradle')
        
        if file_path.name.endswith('.kts'):
            analysis['languages'].add('Kotlin')
        else:
            analysis['languages'].add('Groovy')
            
        # Detect Android
        if 'com.android.application' in content or 'com.android.library' in content:
            analysis['frameworks'].add('Android')
            analysis['project_types'].add('Mobile App')
            analysis['languages'].add('Java/Kotlin')
        
        # Detect Spring Boot
        if 'org.springframework.boot' in content:
            analysis['frameworks'].add('Spring Boot')
            analysis['project_types'].add('Java Application')
            
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_requirements_txt(file_path, analysis):
    """Parse Python requirements.txt"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        analysis['package_managers'].add('pip')
        analysis['languages'].add('Python')
        analysis['key_files'].append('requirements.txt')
        
        deps = {}
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                # Handle requirements like 'package==1.0.0' or 'package>=1.0.0'
                match = re.match(r'^([a-zA-Z0-9\-_\.]+)([><=!]+.*)?', line)
                if match:
                    pkg_name = match.group(1).lower()
                    version = match.group(2) if match.group(2) else ""
                    deps[pkg_name] = version
        
        analysis['dependencies']['pip'] = deps
        
        # Framework detection
        framework_patterns = {
            'django': 'Django',
            'flask': 'Flask',
            'fastapi': 'FastAPI',
            'tornado': 'Tornado',
            'pyramid': 'Pyramid',
            'celery': 'Celery',
            'pandas': 'Pandas',
            'numpy': 'NumPy',
            'tensorflow': 'TensorFlow',
            'pytorch': 'PyTorch',
            'scikit-learn': 'Scikit-learn',
            'requests': 'Requests',
            'sqlalchemy': 'SQLAlchemy'
        }
        
        for dep_name in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_name:
                    analysis['frameworks'].add(framework)
        
        # Project type detection
        if any(fw in analysis['frameworks'] for fw in ['Django', 'Flask', 'FastAPI']):
            analysis['project_types'].add('Backend API')
        elif any(fw in analysis['frameworks'] for fw in ['TensorFlow', 'PyTorch', 'Scikit-learn']):
            analysis['project_types'].add('Machine Learning')
            
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_pyproject_toml(file_path, analysis):
    """Parse Python pyproject.toml"""
    try:
        import tomli
    except ImportError:
        try:
            import tomllib as tomli
        except ImportError:
            return
    
    try:
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        
        analysis['package_managers'].add('pip/poetry')
        analysis['languages'].add('Python')
        analysis['key_files'].append('pyproject.toml')
        
        # Check for Poetry
        if 'tool' in data and 'poetry' in data['tool']:
            analysis['package_managers'].add('Poetry')
            deps = data['tool']['poetry'].get('dependencies', {})
            analysis['dependencies']['poetry'] = deps
            
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_cargo_toml(file_path, analysis):
    """Parse Rust Cargo.toml"""
    try:
        import tomli
    except ImportError:
        try:
            import tomllib as tomli
        except ImportError:
            return
    
    try:
        with open(file_path, 'rb') as f:
            data = tomli.load(f)
        
        analysis['package_managers'].add('Cargo')
        analysis['languages'].add('Rust')
        analysis['key_files'].append('Cargo.toml')
        analysis['project_types'].add('Rust Application')
        
        deps = data.get('dependencies', {})
        analysis['dependencies']['cargo'] = deps
        
        # Framework detection
        framework_patterns = {
            'actix-web': 'Actix Web',
            'warp': 'Warp',
            'rocket': 'Rocket',
            'axum': 'Axum',
            'tokio': 'Tokio',
            'serde': 'Serde',
            'diesel': 'Diesel'
        }
        
        for dep_name in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_name:
                    analysis['frameworks'].add(framework)
                    
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_go_mod(file_path, analysis):
    """Parse Go go.mod file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis['package_managers'].add('Go Modules')
        analysis['languages'].add('Go')
        analysis['key_files'].append('go.mod')
        analysis['project_types'].add('Go Application')
        
        # Extract dependencies
        deps = {}
        in_require_block = False
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('require ('):
                in_require_block = True
                continue
            elif line == ')' and in_require_block:
                in_require_block = False
                continue
            elif in_require_block or line.startswith('require '):
                # Parse require statements
                match = re.match(r'require\s+([^\s]+)\s+([^\s]+)', line) or re.match(r'([^\s]+)\s+([^\s]+)', line)
                if match:
                    deps[match.group(1)] = match.group(2)
        
        analysis['dependencies']['go'] = deps
        
        # Framework detection
        framework_patterns = {
            'gin-gonic/gin': 'Gin',
            'gorilla/mux': 'Gorilla Mux',
            'echo': 'Echo',
            'fiber': 'Fiber',
            'kubernetes': 'Kubernetes',
            'grpc': 'gRPC'
        }
        
        for dep_name in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_name:
                    analysis['frameworks'].add(framework)
                    
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_dotnet_project(file_path, analysis):
    """Parse .NET project files (.csproj, .fsproj, .vbproj)"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        analysis['package_managers'].add('NuGet')
        analysis['languages'].add('C#/.NET')
        analysis['project_types'].add('.NET Application')
        
        # Extract package references
        deps = {}
        for pkg_ref in root.findall('.//PackageReference'):
            include = pkg_ref.get('Include')
            version = pkg_ref.get('Version')
            if include:
                deps[include] = version or "unknown"
        
        analysis['dependencies']['nuget'] = deps
        
        # Framework detection
        framework_patterns = {
            'Microsoft.AspNetCore': 'ASP.NET Core',
            'Microsoft.EntityFrameworkCore': 'Entity Framework Core',
            'Xamarin': 'Xamarin',
            'Microsoft.Maui': 'MAUI',
            'Blazor': 'Blazor'
        }
        
        for dep_name in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_name:
                    analysis['frameworks'].add(framework)
                    
    except (ET.ParseError, FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_flutter_pubspec(file_path, analysis):
    """Parse Flutter pubspec.yaml"""
    try:
        import yaml
    except ImportError:
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        analysis['frameworks'].add('Flutter')
        analysis['languages'].add('Dart')
        analysis['project_types'].add('Mobile App')
        analysis['key_files'].append('pubspec.yaml')
        
        deps = data.get('dependencies', {})
        analysis['dependencies']['flutter'] = deps
        
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_ios_dependencies(file_path, analysis, filename):
    """Parse iOS dependency files"""
    analysis['project_types'].add('Mobile App')
    analysis['languages'].add('Swift/Objective-C')
    
    if filename == 'podfile':
        analysis['package_managers'].add('CocoaPods')
    elif filename == 'package.swift':
        analysis['package_managers'].add('Swift Package Manager')

def analyze_cmake(file_path, analysis):
    """Parse CMakeLists.txt for C/C++ projects"""
    analysis['build_tools'].add('CMake')
    analysis['languages'].add('C/C++')
    analysis['project_types'].add('C/C++ Application')

def analyze_makefile(file_path, analysis):
    """Parse Makefile"""
    analysis['build_tools'].add('Make')
    
def analyze_nuget_packages(file_path, analysis):
    """Parse .NET packages.config for NuGet dependencies"""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        analysis['package_managers'].add('NuGet')
        analysis['languages'].add('C#/.NET')
        analysis['key_files'].append('packages.config')
        
        deps = {}
        for package in root.findall('.//package'):
            package_id = package.get('id')
            version = package.get('version')
            if package_id:
                deps[package_id] = version or "unknown"
        
        analysis['dependencies']['nuget'] = deps
        
        # Framework detection (same as in analyze_dotnet_project)
        framework_patterns = {
            'Microsoft.AspNetCore': 'ASP.NET Core',
            'Microsoft.EntityFrameworkCore': 'Entity Framework Core',
            'Newtonsoft.Json': 'JSON.NET',
            'NUnit': 'NUnit',
            'xunit': 'xUnit'
        }
        
        for dep_name in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_name:
                    analysis['frameworks'].add(framework)
                    
    except (ET.ParseError, FileNotFoundError, UnicodeDecodeError):
        pass

def analyze_gemfile(file_path, analysis):
    """Parse Ruby Gemfile for gem dependencies"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        analysis['package_managers'].add('Bundler')
        analysis['languages'].add('Ruby')
        analysis['key_files'].append('Gemfile')
        analysis['project_types'].add('Ruby Application')
        
        deps = {}
        # Simple parsing for gem declarations
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('gem '):
                # Parse gem "name", "version" format
                import re
                match = re.match(r'gem\s+["\']([^"\']+)["\'](?:\s*,\s*["\']([^"\']+)["\'])?', line)
                if match:
                    gem_name = match.group(1)
                    version = match.group(2) if match.group(2) else "latest"
                    deps[gem_name] = version
        
        analysis['dependencies']['bundler'] = deps
        
        # Framework detection
        framework_patterns = {
            'rails': 'Ruby on Rails',
            'sinatra': 'Sinatra',
            'rack': 'Rack',
            'rspec': 'RSpec',
            'minitest': 'MiniTest',
            'devise': 'Devise',
            'activerecord': 'ActiveRecord'
        }
        
        for dep_name in deps.keys():
            for pattern, framework in framework_patterns.items():
                if pattern in dep_name.lower():
                    analysis['frameworks'].add(framework)
        
        # Project type detection
        if 'rails' in analysis['frameworks']:
            analysis['project_types'].add('Web Application')
            
    except (FileNotFoundError, UnicodeDecodeError):
        pass

def detect_project_patterns(files, analysis):
    """Detect project types based on file patterns"""
    file_patterns = {
        'Mobile App': ['.swift', '.m', '.kt', '.java', '.dart'],
        'Frontend': ['.jsx', '.tsx', '.vue', '.svelte'],
        'Backend API': ['.py', '.java', '.go', '.rs', '.cs'],
        'Shell/DevOps': ['.sh', '.bash', '.zsh', '.fish'],
        'Infrastructure': ['.tf', '.yml', '.yaml'],
        'Documentation': ['.md', '.rst', '.txt']
    }
    
    file_extensions = [os.path.splitext(f)[1].lower() for f in files]
    
    for project_type, extensions in file_patterns.items():
        if any(ext in file_extensions for ext in extensions):
            analysis['project_types'].add(project_type)

def format_dependency_summary(analysis):
    """Format dependency analysis for consumption"""
    if not any([analysis['frameworks'], analysis['dependencies'], analysis['project_types']]):
        return ""
    
    summary = "## Dependency Analysis & Tech Stack\n\n"
    
    if analysis['project_types']:
        summary += f"**Project Type(s)**: {', '.join(sorted(analysis['project_types']))}\n"
    
    if analysis['languages']:
        summary += f"**Languages**: {', '.join(sorted(analysis['languages']))}\n"
    
    if analysis['frameworks']:
        summary += f"**Frameworks/Libraries**: {', '.join(sorted(analysis['frameworks']))}\n"
    
    if analysis['package_managers']:
        summary += f"**Package Managers**: {', '.join(sorted(analysis['package_managers']))}\n"
    
    if analysis['build_tools']:
        summary += f"**Build Tools**: {', '.join(sorted(analysis['build_tools']))}\n"
    
    # Key dependencies summary
    if analysis['dependencies']:
        summary += f"**Key Dependencies**:\n"
        for pm, deps in analysis['dependencies'].items():
            if deps:
                key_deps = list(deps.keys())[:5]  # Show first 5 dependencies
                more_count = len(deps) - 5
                summary += f"- {pm.title()}: {', '.join(key_deps)}"
                if more_count > 0:
                    summary += f" (+{more_count} more)"
                summary += "\n"
    
    summary += "\n"
    return summary
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

def smart_truncate_by_chars(content, file_path, max_chars=50000):
    """
    Truncate by character count for very large files only.
    Most source files under 50KB will not be truncated.
    """
    if len(content) <= max_chars:
        return content, False
    
    # Find a good place to cut (try to end at a complete line)
    truncate_point = max_chars
    
    # Look backwards for a newline within the last 500 chars
    for i in range(max_chars, max(max_chars - 500, 0), -1):
        if content[i] == '\n':
            truncate_point = i
            break
    
    truncated_content = content[:truncate_point]
    truncated_content += '\n\n# <TRUNCATED>\n'
    truncated_content += f'# Original file: {len(content):,} characters (~{len(content)//1000}KB)\n'
    truncated_content += f'# Showing first: {truncate_point:,} characters (~{truncate_point//1000}KB)\n'
    truncated_content += '# Ask for the complete file if you need to see the rest\n'
    truncated_content += '# </TRUNCATED>'
    
    return truncated_content, True

def should_auto_ignore(file_path):
    """
    Check if file should be automatically ignored.
    Handles nested directories properly.
    
    Examples:
    - 'frontend/node_modules/react/index.js' -> True (contains node_modules/)
    - 'backend/dist/main.js' -> True (contains dist/)
    - 'src/components/Button.js' -> False
    """
    # Normalize path separators for cross-platform compatibility
    normalized_path = file_path.replace('\\', '/')
    path_parts = normalized_path.split('/')
    
    for pattern in AUTO_IGNORE_PATTERNS:
        if pattern.endswith('/'):
            # Directory pattern - check if any part of the path matches
            dir_name = pattern[:-1]  # Remove trailing slash
            if dir_name in path_parts:
                return True
        elif pattern.startswith('*.'):
            # Extension pattern
            if normalized_path.endswith(pattern[1:]):
                return True
        else:
            # Exact filename pattern
            filename = path_parts[-1]  # Get just the filename
            if filename == pattern:
                return True
    
    return False

def load_gitignore_patterns(base_path):
    """Load patterns from .gitignore if it exists"""
    gitignore_path = base_path / '.gitignore'
    if gitignore_path.exists():
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                patterns = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        patterns.append(line)
                return patterns
        except Exception as e:
            print(f"Warning: Could not read .gitignore: {e}")
    return []

def matches_gitignore_pattern(file_path, pattern):
    """
    Check if a file path matches a gitignore pattern.
    Simplified implementation - handles most common cases.
    """
    # Convert to forward slashes for consistency
    file_path = file_path.replace('\\', '/')
    pattern = pattern.replace('\\', '/')
    
    # Handle directory patterns
    if pattern.endswith('/'):
        return f'/{pattern}' in f'/{file_path}' or file_path.startswith(pattern)
    
    # Handle wildcard patterns
    if '*' in pattern:
        import fnmatch
        # Check against filename only for simple patterns
        if '/' not in pattern:
            filename = file_path.split('/')[-1]
            return fnmatch.fnmatch(filename, pattern)
        else:
            return fnmatch.fnmatch(file_path, pattern)
    
    # Handle exact matches
    if '/' in pattern:
        return pattern in file_path
    else:
        # Pattern without slash matches filename only
        filename = file_path.split('/')[-1]
        return filename == pattern

def matches_gitignore(file_path, gitignore_patterns):
    """Check if file matches any gitignore pattern"""
    for pattern in gitignore_patterns:
        if matches_gitignore_pattern(file_path, pattern):
            return True
    return False

def should_include_file(file_path, allowed_extensions, gitignore_patterns=None):
    """
    Determine if file should be included in the summary.
    
    Args:
        file_path: Relative path from base directory
        allowed_extensions: Set of allowed file extensions
        gitignore_patterns: List of gitignore patterns (optional)
    
    Returns:
        bool: True if file should be included
    """
    
    # First check auto-ignore patterns (build artifacts, etc.)
    if should_auto_ignore(file_path):
        return False
    
    # Check gitignore patterns if available
    if gitignore_patterns and matches_gitignore(file_path, gitignore_patterns):
        return False
    
    # Check file extension
    ext = os.path.splitext(file_path)[1].lower()
    return ext in allowed_extensions


def print_file_contents(starting_dir='.', output_file=None, toc=False, ignore_spec=None, ignore_extensions=None):
    """
    Recursively process files with allowed extensions from starting_dir, excluding those matching ignore_spec
    or ignore_extensions, and either print their contents or write to an output file. Prioritizes files
    for better understanding.

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

    gitignore_patterns = load_gitignore_patterns(base_path)
    if gitignore_patterns:
        print(f"Loaded {len(gitignore_patterns)} patterns from .gitignore")
        
    try:
        for root, dirs, files in os.walk(starting_dir):
            relative_root = os.path.relpath(root, base_path).replace(os.sep, '/')
            
            if should_auto_ignore(relative_root + '/'):
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
                
                if should_auto_ignore(relative_path):
                    continue
                    
                if gitignore_patterns and matches_gitignore(relative_path, gitignore_patterns):
                    continue
                
                files_to_include.append(relative_path)
        
        prioritized_files, entry_points = prioritize_files(files_to_include, base_path)
        
        # Analyze dependencies and tech stack
        dependency_analysis = analyze_dependencies(files_to_include, base_path)

        # Write top-level heading and initial message
        message = "# Codebase Summary\n\nThe following is a complete codebase summary optimized for structural analysis. Files are prioritized by importance - entry points and configuration first, followed by core application logic. This ordering helps establish program flow and architecture context upfront.\n\n"
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
        
        # Enhanced project overview with entry point information and tech stack
        dep_files = [f for f in files_to_include if os.path.basename(f) in ('package.json', 'pom.xml', 'requirements.txt', 'build.gradle', 'pyproject.toml', 'go.mod', 'cargo.toml', 'pubspec.yaml')]
        dep_summary = f"- Dependency files: {', '.join(dep_files)}\n" if dep_files else "- Dependency files: None detected\n"

        # Entry points summary for context
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

        # Configuration files summary for context
        config_files = detect_critical_config_files(files_to_include) + detect_other_config_files(files_to_include, detect_critical_config_files(files_to_include))
        config_summary = ""
        if config_files:
            config_summary = "## Configuration Files\n\n"
            for config_file in config_files[:8]:  # Show first 8 config files
                desc = get_config_file_description(config_file)
                if desc:
                    config_summary += f"**{config_file}**: {desc}\n"
                else:
                    config_summary += f"**{config_file}**: Configuration file\n"
            if len(config_files) > 8:
                config_summary += f"*...and {len(config_files) - 8} more configuration files*\n"
            config_summary += "\n"
        
        # Add dependency analysis
        dependency_summary = format_dependency_summary(dependency_analysis)
        
        overview = f"## Project Overview\n\n- Total files: {len(files_to_include)}\n- Languages used: {', '.join(sorted(lang_counts.keys()))}\n- Approximate total lines: {total_lines}\n{dep_summary}\n{entry_summary}{config_summary}{dependency_summary}"
        
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
        code_files_header = "## Code Files (Priority Order)\n\n*Files are ordered by importance for analysis: entry points → configuration → core logic → supporting files*\n\n"
        if output:
            output.write(code_files_header)
        else:
            print(code_files_header)
        
        # Output each file's contents in prioritized order
        for relative_path in prioritized_files:
            full_path = base_path / relative_path
            ext = os.path.splitext(relative_path)[1].lower()
            lang = EXT_TO_LANG.get(ext, '')
            
            # Determine file role for context
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
                    
                truncated_contents, was_truncated = smart_truncate_by_chars(contents, relative_path)
                
                line_count = len(contents.splitlines())
                file_size = os.path.getsize(full_path)
                
                # Enhanced metadata with role, and config info
                metadata_parts = [f"{line_count} lines, {file_size} bytes"]
                if role_indicators:
                    metadata_parts.append(role_indicators[0])
                
                if was_truncated:
                    metadata_parts.append(f"**TRUNCATED** (showing ~{len(truncated_contents):,} chars)")
                
                #  configuration file description
                config_desc = get_config_file_description(relative_path)
                if config_desc:
                    metadata_parts.append(f"Config: {config_desc}")
                
                metadata = f"**Metadata**: {' | '.join(metadata_parts)}\n\n"
                
                if was_truncated:
                    metadata += f"📄 **LARGE FILE NOTICE**: This file was truncated for readability.\n"
                    metadata += f"**Original size**: {line_count:,} lines ({file_size:,} bytes)\n"
                    metadata += f"**To see complete file**: Ask me to \"show the full contents of {relative_path}\"\n\n"
                
                output_str = header + metadata + f"```{lang}\n{truncated_contents.rstrip()}\n```\n\n"
                
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
        description="Create optimized codebase summaries with intelligent file prioritization."
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