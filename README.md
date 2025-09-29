# SchemaGeneration 🚀

AI-powered pipeline to generate database schemas from Figma wireframes using OpenAI and Model Context Protocol (MCP).

## ✨ Features

- 🎨 **Figma Integration**: Extract wireframe data directly from Figma using MCP
- 🤖 **AI Analysis**: Use OpenAI GPT-5 to analyze UI components and generate business entities
- 📊 **Schema Generation**: Create complete Entity-Relationship models with attributes and relationships
- 🏗️ **Multi-format Output**: Generate Prisma schemas, SQL, and JSON outputs
- 🔍 **Smart Analysis**: Automatically infer entities, attributes, and relationships from component names

## 🛠️ Setup

### 1. Install Dependencies

```bash
# Install Python dependencies
uv sync

# Install Figma MCP server (Node.js required)
npm install -g figma-developer-mcp
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
```

Required environment variables:
```env
OPENAI_API_KEY=your_openai_api_key_here
FIGMA_ACCESS_TOKEN=your_figma_access_token_here
FIGMA_FILE_ID=your_figma_file_id_here
```

### 3. Get Figma Credentials

1. **Figma Access Token**: Go to [Figma Settings → Personal Access Tokens](https://www.figma.com/developers/api#access-tokens)
2. **File ID**: From your Figma URL: `https://www.figma.com/file/{FILE_ID}/...`

## 🚀 Usage

### Generate Schema from Figma (Complete Pipeline)

```bash
# Run the complete AI-powered pipeline
uv run python ai_to_schema.py
```

This will:
1. 📋 Extract raw data from Figma via MCP
2. 🤖 Analyze component names with OpenAI to identify business entities
3. ⚙️ Run the complete schema generation pipeline
4. 📄 Generate final `schema/mer.json`

### Manual Steps (Advanced)

If you want to run steps individually:

```bash
# 1. Extract Figma data
uv run python simple_figma_test.py

# 2. Generate context pack and run pipeline
uv run python generate_from_figma.py --skip-figma

# 3. Generate Prisma schema (optional)
uv run python -m pipeline.run_all prisma schema/mer.json schema.prisma
```

## 📁 Project Structure

```
├── ai_to_schema.py          # 🎯 Main pipeline script (START HERE)
├── simple_figma_test.py     # 🎨 Figma MCP data extraction
├── generate_from_figma.py   # 🔄 Alternative pipeline runner
├── 
├── extractors/              # 📊 Data extraction modules
│   ├── figma_ai_analyzer.py # 🤖 AI-powered Figma analysis
│   └── figma_mcp_client.py  # 🔌 Figma MCP connection
├── 
├── pipeline/                # ⚙️ Schema generation pipeline
│   ├── run_all.py          # 📋 Pipeline orchestrator
│   └── passes/             # 🔄 Individual processing passes
├── 
├── llm/                    # 🧠 OpenAI integration
├── prompts/                # 💬 LLM prompts for each pass
├── merge/                  # 🔀 Data merging and alignment
├── validate/               # ✅ Schema validation
├── projectors/             # 🏗️ Output format generators
│   └── prisma/            # 📊 Prisma schema generation
└── 
└── schema/                 # 📄 Generated schemas (gitignored)
    └── mer.json           # 🎯 Final Entity-Relationship model
```

## 📊 Output Format

The pipeline generates a complete MER (Model Entity-Relationship) in JSON format:

```json
{
  "entities": [
    {
      "name": "User",
      "description": "User account with authentication",
      "attributes": [
        {
          "name": "id",
          "type": "string",
          "pk": true,
          "nullable": false
        },
        {
          "name": "email",
          "type": "email",
          "unique": true,
          "nullable": false
        }
      ],
      "confidence": 0.9
    }
  ],
  "relationships": [
    {
      "from": "Project",
      "to": "User", 
      "type": "many-to-one",
      "fk": {
        "attribute": "userId",
        "ref": "User.id"
      }
    }
  ]
}
```

## 🔧 How It Works

### 1. Figma Analysis 🎨
- Connects to Figma via MCP (Model Context Protocol)
- Extracts component names and structure
- Example: "Inicio de Sesion" → Login functionality

### 2. AI Entity Extraction 🤖
- Sends component names to OpenAI GPT-5
- AI analyzes UI context to infer business entities
- Example: Login screen → User entity with email, password attributes

### 3. Schema Generation ⚙️
- Multi-pass LLM pipeline:
  - **Entities**: Identify main business objects
  - **Attributes**: Define properties and types
  - **Relationships**: Connect entities with cardinalities
  - **Validation**: Check consistency and completeness

### 4. Output Generation 📊
- JSON MER model
- Prisma schema (optional)
- Validation reports

## 🎯 Example Workflow

1. **Figma Wireframes**: Design screens like "Login", "User Profile", "Projects"
2. **AI Analysis**: 
   - "Inicio de Sesion" → User entity
   - "Proyectos" → Project entity  
   - "Crear cuenta" → User registration attributes
3. **Generated Schema**:
   - User(id, email, password, name)
   - Project(id, name, description, userId)
   - Relationship: User 1:N Project

## 🔍 Troubleshooting

### MCP Connection Issues
```bash
# Test Figma MCP connection
npm list -g figma-developer-mcp
```

### API Key Issues
- Verify OpenAI API key has sufficient credits
- Check Figma access token permissions
- Ensure file ID is correct and accessible

### Pipeline Errors
- Check `uv run python ai_to_schema.py` output for detailed logs
- Verify all environment variables are set
- Ensure sufficient OpenAI API quota

## 📝 License

MIT License - Feel free to use and modify!

---

**🚀 Ready to generate schemas from your Figma designs? Run `uv run python ai_to_schema.py` and watch the magic happen!**
