# DevAgent

DevAgent is my personal experiment in building a **local-first AI agent** that can scaffold entire software projects from a natural language prompt.

Instead of relying on cloud APIs, DevAgent uses **local LLMs via [Ollama](https://ollama.ai/)** to plan and generate code, giving me **privacy, control, and hackability**.  
It’s not perfect (yet), but it’s already at a stage where it can take a single command like:

```bash
python main.py new "build a simple FastAPI app with a single endpoint"
```

…and produce a runnable project folder with files, dependencies, and a basic README.

Current Capabilities (as of this version)  
**Planner/Executor Architecture**

- Planner model (`mistral:7b-instruct`) generates a JSON project plan.
- Executor model (`deepseek-coder:6.7b`) writes the actual code.

**Self-Correction Loop**

- After generation, DevAgent tries to run the app.
- If it fails, it automatically asks the LLM to fix the code (up to 3 attempts).

**Contextual Awareness**

- Each file generation step can include the contents of its dependencies, so code is more consistent across files.

**Dependency Handling**

- Creates a `requirements.txt` file and installs dependencies automatically.

**Auto-Generated README**

- Each project comes with a README that includes the original prompt, dependency list, and file tree.

**Interactive Mode**

- Run `python main.py` with no arguments to enter a loop where you can type multiple prompts one after another.

**How It Works**  
Workflow at a high level:

```
[Prompt via CLI] → [Planner LLM → JSON Plan] → [Orchestrator Loop]
  → [Executor LLM → Generate Code] → [Filesystem]
  → [Validation + Self-Correction] → [Final Project + Auto-README]
```

**Repo Structure**  
Currently, the core logic is split into:

- `main.py` — Orchestrator, CLI, planning, execution, correction, auto-docs.
- `llm_interface.py` — Minimal wrapper to query Ollama locally.

**Usage**

**Prerequisites**

- Python 3.10+
- Ollama installed and running
- Models:

```bash
ollama pull mistral:7b-instruct
ollama pull deepseek-coder:6.7b
```

**Setup**

```bash
git clone https://github.com/gautam-chitti/DevAgent
cd devagent
python -m venv .venv
source .venv/bin/activate    # (on Linux/Mac)
.venv\Scripts\activate       # (on Windows)
pip install -r requirements.txt
```

**Run**

```bash
# Non-interactive
python main.py new "build a flask app with a /hello endpoint"

# Interactive loop
python main.py
```

**Limitations / Known Issues**

Being honest about the current state:

- Generated projects are hit-or-miss: sometimes they run perfectly, other times they need manual fixes.
- The self-correction loop works for simple issues, but isn’t bulletproof.
- Larger/more complex prompts may overwhelm context or produce incomplete scaffolds.
- Currently limited to Python-based projects (Flask, FastAPI, Streamlit tested).

**Roadmap**

What I want to explore next:

- Better Memory: giving the Executor richer context across files.
- Improved Documentation: richer auto-generated READMEs.
- Smarter Self-Healing: multiple strategies for debugging, not just retry.
- Extending beyond Python: try simple Node.js or frontend scaffolds.

**Why I Built This**

I wanted a local-first, transparent AI junior developer that I could fully control and learn from — not a closed black-box.  
This repo is a work-in-progress and an educational project, not a production tool.

Feedback, ideas, and PRs are welcome!
