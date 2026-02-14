# DevOps Agent - Concept Design

Automatizovaný agent pro deployment, monitoring a infrastructure management.

---

## Co by dělal?

### 1. Deployment Automation
```
User: "Deploy latest version to staging"

Agent:
1. Checks: Tests passing? Migrations ready?
2. Creates: Backup of production DB
3. Runs: Alembic migrations on staging
4. Deploys: Latest code to Railway staging
5. Verifies: Health checks pass
6. Reports: "Deployed v1.2.3 to staging ✓"
```

### 2. Error Triage
```
User: "Production has errors, what's wrong?"

Agent:
1. Fetches: Last 100 errors from error_logs table
2. Analyzes: Common patterns, stack traces
3. Identifies: "90% errors are from /api/backtest - DB timeout"
4. Suggests: "Increase connection pool size or add index"
5. Can fix: Creates PR with suggested changes
```

### 3. CI/CD Management
```
User: "Setup CI/CD for this project"

Agent:
1. Creates: .github/workflows/test.yml
2. Configures: Test matrix (Python 3.11, 3.12)
3. Adds: Deployment workflow to Railway
4. Sets: Environment secrets
5. Tests: Triggers test run
6. Reports: "CI/CD ready - see badge in README"
```

### 4. Infrastructure Monitoring
```
Agent (proactive):
"⚠️ Database at 85% capacity - suggest scaling or cleanup"
"✓ API response time: 150ms avg (good)"
"⚠️ 3 failed deployments last week - investigate?"
```

---

## Technická Implementace

### Možnost 1: MCP Server (doporučuji)

**Struktura:**
```
agent/
├── devops_mcp_server.py     # MCP server
├── tools/
│   ├── github_tools.py       # GitHub API wrapper
│   ├── railway_tools.py      # Railway deployment
│   ├── database_tools.py     # DB migrations, backups
│   ├── monitoring_tools.py   # Sentry, logs
│   └── ci_tools.py           # CI/CD automation
└── skills/
    ├── deploy.py             # Deployment workflows
    ├── rollback.py           # Rollback procedures
    └── triage.py             # Error analysis
```

**MCP Server:**
```python
# agent/devops_mcp_server.py
from anthropic import Anthropic
from mcp.server import Server
from tools import github_tools, railway_tools

server = Server("devops-agent")

@server.tool()
async def deploy_to_staging(
    version: str,
    run_migrations: bool = True
) -> dict:
    """Deploy specific version to staging environment."""
    # 1. Run tests
    test_result = await github_tools.trigger_workflow("test")
    if not test_result.success:
        return {"error": "Tests failed, abort deployment"}

    # 2. Backup DB
    backup_id = await railway_tools.backup_database("staging")

    # 3. Run migrations
    if run_migrations:
        await railway_tools.run_command("alembic upgrade head")

    # 4. Deploy
    deploy_result = await railway_tools.deploy(
        environment="staging",
        version=version
    )

    return {
        "success": True,
        "version": version,
        "backup_id": backup_id,
        "url": deploy_result.url
    }

@server.tool()
async def analyze_errors(
    timeframe: str = "24h"
) -> dict:
    """Analyze recent production errors."""
    # Fetch from error_logs table
    errors = await database.query("""
        SELECT error_type, error_message, COUNT(*) as count
        FROM error_logs
        WHERE created_at > NOW() - INTERVAL %s
        GROUP BY error_type, error_message
        ORDER BY count DESC
        LIMIT 10
    """, (timeframe,))

    # Use Claude to analyze patterns
    client = Anthropic()
    analysis = client.messages.create(
        model="claude-sonnet-4",
        messages=[{
            "role": "user",
            "content": f"Analyze these errors and suggest fixes:\n{errors}"
        }]
    )

    return {
        "errors": errors,
        "analysis": analysis.content[0].text,
        "recommendations": extract_recommendations(analysis)
    }
```

**Usage v Claude Code:**
```python
# Claude Code CLI
> /devops deploy to staging

# Agent používá MCP tools
→ Checking tests... ✓
→ Creating backup... ✓
→ Running migrations... ✓
→ Deploying... ✓

Deployed v1.2.3 to staging:
https://staging.railway.app
Backup ID: backup_20240214_235900
```

---

### Možnost 2: Standalone Agent

**Struktura:**
```python
# agent/devops_agent.py
from anthropic import Anthropic
from typing import List, Dict

class DevOpsAgent:
    """AI-powered DevOps automation agent."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)
        self.tools = self._load_tools()

    def _load_tools(self) -> List[Dict]:
        """Load available tools for the agent."""
        return [
            {
                "name": "deploy",
                "description": "Deploy to environment",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "environment": {"type": "string"},
                        "version": {"type": "string"}
                    }
                }
            },
            {
                "name": "rollback",
                "description": "Rollback to previous version",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "environment": {"type": "string"},
                        "backup_id": {"type": "string"}
                    }
                }
            },
            # ... more tools
        ]

    async def chat(self, message: str) -> str:
        """Chat with the agent."""
        response = self.client.messages.create(
            model="claude-sonnet-4",
            messages=[{"role": "user", "content": message}],
            tools=self.tools,
            max_tokens=4096
        )

        # Handle tool calls
        while response.stop_reason == "tool_use":
            tool_results = await self._execute_tools(response.content)
            response = self.client.messages.create(
                model="claude-sonnet-4",
                messages=[
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response.content},
                    {"role": "user", "content": tool_results}
                ],
                tools=self.tools
            )

        return response.content[0].text

    async def _execute_tools(self, content: List) -> List[Dict]:
        """Execute tool calls from Claude."""
        results = []
        for block in content:
            if block.type == "tool_use":
                result = await self._execute_tool(
                    block.name,
                    block.input
                )
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result
                })
        return results

    async def _execute_tool(self, name: str, input: Dict) -> str:
        """Execute a specific tool."""
        if name == "deploy":
            return await self._deploy(**input)
        elif name == "rollback":
            return await self._rollback(**input)
        # ... other tools

    async def _deploy(self, environment: str, version: str) -> str:
        """Execute deployment."""
        # Implementation
        pass
```

**Usage:**
```python
# CLI
from agent.devops_agent import DevOpsAgent

agent = DevOpsAgent(api_key=os.getenv("ANTHROPIC_API_KEY"))

async def main():
    response = await agent.chat("Deploy latest version to staging")
    print(response)

# Output:
# I'll deploy the latest version to staging. Let me:
# 1. Check tests... ✓ All passing
# 2. Create backup... ✓ backup_20240214
# 3. Run migrations... ✓ 2 migrations applied
# 4. Deploy... ✓ Deployed v1.2.3
#
# Staging URL: https://staging.railway.app
# Rollback ID: backup_20240214
```

---

## Rozšiřitelnost (Dynamic Skills)

### Plugin System

```python
# agent/skills/base.py
class DevOpsSkill:
    """Base class for DevOps skills."""

    name: str
    description: str

    def get_tools(self) -> List[Dict]:
        """Return MCP tools for this skill."""
        raise NotImplementedError

    async def execute(self, action: str, **kwargs):
        """Execute skill action."""
        raise NotImplementedError

# agent/skills/docker_skill.py
class DockerSkill(DevOpsSkill):
    name = "docker"
    description = "Docker container management"

    def get_tools(self):
        return [
            {
                "name": "docker_build",
                "description": "Build Docker image",
                "input_schema": {...}
            },
            {
                "name": "docker_push",
                "description": "Push image to registry",
                "input_schema": {...}
            }
        ]

    async def execute(self, action: str, **kwargs):
        if action == "docker_build":
            # Build image
            pass

# agent/devops_agent.py
class DevOpsAgent:
    def __init__(self):
        self.skills = []

    def register_skill(self, skill: DevOpsSkill):
        """Dynamically add new skill."""
        self.skills.append(skill)
        self.tools.extend(skill.get_tools())

# Usage
agent = DevOpsAgent()
agent.register_skill(DockerSkill())
agent.register_skill(KubernetesSkill())  # Add more skills
```

---

## Cost Management (Claude Subscription)

### Použití Claude API (ne Claude Code)

```python
# Cost-effective prompt design
class DevOpsAgent:
    def __init__(self):
        self.client = Anthropic()
        # Cache system prompt
        self.system_prompt = """
You are a DevOps automation agent. You manage:
- Deployments (Railway, Render)
- CI/CD (GitHub Actions)
- Database migrations (Alembic)
- Error monitoring (Sentry)

Be concise and action-oriented.
"""

    async def chat(self, message: str):
        response = self.client.messages.create(
            model="claude-sonnet-4",  # or haiku for simple tasks
            system=self.system_prompt,
            messages=[{"role": "user", "content": message}],
            tools=self.tools,
            max_tokens=2048  # Limit output
        )
```

**Cost optimization:**
- Use **Haiku** for simple tasks (cheaper)
- Use **Sonnet** for complex analysis
- Cache system prompts
- Limit max_tokens

**Pricing (2024):**
- Haiku: $0.25 / 1M input tokens
- Sonnet: $3 / 1M input tokens

Deployment task: ~1000 tokens = $0.003 (Sonnet)

---

## Integration s tvým projektem

### Fáze 1: Basic Agent
```python
# agent/devops_agent.py
class DevOpsAgent:
    """Simple DevOps automation."""

    async def deploy_to_railway(self, environment: str):
        """Deploy to Railway."""
        subprocess.run(["railway", "up", "-e", environment])

    async def run_migrations(self):
        """Run Alembic migrations."""
        subprocess.run(["alembic", "upgrade", "head"])

# CLI
python -m agent.devops_agent deploy staging
```

### Fáze 2: AI-Powered
```python
# Add Claude for decision making
class DevOpsAgent:
    async def smart_deploy(self, message: str):
        # Claude decides what to do
        response = self.client.messages.create(
            model="claude-sonnet-4",
            messages=[{
                "role": "user",
                "content": f"Deployment request: {message}"
            }],
            tools=[deploy_tool, rollback_tool, ...]
        )
```

### Fáze 3: Autonomous
```python
# Proactive monitoring
class DevOpsAgent:
    async def monitor_loop(self):
        while True:
            # Check health
            errors = await self.get_recent_errors()
            if len(errors) > threshold:
                # Agent automatically triages
                analysis = await self.analyze_errors(errors)
                await self.notify_user(analysis)

            await asyncio.sleep(300)  # 5 min
```

---

## Konkrétní příklad

### User Story
```
User: "Production API is slow, fix it"

Agent workflow:
1. Fetch metrics from Railway
2. Query error_logs table
3. Analyze with Claude:
   "80% requests to /backtest timeout after 30s"
   "Root cause: Missing index on candles(symbol, timeframe)"

4. Create fix:
   - alembic revision -m "add index"
   - Write migration

5. Test on staging:
   - Deploy migration
   - Run load test
   - Verify improvement

6. Ask user: "Fix ready. Deploy to production?"

7. On approval:
   - Backup DB
   - Run migration
   - Monitor metrics

8. Report: "Fixed! API latency 30s → 200ms"
```

---

## Implementační plán

### Měsíc 1: Foundation
- [ ] Basic MCP server structure
- [ ] GitHub API integration
- [ ] Railway deployment tools
- [ ] Simple CLI

### Měsíc 2: Intelligence
- [ ] Claude integration
- [ ] Error analysis
- [ ] Smart deployment decisions
- [ ] Rollback automation

### Měsíc 3: Autonomy
- [ ] Proactive monitoring
- [ ] Auto-fix simple errors
- [ ] Performance optimization
- [ ] Cost tracking

---

## Závěr

**DevOps Agent by byl:**
- 🤖 **Autonomní** - rozhoduje se sám
- 🔧 **Rozšiřitelný** - plugin system
- 💰 **Cost-effective** - Claude API subscription
- 🚀 **Proaktivní** - monitoring + auto-fix

**První krok:**
Začít s jednoduchým MCP serverem pro deployment a postupně přidávat inteligenci.

**Chceš to implementovat?**
