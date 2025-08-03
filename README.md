# GitHub Star Auto Classification

🌟 AI-powered tool to automatically classify GitHub starred repositories into different star lists, supporting both automatic updates and existing list modes.

## System Overview

This project is built on [Pocket Flow](https://github.com/The-Pocket/PocketFlow) framework using Agentic Coding design patterns:

```mermaid
flowchart TD
    A[User/GitHub Actions] --> B[main.py]
    B --> C[Star Classification Flow]
    
    subgraph Flow["Star Classification Workflow"]
        D[Initialize<br/>Config & Validation] --> E[Fetch Starred Repos<br/>Get Repository Data]
        E --> F[Mode Decision<br/>Auto vs Existing Lists]
        F --> G[AI Analysis<br/>Batch Classification]
        G --> H[Manage Star Lists<br/>Create & Update Lists]
    end
    
    C --> D
    
    subgraph Utils["Core Components"]
        I[Configuration<br/>Settings & Options]
        J[GitHub Client<br/>API Operations]
        K[AI Analyzer<br/>Repository Classification]
        L[List Manager<br/>Smart Summary Generation]
        M[LLM Interface<br/>OpenAI Compatible]
    end
    
    D --> I
    E --> J
    F --> J
    G --> K
    H --> L
    K --> M
    L --> M
    
    subgraph External["External APIs"]
        N[GitHub API]
        O[OpenAI Compatible API]
    end
    
    J --> N
    M --> O
    
    subgraph Results["Outputs"]
        P[Organized Star Lists]
        Q[Classification Report]
        R[System Logs]
    end
    
    H --> P
    H --> Q
    B --> R
```

## Features

- 🤖 **AI-Driven Classification**: Automatic repository analysis and categorization
- 📋 **Dual Modes**: Auto creation or existing list management
- ✨ **Smart Summaries**: AI-powered list descriptions and enhancements
- ⚡ **GitHub Actions**: Automated scheduling and manual triggers
- 🔧 **Flexible Config**: Multiple LLM providers, custom settings

## Quick Start

### 1. Clone the Project

```bash
git clone https://github.com/your-username/star-tidy.git
cd star-tidy
```

### 2. Install Dependencies

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install project dependencies
uv sync
```

### 3. Configure Environment Variables

Create a `.env` file or set environment variables:

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"  # GitHub Personal Access Token
export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxx"   # OpenAI API Key
export OPENAI_API_BASE="https://api.openai.com/v1"  # Optional, for compatible services
export AI_MODEL="gpt-4o-mini"  # Optional, default model
```

### 4. Run Classification

```bash
# Quick start (runs with default settings)
uv run star-tidy

# Or using python directly
uv run python main.py

# Dry run mode (test without actual changes)
uv run star-tidy star --dry-run

# Verbose logging
uv run star-tidy --verbose

# With summary options
uv run star-tidy star --auto-complete-summaries --enhance-existing-summaries

# Exclude specific repositories
uv run star-tidy star --exclude-repo "user/repo1" --exclude-repo "user/repo2"

# Use existing lists mode
uv run star-tidy star --mode existing_lists

# Interactive setup wizard
uv run star-tidy setup

# Use alternative LLM providers
uv run star-tidy star --api-base https://api.deepseek.com --ai-model deepseek-chat
uv run star-tidy star --api-base https://api.groq.com/openai/v1 --ai-model llama3-8b-8192
```

## CLI Commands

The tool provides several commands for different operations:

### Main Commands

```bash
# Show help and available commands
uv run star-tidy --help

# Run star classification (default command)
uv run star-tidy star [OPTIONS]

# Show current configuration
uv run star-tidy config

# Interactive setup wizard
uv run star-tidy setup

# Run system tests
uv run star-tidy test

# Test LLM connection
uv run star-tidy test-llm

# Legacy Q&A mode
uv run star-tidy qa
```

### Star Command Options

```bash
# Classification modes
--mode auto                    # Create new lists automatically (default)
--mode existing_lists          # Use existing star lists

# Summary options
--auto-complete-summaries      # Auto-complete missing descriptions
--enhance-existing-summaries   # Enhance existing descriptions
--use-ai-summary              # Use AI for summary generation
--include-stats               # Include repository statistics

# Repository filtering
--exclude-repo "user/repo"     # Exclude specific repositories (repeatable)

# LLM Configuration
--ai-model gpt-4o-mini         # AI model to use
--api-base https://api.openai.com/v1  # API base URL for compatible services
--max-tokens 1000              # Maximum tokens to generate
--temperature 0.7              # Sampling temperature (0-2)

# Configuration
--config path/to/config.yaml   # Use specific config file
--dry-run                     # Test mode (no actual changes)
```

### Interactive Setup

```bash
# Set up configuration interactively
uv run star-tidy setup

# Advanced setup with custom config file
uv run star-tidy setup --config-file my-config.yaml
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GITHUB_TOKEN` | Yes | - | GitHub Personal Access Token |
| `OPENAI_API_KEY` | Yes | - | OpenAI API Key |
| `OPENAI_API_BASE` | No | `https://api.openai.com/v1` | API Base URL |
| `AI_MODEL` | No | `gpt-4o-mini` | AI Model to use |
| `STAR_TIDY_MODE` | No | `auto` | Run mode (`auto` or `existing_lists`) |
| `DRY_RUN` | No | `false` | Whether to run in dry-run mode |
| `AUTO_COMPLETE_SUMMARIES` | No | `true` | Auto-complete missing descriptions |
| `ENHANCE_EXISTING_SUMMARIES` | No | `true` | Enhance existing descriptions |
| `MAX_TOKENS` | No | - | Maximum tokens to generate |
| `TEMPERATURE` | No | - | Sampling temperature (0-2) |

### Configuration File

Copy `config.example.yaml` to `config.yaml` and customize as needed:

```yaml
mode: "auto"  # or "existing_lists"
exclude_repos:
  - "user/repo-to-exclude"
dry_run: false
summary_options:
  auto_complete: true
  enhance_existing: true
  use_ai_summary: true
  include_stats: true
```

## GitHub Actions Setup

### 1. Configure Secrets

Add the following Secrets in your GitHub repository settings:

- `OPENAI_API_KEY`: OpenAI API Key
- Optional: `OPENAI_API_BASE`, `AI_MODEL`

### 2. Enable Actions

The project includes pre-configured GitHub Actions workflow:

- **Manual Trigger**: Run manually from Actions page with customizable options
- **Scheduled Execution**: Automatically runs every Sunday at 2 AM
- **Custom Trigger**: Modify `.github/workflows/star-classification.yml`

### 3. New Summary Options

The workflow now supports additional options:
- Auto-complete missing list descriptions
- Enhance existing list descriptions
- Configurable through workflow inputs

## Operation Modes

### Auto Mode (`auto`)

AI automatically analyzes repositories and creates new star lists:

- Automatically categorizes based on tech stack, purpose, etc.
- Creates semantic category names
- AI-powered list descriptions with statistics
- Suitable for starting fresh organization of star lists

### Existing Lists Mode (`existing_lists`)

Classifies based on user's existing star lists:

- Uses existing classifications as reference
- Assigns new repositories to appropriate existing categories
- Auto-completes missing list descriptions
- Enhances existing descriptions with updated information
- Suitable for maintaining existing classification systems

## Directory Structure

```
star-tidy/
├── main.py              # Main program entry
├── flow.py              # Flow definitions  
├── nodes.py             # Core node implementations
├── utils/               # Utility functions
│   ├── call_llm.py      # LLM API calls
│   ├── github_client.py # GitHub API client
│   ├── repo_analyzer.py # Repository analyzer
│   ├── star_list_manager.py # Smart list manager
│   └── config.py        # Configuration management
├── .github/workflows/   # GitHub Actions
└── pyproject.toml       # UV project configuration
```

## Development Guide

- Built on [Pocket Flow](https://github.com/The-Pocket/PocketFlow) framework
- Install dev dependencies: `uv sync --extra dev`
- Run tests: `uv run pytest`
- Format code: `uv run black .`

## License

MIT License
