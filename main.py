import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load config
with open("config.yml") as f:
    config = yaml.safe_load(f)

VAULT = Path(config["vault_path"])
PROVIDER = config.get("llm_provider", "gemini")

# Init the right client based on provider
if PROVIDER == "claude":
    import anthropic
    llm_client = anthropic.Anthropic(api_key=config["claude_api_key"])
    MODEL = config["claude_model"]
else:
    import google.generativeai as genai
    genai.configure(api_key=config["gemini_api_key"])
    MODEL = config["gemini_model"]
    llm_client = genai.GenerativeModel(MODEL)


def call_llm(prompt: str) -> str:
    """Single function to call whichever LLM is configured."""
    if PROVIDER == "claude":
        response = llm_client.messages.create(
            model=MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    else:
        response = llm_client.generate_content(prompt)
        return response.text


def log_path(project: str) -> Path:
    return VAULT / "projects" / project / "log.md"

def status_path(project: str) -> Path:
    return VAULT / "projects" / project / "status.md"


class EndSession(BaseModel):
    project: str
    worked_on: str
    status: str   # building | stalled | paused | done
    learned: str


@app.post("/end")
async def end_session(data: EndSession):
    project_dir = VAULT / "projects" / data.project
    project_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    log_entry = (
        f"\n## {today}\n"
        f"**Project:** {data.project}\n"
        f"**Status:** {data.status}\n"
        f"**Worked on:** {data.worked_on}\n"
        f"**Learned:** {data.learned}\n\n---\n"
    )

    with open(log_path(data.project), "a") as f:
        f.write(log_entry)

    with open(status_path(data.project), "w") as f:
        f.write(data.status)

    return {"ok": True, "project": data.project, "date": today}


@app.get("/status")
async def get_status():
    projects_dir = VAULT / "projects"
    results = []

    if projects_dir.exists():
        for d in sorted(projects_dir.iterdir()):
            if d.is_dir():
                name = d.name

                status = "unknown"
                s_path = status_path(name)
                if s_path.exists():
                    status = s_path.read_text().strip()

                last_session = "never"
                l_path = log_path(name)
                if l_path.exists():
                    for line in reversed(l_path.read_text().splitlines()):
                        if line.startswith("## "):
                            last_session = line.replace("## ", "").strip()
                            break

                results.append({"name": name, "status": status, "last_session": last_session})

    return {"projects": results}


@app.get("/start/{project}")
async def start_session(project: str):
    l_path = log_path(project)

    if not l_path.exists():
        context = "No previous sessions found. This is the first session."
    else:
        today = datetime.now()
        seven_days_ago = today - timedelta(days=7)

        entries = []
        current_entry = []
        in_range = False

        for line in l_path.read_text().splitlines(keepends=True):
            if line.startswith("## "):
                try:
                    entry_date = datetime.strptime(line.replace("## ", "").strip(), "%Y-%m-%d")
                    in_range = entry_date >= seven_days_ago
                    if in_range:
                        if current_entry:
                            entries.append("".join(current_entry))
                        current_entry = [line]
                    else:
                        current_entry = []
                except ValueError:
                    in_range = False
            elif in_range:
                current_entry.append(line)

        if current_entry:
            entries.append("".join(current_entry))

        context = "\n".join(entries) if entries else "No sessions in the last 7 days."

    prompt = f"""You are a builder's assistant. The user is starting a work session on project: {project}.

Here are their recent session logs:

{context}

Write a short, punchy session briefing (max 5 sentences):
1. What they last worked on
2. Where they left off
3. One concrete thing to focus on today

Be direct. No preamble. No "Here is your briefing:". Just the briefing."""

    try:
        briefing = call_llm(prompt)
    except Exception as e:
        briefing = f"Error getting briefing: {str(e)}"

    return {"project": project, "briefing": briefing}


class NewProject(BaseModel):
    name: str

@app.post("/project/new")
async def new_project(data: NewProject):
    name = data.name.strip().lower().replace(" ", "-")
    if not name:
        raise HTTPException(status_code=400, detail="Project name required")
    project_dir = VAULT / "projects" / name
    if project_dir.exists():
        raise HTTPException(status_code=409, detail="Project already exists")
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "log.md").touch()
    (project_dir / "status.md").write_text("building")
    return {"ok": True, "name": name}


class BacklogItem(BaseModel):
    idea: str

@app.post("/backlog")
async def add_backlog(item: BacklogItem):
    backlog_file = VAULT / "backlog.md"
    today = datetime.now().strftime("%Y-%m-%d")
    entry = f"- [{today}] {item.idea}\n"
    with open(backlog_file, "a") as f:
        f.write(entry)
    return {"ok": True}


@app.get("/backlog")
async def get_backlog():
    backlog_file = VAULT / "backlog.md"
    items = []
    if backlog_file.exists():
        for line in backlog_file.read_text().splitlines():
            if line.startswith("- "):
                items.append(line[2:].strip())
    return {"items": items}


class AskQuery(BaseModel):
    project: str
    question: str

@app.post("/ask")
async def ask(query: AskQuery):
    l_path = log_path(query.project)
    if not l_path.exists():
        return {"answer": "No session logs found for this project yet."}

    log_content = l_path.read_text().strip()
    if not log_content:
        return {"answer": "No session logs found for this project yet."}

    prompt = f"""You are a helpful assistant with access to a developer's session logs for project: {query.project}.

Here are all their session logs:

{log_content}

Answer this question based only on what is in the logs:
{query.question}

Be concise and direct. If the answer isn't in the logs, say so plainly."""

    try:
        answer = call_llm(prompt)
    except Exception as e:
        answer = f"Error: {str(e)}"

    return {"answer": answer}


@app.get("/")
def root():
    return FileResponse("index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8100, reload=True)
