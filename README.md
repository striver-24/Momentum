# Momentum - Flow-State Engineering Agent 🚀

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/striver-24/Momentum)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An autonomous software development agent that transforms high-level business requirements into production-ready code through automated development loops.

## 🎯 Overview

Momentum is designed to radically accelerate software development by automating the entire inner development loop. Simply provide natural language requirements, and receive fully tested, documented, and production-ready code in the form of a pull request.

### Key Features

- **Natural Language Input**: Submit requirements in plain English
- **Autonomous Development**: Complete feature implementation from planning to PR
- **AI-Powered Quality Assurance**: Integrated CodeRabbitAI review process
- **Isolated Execution**: Docker-based containerization for safe code execution
- **Self-Correction**: Automatic bug fixing based on AI feedback
- **Vector Memory**: Long-term codebase understanding and consistency

## 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Orchestration   │───▶│   LLM Core      │
│   (CLI/Web)     │    │     Engine       │    │ (Llama/Cerebras)│
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Vector Database │    │    Execution     │    │  Code Quality   │
│ (ChromaDB/Pine) │    │ Environment      │    │ & Verification  │
│                 │    │   (Docker MCP)   │    │ (CodeRabbitAI)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

- **Orchestration**: Python 3.10+, LangChain/LangGraph, FastAPI
- **LLM & Compute**: Meta Llama 3 on Cerebras Cloud
- **Containerization**: Docker / Mirantis Container Platform (MCP)
- **Code Review**: CodeRabbitAI + GitHub integration
- **Version Control**: Git (GitHub/GitLab)
- **Vector Database**: ChromaDB (local) / Pinecone (cloud)
- **Frontend**: Next.js (optional web interface)

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Docker Desktop
- Git
- GitHub account with CodeRabbitAI app installed

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/striver-24/Momentum.git
   cd Momentum
   ```
2. **Set up the backend**

   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Set up the frontend (optional)**

   ```bash
   cd apps/frontend
   npm install
   ```
4. **Configure environment variables**

   ```bash
   cp backend/.env.example backend/.env
   # Edit .env with your API keys and configuration
   ```

### Environment Configuration

Create a `.env` file in the `backend` directory with:

```env
# Cerebras Cloud API
CEREBRAS_API_KEY=your_cerebras_api_key
CEREBRAS_MODEL=llama3-70b

# GitHub Configuration
GITHUB_TOKEN=your_github_token
GITHUB_REPO_OWNER=your_username
GITHUB_REPO_NAME=your_repo

# CodeRabbitAI
CODERABBITAI_WEBHOOK_SECRET=your_webhook_secret

# Vector Database
VECTOR_DB_TYPE=chromadb  # or pinecone
PINECONE_API_KEY=your_pinecone_key  # if using Pinecone

# Docker MCP
DOCKER_HOST=unix:///var/run/docker.sock
```

## 📖 Usage

### Command Line Interface

```bash
# Start the orchestration engine
python backend/main.py

# Submit a feature request
python -m src.agent.orchestrator --request "Create a user authentication system with JWT tokens"

# Monitor progress
python -m src.agent.orchestrator --status

# List completed features
python -m src.agent.orchestrator --list
```

### Web Interface (Optional)

```bash
# Start the frontend
cd apps/frontend
npm run dev

# Open browser to http://localhost:3000
```

## 🔄 Development Workflow

### 1. Requirement Submission

```
"Implement a feature to allow users to reset their password. 
It needs an API endpoint that takes an email, generates a unique token, 
saves it to the database with an expiry, and sends a reset link."
```

### 2. Automated Process

1. **Planning**: LLM breaks down the requirement into tasks
2. **Code Generation**: Creates implementation in isolated Docker container
3. **Testing**: Generates and runs comprehensive tests
4. **Documentation**: Auto-generates API docs and comments
5. **PR Creation**: Commits to feature branch and opens pull request
6. **AI Review**: CodeRabbitAI performs automated code review
7. **Self-Correction**: Fixes issues based on review feedback
8. **Final Approval**: Ready for human review and merge

### 3. Quality Assurance

- Automated testing (unit, integration, e2e)
- Code style and formatting checks
- Security vulnerability scanning
- Performance optimization suggestions
- Documentation completeness validation

## 📁 Project Structure

```
Momentum/
├── backend/                 # Python orchestration engine
│   ├── src/
│   │   ├── agent/          # Core agent logic
│   │   │   └── orchestrator.py
│   │   ├── api/            # FastAPI endpoints
│   │   └── connectors/     # External service integrations
│   │       └── llm_connector.py
│   ├── main.py             # Application entry point
│   └── requirements.txt    # Python dependencies
├── apps/
│   └── frontend/           # Next.js web interface (optional)
│       ├── app/
│       │   └── page.tsx
│       └── package.json
├── .gitignore
└── README.md
```

## 🧩 Core Components

### Orchestration Engine

The central brain that manages the entire development workflow, from task decomposition to final PR creation.

### LLM Connector

Handles all communication with Meta Llama models running on Cerebras Cloud infrastructure for maximum performance.

### Docker MCP Integration

Provides isolated execution environments for safe code generation, testing, and validation.

### Vector Database

Maintains long-term memory of codebase patterns, architectural decisions, and development history.

### CodeRabbitAI Integration

Automated code review system that catches bugs, enforces best practices, and prevents AI hallucinations.

## 🎛️ Configuration

### Agent Behavior

Customize the agent's behavior through configuration files:

```python
# backend/config/agent_config.py
AGENT_CONFIG = {
    "max_iterations": 5,
    "test_coverage_threshold": 80,
    "code_review_strictness": "high",
    "auto_merge_approved": False,
    "documentation_level": "comprehensive"
}
```

### LLM Parameters

```python
# backend/config/llm_config.py
LLM_CONFIG = {
    "model": "llama3-70b",
    "temperature": 0.1,
    "max_tokens": 4096,
    "context_window": 32768
}
```

## 🔌 API Reference

### REST Endpoints

#### Submit Feature Request

```http
POST /api/v1/features
Content-Type: application/json

{
  "description": "Feature description in natural language",
  "priority": "high|medium|low",
  "target_branch": "main"
}
```

#### Get Feature Status

```http
GET /api/v1/features/{feature_id}/status
```

#### List Features

```http
GET /api/v1/features?status=pending|in_progress|completed|failed
```

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
python -m pytest tests/ -v --coverage
```

### Run Frontend Tests

```bash
cd apps/frontend
npm test
```

### Integration Tests

```bash
# Run full end-to-end tests
python -m pytest tests/integration/ -v
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d
```

### Cloud Deployment

```bash
# Deploy to your preferred cloud provider
# Configuration files provided for AWS, GCP, Azure
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `npm test` or `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📋 Roadmap

### Phase 1: Foundation ✅

- [X] Basic orchestration engine
- [X] LLM integration with Cerebras
- [X] Docker MCP setup
- [X] GitHub integration

### Phase 2: Core Features 🚧

- [ ] Vector database integration
- [ ] Advanced prompt engineering
- [ ] CodeRabbitAI review loop
- [ ] Self-correction mechanisms

### Phase 3: Enhanced Capabilities 📋

- [ ] Multi-language support
- [ ] Advanced testing strategies
- [ ] Performance optimization
- [ ] Security scanning integration

### Phase 4: User Experience 📋

- [ ] Web interface
- [ ] Real-time progress tracking
- [ ] Advanced configuration options
- [ ] Team collaboration features

## 🐛 Troubleshooting

### Common Issues

#### Docker Connection Issues

```bash
# Check Docker daemon status
docker info

# Restart Docker Desktop
# On macOS: restart Docker Desktop app
# On Linux: sudo systemctl restart docker
```

#### API Key Configuration

```bash
# Verify environment variables
python -c "import os; print('CEREBRAS_API_KEY' in os.environ)"
```

#### GitHub Integration

```bash
# Test GitHub token permissions
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Meta AI for the Llama language model
- Cerebras Systems for high-performance AI infrastructure
- CodeRabbitAI for automated code review capabilities
- The open-source community for foundational tools and libraries

## 📞 Support

- **Documentation**: [Wiki](https://github.com/striver-24/Momentum/wiki)
- **Issues**: [GitHub Issues](https://github.com/striver-24/Momentum/issues)
- **Discussions**: [GitHub Discussions](https://github.com/striver-24/Momentum/discussions)
- **Email**: support@momentum-agent.dev

---

**Built with ❤️ by Deivyansh Singh**
