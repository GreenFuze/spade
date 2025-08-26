# FakeApp - Test Application for SPADE

This is a test application with a multi-language project structure to test SPADE workspace initialization and ignore/allow patterns.

## Project Structure

```
fakeapp/
├── src/                    # Source code
│   ├── api/               # API layer
│   ├── cli/               # Command line interface
│   ├── server/            # Server components
│   └── web/               # Web frontend
├── tests/                 # Test files
├── docs/                  # Documentation
├── build/                 # Build artifacts (should be ignored)
├── node_modules/          # Node.js dependencies (should be ignored)
├── __pycache__/           # Python cache (should be ignored)
├── .git/                  # Git repository (should be ignored)
├── .vscode/               # VS Code settings (should be ignored)
├── .idea/                 # IntelliJ settings (should be ignored)
├── .github/               # GitHub workflows (should be visible)
├── package.json           # Node.js package file
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

## Purpose

This application is designed to test:
- Workspace initialization with `--init-workspace`
- Ignore patterns in `.spadeignore`
- Allow patterns in `.spadeallow`
- Configuration loading from `run.json`
