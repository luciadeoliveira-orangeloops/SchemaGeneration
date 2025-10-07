# 🗄️ Schema Generation - Automated Database Schema Creator

A complete system for automatically generating database schemas from documentation and Figma designs, with AI-powered interactive refinement.

## 📋 Table of Contents

- [🚀 Quick Start](#-quick-start)
- [📦 Installation](#-installation)
- [🔧 Configuration](#-configuration)
- [📖 Complete Usage Guide](#-complete-usage-guide)
- [🎯 Main Commands](#-main-commands)
- [📝 Interactive Refinement System](#-interactive-refinement-system)
- [🗃️ Prisma Schema Generation](#️-prisma-schema-generation)
- [📁 Project Structure](#-project-structure)
- [🐛 Troubleshooting](#-troubleshooting)

## ✨ Key Features

- 🎨 **Figma Integration**: Extract wireframe data directly from Figma using MCP
- 🤖 **AI Analysis**: Uses OpenAI GPT-4o to analyze UI components and generate business entities
- 📊 **Schema Generation**: Creates complete Entity-Relationship models with attributes and relationships
- 🔄 **Interactive Refinement**: Hybrid system to answer questions via terminal or markdown
- 🏗️ **Multiple Formats**: Generates Prisma schemas
- 🔍 **Smart Analysis**: Automatically infers entities, attributes and relationships

---

## 🚀 Quick Start

### Basic 3-step workflow:

```bash
# 1. Generate initial schema
uv run python ai_to_schema.py

# 2. Refine schema interactively
uv run python pipeline/interactive_refinement.py

# 3. Generate Prisma schema
uv run python projectors/prisma/to_prisma.py
```

---

## 📦 Installation

### Prerequisites:
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- OpenAI API access
- Figma access (optional)

### Installation:

```bash
# Install dependencies (uv installs them automatically)
uv sync
```
---

## 🔧 Configuration

### Required environment variables:

Create a `.env` file in the project root:

```env
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Model to use (optional, default: gpt-4o)
LLM_MODEL=gpt-4o

# Figma Access Token (optional, only if using Figma)
FIGMA_ACCESS_TOKEN=your-figma-token-here

# MCP Server URL (optional, defaults to local server)
MCP_SERVER_URL=http://localhost:3000
```

### Required input files:

1. **Documentation** (`docs/` folder):
   - `requirements.pdf` - Project specifications
   - Other relevant documents

---

## 📋 Main Commands

### 1. `ai_to_schema.py` - Initial schema generation

Executes the complete pipeline from documents + Figma to generate the initial MER.

```bash
uv run ai_to_schema.py
```

**What it does:**
- Reads documentation from `docs/` folder
- Connects to Figma (if configured) to extract design data
- Analyzes both sources using AI
- Generates initial MER in `schema/mer.json`

**Generated files:**
- `schema/mer.json` - Generated Entity-Relationship Model
- `context/figma-ai-analysis.json` - AI analysis of Figma data (if applicable)

**Prerequisites:**
- Documentation files in `docs/` folder
- OpenAI API key configured

---

### 2. `pipeline/interactive_refinement.py` - Interactive refinement

Interactive refinement system with hybrid terminal/markdown workflow.

```bash
uv run pipeline/interactive_refinement.py [options]
```

**Arguments:**
- `--schema-file PATH` - Path to schema file (default: `schema/mer.json`)
- `--from-markdown FILE` - Resume from existing markdown file
- `--output-file PATH` - Output path for refined schema (default: `schema/mer_refined.json`)

**Interactive options:**
1. **Answer all questions interactively** - Terminal Q&A with auto-save to markdown
2. **Skip all questions and save to markdown** - Generate markdown file directly
3. **Load answers from existing markdown** - Resume from previously saved markdown file

**What it does:**
- Analyzes current schema for potential improvements
- Generates contextual questions about business logic, relationships and constraints
- Provides flexible workflow: terminal interaction OR markdown file editing
- Automatically saves progress and generates refined schema

**Generated files:**
- `questions_YYYYMMDD_HHMMSS.md` - Generated questions in markdown format
- `schema/mer_refined.json` - Refined schema based on answers

**Usage examples:**

```bash
# Standard interactive refinement
uv run pipeline/interactive_refinement.py

# Use specific schema file
uv run pipeline/interactive_refinement.py --schema-file my_schema.json

# Resume from existing markdown
uv run pipeline/interactive_refinement.py --from-markdown questions_20241207_143022.md
```

---

### 3. `projectors/prisma/to_prisma.py` - Prisma schema generation

Converts MER JSON to production-ready Prisma schema.

```bash
uv run projectors/prisma/to_prisma.py [options]
```

**Arguments:**
- `--input PATH` - Input MER JSON file (default: `schema/mer_refined.json`)
- `--output PATH` - Output Prisma schema file (default: `schema.prisma`)

**What it does:**
- Converts MER JSON to Prisma schema format
- Handles proper type mapping (String, Int, DateTime, etc.)
- Generates enums with appropriate default values
- Creates relationships with proper referential integrity
- Produces professional, production-ready Prisma schemas

**Generated file:**
- `schema.prisma` - Complete Prisma schema ready for use

**Usage examples:**

```bash
# Generate Prisma schema from refined MER
uv run projectors/prisma/to_prisma.py

# Use specific files
uv run projectors/prisma/to_prisma.py --input schema/mer.json --output my-schema.prisma
```

---

## 📖 Complete Usage Guide

### Typical workflow:

1. **Prepare documentation**: Place relevant files in `docs/`
2. **Generate initial schema**: `uv run ai_to_schema.py`
3. **Refine interactively**: `uv run pipeline/interactive_refinement.py`
4. **Generate Prisma**: `uv run projectors/prisma/to_prisma.py`
5. **Use in project**: Copy `schema.prisma` to your project