
import typer
from rich.console import Console
import json
import os
import re
import subprocess
import sys
import time
from llm_interface import query_ollama

# Model and console constants
PLANNER_MODEL = "mistral:7b-instruct"
EXECUTOR_MODEL = "deepseek-coder:6.7b"
CONSOLE = Console()
MAX_CORRECTION_ATTEMPTS = 3

# Typer application instance
app = typer.Typer()

def sanitize_json(plan_str: str) -> str:
    # Quick regex/replace sanitization before repair
    json_str = plan_str.strip().replace('"""', '"').replace("'''", '"')
    
    # Extract JSON substring only
    json_start_index = json_str.find('{')
    json_end_index = json_str.rfind('}') + 1
    if json_start_index == -1 or json_end_index == 0:
        return json_str
    return json_str[json_start_index:json_end_index]

def run_and_correct(run_cmd: list, target_file: str):
    # Runs the generated app, capture errors, and attempts to fix them
    for attempt in range(MAX_CORRECTION_ATTEMPTS):
        CONSOLE.print(f"\nAttempt {attempt + 1}/{MAX_CORRECTION_ATTEMPTS}: Running the app...")
        try:
            # Run the command and capture output
            result = subprocess.run(
                run_cmd,
                check=True,
                text=True,
                capture_output=True,
                timeout=15
            )
            CONSOLE.print("App ran successfully without errors!")
            CONSOLE.print(f"Output:\n{result.stdout}")
            return True # exit the loop

        except subprocess.CalledProcessError as e:
            error_output = e.stderr
            CONSOLE.print(f"App failed to run. Error detected!")
            CONSOLE.print(f"Error:\n{error_output}")

            if attempt < MAX_CORRECTION_ATTEMPTS - 1:
                CONSOLE.print(f"Attempting self-correction for {target_file}...")
                try:
                    with open(target_file, "r", encoding="utf-8") as f:
                        original_code = f.read()

                    fixer_prompt = f"""You are an expert programmer AI.
The following Python code in the file '{target_file}' failed to run.
Analyze the error message and the code, and provide a corrected version.

--- ERROR MESSAGE ---
{error_output}
--- END ERROR MESSAGE ---

--- ORIGINAL CODE ---
{original_code}
--- END ORIGINAL CODE ---

Your response must ONLY be the raw, corrected Python code for the file.
Do not include explanations, markdown, or anything else.
"""
                    with CONSOLE.status(f"Generating fix for {target_file}...", spinner="dots"):
                        corrected_code = query_ollama(EXECUTOR_MODEL, fixer_prompt)

                    if corrected_code:
                         # Clean up potential markdown fences
                        if "```" in corrected_code:
                            code_start = corrected_code.find("```") + 3
                            code_end = corrected_code.rfind("```")
                            if "generated_code" in locals() and generated_code[code_start:].lstrip().startswith("python"):
                                code_start = corrected_code.find("\n", code_start) + 1
                            corrected_code = corrected_code[code_start:code_end].strip()

                        with open(target_file, "w", encoding="utf-8") as f:
                            f.write(corrected_code)
                        CONSOLE.print(f"Fix applied to {target_file}. Retrying...")
                        time.sleep(2) #pause before retrying
                    else:
                        CONSOLE.print("Failed to generate a fix. Aborting.")
                        return False

                except Exception as file_e:
                    CONSOLE.print(f"Error during file operation for correction: {file_e}")
                    return False
        except subprocess.TimeoutExpired:
            CONSOLE.print("App run timed out. Assuming it's a running server, marking as success.")
            return True # For web servers that run indefinitely
        except Exception as general_e:
            CONSOLE.print(f"An unexpected error occurred: {general_e}")
            return False

    CONSOLE.print(f"Could not fix the app after {MAX_CORRECTION_ATTEMPTS} attempts.")
    return False


@app.command()
def new(project_prompt: str):
    # Creates a new project
    CONSOLE.print(f"Starting new project: '{project_prompt}'")

    # Planner step
    with CONSOLE.status("Thinking... Creating a multi-step plan...", spinner="dots"):
        planner_prompt = f"""
You are an expert software architect AI. Your job is to create a valid JSON execution plan to build a software project.

STRICT OUTPUT FORMAT:
You MUST return a JSON object with the following structure:
{{
  "projectName": "string (kebab-case)",
  "plan": [
    {{
      "type": "create_directory" | "generate_file" | "create_requirements_file",
      "path": "string (filename or folder)",
      "prompt": "string (instructions for code generation, required if type=generate_file)",
      "dependencies": ["array", "of", "filenames"]
    }}
  ]
}}

RULES:
- Do not output explanations, comments, or text outside the JSON.
- For multi-file projects, create a logical directory structure.
- "generate_file" steps MUST include a "path" and a "prompt".
- The "dependencies" in a "generate_file" step are other files the current file depends on, ensuring context is provided.

--- EXAMPLE ---
User request: "a flask api with a separate file for routes"
Your JSON response:
{{
  "projectName": "multi-file-flask-api",
  "plan": [
    {{
      "type": "create_requirements_file",
      "path": "requirements.txt",
      "dependencies": ["Flask"]
    }},
    {{
      "type": "create_directory",
      "path": "app"
    }},
    {{
      "type": "generate_file",
      "path": "app/routes.py",
      "prompt": "Create a Python file with a Flask Blueprint. Add one route '/hello' that returns a JSON object {{'message': 'hello from routes'}}."
    }},
    {{
      "type": "generate_file",
      "path": "app/__init__.py",
      "prompt": "Create a Flask application factory function called create_app. Import the blueprint from app.routes and register it with the app. The factory should return the app instance.",
      "dependencies": ["app/routes.py"]
    }},
    {{
      "type": "generate_file",
      "path": "run.py",
      "prompt": "Create a main entrypoint file. Import the create_app factory from the 'app' module, call it to create the app, and run it in debug mode.",
      "dependencies": ["app/__init__.py"]
    }}
  ]
}}
--- END EXAMPLE ---

User request: "{project_prompt}"
"""
        plan_str = query_ollama(PLANNER_MODEL, planner_prompt)
        if not plan_str:
            CONSOLE.print("Failed to get a plan from the Planner.")
            raise typer.Exit()

    # Clean and parse plan
    try:
        json_str = sanitize_json(plan_str)

        def escape_json_strings(match):
            content = match.group(1)
            safe = content.replace("\n", "\\n").replace("\r", "\\r")
            return f"\"{safe}\""

        json_str = re.sub(r'"([^"]*?)"', escape_json_strings, json_str, flags=re.DOTALL)
        plan = json.loads(json_str)

    except (ValueError, json.JSONDecodeError):
        CONSOLE.print("Planner JSON invalid, attempting auto-repair...")
        repair_prompt = f"""
You are a strict JSON formatter.
Take the following invalid JSON-like text and return ONLY valid JSON.
Do not include explanations, markdown, or extra text.

Text:
{plan_str}
"""
        repaired = query_ollama(PLANNER_MODEL, repair_prompt)
        repaired = sanitize_json(repaired)
        try:
            plan = json.loads(repaired)
        except (ValueError, json.JSONDecodeError) as e:
            CONSOLE.print(f"Planner JSON repair failed: {e}")
            CONSOLE.print(f"Raw response was:\n{plan_str}")
            raise typer.Exit()

    # Schema auto-repair
    fixed_plan = []
    for step in plan.get("plan", []):
        if not step.get("type"):
            if "prompt" in step:
                step["type"] = "generate_file"
            elif "dependencies" in step:
                step["type"] = "create_requirements_file"
            elif "path" in step:
                step["type"] = "create_directory"
            else:
                step["type"] = "unknown"
        fixed_plan.append(step)
    plan["plan"] = fixed_plan

    project_name = plan.get("projectName", "untitled-project")
    CONSOLE.print(f"Plan received for project '{project_name}'.")

    if not os.path.exists(project_name):
        os.makedirs(project_name)
    os.chdir(project_name)

    memory = {}

    # Orchestrator loop
    for i, step in enumerate(plan.get("plan", [])):
        step_type = step.get("type")
        step_description = step.get("description", f"Executing step type '{step_type}'")
        CONSOLE.print(f"-> Executing step {i+1}/{len(plan['plan'])}: {step_description}")

        if step_type == "create_directory":
            path = step.get("path", "subdir")
            try:
                os.makedirs(path, exist_ok=True)
                CONSOLE.print(f"Created directory: {path}")
            except OSError as e:
                CONSOLE.print(f"Error creating directory {path}: {e}")

        elif step_type == "generate_file":
            path = step.get("path", "app.py")
            prompt = step.get("prompt", "Create a minimal Flask app with a '/' route returning 'Hello, World!'")
            dependencies = step.get("dependencies", [])
            context_str = ""
            for dep in dependencies:
                if dep in memory:
                    context_str += f"Content of {dep}:\n{memory[dep]}\n\n"
            if len(context_str) > 20000:
                context_str = context_str[-20000:] + "\n... (context truncated)"
            with CONSOLE.status(f"Generating code for {path}...", spinner="dots"):
                code_prompt = f"""You are an expert programmer AI. Write only raw code.
Project overview: "{project_prompt}"
Task for this file: "{prompt}"
Existing files context:
{context_str}
Response MUST NOT include explanations, markdown, or backticks.
"""
                generated_code = query_ollama(EXECUTOR_MODEL, code_prompt)
                if not generated_code:
                    CONSOLE.print(f"Executor failed to generate code for {path}.")
                    continue

            if "```" in generated_code:
                code_start = generated_code.find("```") + 3
                code_end = generated_code.rfind("```")
                if generated_code[code_start:].lstrip().startswith(("python", "bash", "javascript", "html", "css")):
                    code_start = generated_code.find("\n", code_start) + 1
                generated_code = generated_code[code_start:code_end].strip()

            try:
                parent_dir = os.path.dirname(path)
                if parent_dir:
                    os.makedirs(parent_dir, exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(generated_code)
                CONSOLE.print(f"Wrote code to: {path}")
                memory[path] = generated_code
            except IOError as e:
                CONSOLE.print(f"Error writing file {path}: {e}")

        elif step_type == "create_requirements_file":
            dependencies = step.get("dependencies", ["flask==2.0.1"])
            try:
                with open("requirements.txt", "w", encoding="utf-8") as f:
                    f.write("\n".join(dependencies))
                CONSOLE.print(f"Created requirements.txt with {len(dependencies)} dependencies.")
            except IOError as e:
                CONSOLE.print(f"Error writing requirements.txt: {e}")
        else:
            CONSOLE.print(f"Unknown step type '{step_type}', skipping.")

    # Validation step
    CONSOLE.print("\nValidating generated project...")
    if os.path.exists("requirements.txt"):
        try:
            subprocess.run(["pip", "install", "-r", "requirements.txt"], check=True, text=True, capture_output=True)
            CONSOLE.print("Dependencies installed successfully.")
        except subprocess.CalledProcessError as e:
            CONSOLE.print(f"Dependency installation failed:\n{e.stderr}")
            os.chdir("..")
            raise typer.Exit()

    # Self-correction step
    run_cmd = None
    target_file = None
    if os.path.exists("app.py") or os.path.exists("main.py"):
        target_file = "app.py" if os.path.exists("app.py") else "main.py"
        with open(target_file, "r", encoding="utf-8") as f:
            code = f.read().lower()
            if "fastapi" in code:
                run_cmd = ["uvicorn", f"{target_file.replace('.py','')}:app", "--port", "8001", "--timeout-keep-alive", "5"]
            elif "flask" in code:
                run_cmd = ["flask", "--app", target_file, "run"]
            elif "streamlit" in code:
                run_cmd = ["streamlit", "run", target_file]
            else:
                run_cmd = ["python", target_file]

    if run_cmd and target_file:
        run_and_correct(run_cmd, target_file)

    # Auto-documentation step
    CONSOLE.print("\nGenerating README.md...")
    def build_tree(path, prefix=""):
        entries = []
        for name in sorted(os.listdir(path)):
            if name.startswith("."): continue
            full_path = os.path.join(path, name)
            if os.path.isdir(full_path):
                entries.append(f"{prefix}{name}/")
                entries.extend(build_tree(full_path, prefix + "   "))
            else:
                entries.append(f"{prefix}{name}")
        return entries
    file_tree = "\n".join(build_tree("."))
    dependencies = []
    if os.path.exists("requirements.txt"):
        with open("requirements.txt", "r", encoding="utf-8") as f:
            dependencies = [line.strip() for line in f if line.strip()]
    readme_content = (
        f"# {project_name}\n\n"
        "## Original Prompt\n"
        f"```\n{project_prompt}\n```\n\n"
        "## Dependencies\n"
        f"{', '.join(dependencies) if dependencies else 'None'}\n\n"
        "## Project Structure\n"
        f"```\n{file_tree}\n```\n"
    )
    try:
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(readme_content)
        CONSOLE.print("README.md generated successfully.")
    except IOError as e:
        CONSOLE.print(f"Error writing README.md: {e}")

    os.chdir("..")
    CONSOLE.print("\nProject scaffolding finished with a self-correction loop.")


def run_interactive_mode():
    # Runs the main interactive loop for DevAgent
    CONSOLE.print("\nWelcome to the DevAgent Interactive Console!")
    CONSOLE.print("Enter your project prompt below. Type 'exit' or 'quit' to close.")

    while True:
        try:
            prompt = CONSOLE.input("DevAgent > ")

            if prompt.lower() in ["exit", "quit"]:
                CONSOLE.print("Goodbye!")
                break

            if not prompt.strip():
                continue

            new(prompt)

            CONSOLE.print("\nProject generation finished. Ready for a new prompt.")

        except KeyboardInterrupt:
            CONSOLE.print("\nGoodbye!")
            break
        except Exception as e:
            CONSOLE.print(f"An unexpected error occurred: {e}")
            CONSOLE.print("Restarting the console...\n")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Non-interactive mode
        if sys.argv[1] == "new":
            if len(sys.argv) > 2:
                prompt = " ".join(sys.argv[2:])
                new(prompt)
            else:
                CONSOLE.print("Error: 'new' command requires a prompt.")
        else:
            # For backward compatibility with `python main.py "a prompt"`
            prompt = " ".join(sys.argv[1:])
            new(prompt)
    else:
        # Interactive mode
        run_interactive_mode()