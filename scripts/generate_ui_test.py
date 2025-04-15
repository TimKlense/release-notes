import os
import subprocess
import openai
from github import Github

openai.api_key = os.getenv("OPENAI_API_KEY")
g = Github(os.getenv("GITHUB_TOKEN"))

def get_changed_files(base: str, head: str):
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True, text=True
    )
    files = result.stdout.strip().split("\n")
    return [f for f in files if f.endswith(('.tsx', '.jsx', '.html', '.css'))]

def get_file_diffs(base: str, head: str, files: list):
    diff_cmd = ["git", "diff", f"{base}...{head}", "--"] + files
    result = subprocess.run(diff_cmd, capture_output=True, text=True)
    return result.stdout

def generate_cypress_test(diff: str) -> str:
    prompt = f"""
You are an expert QA engineer. Based on the following UI-related code diff, write a Cypress test that validates the visual or interactive behavior described in the change.

Respond with only the code.

```diff
{diff}
