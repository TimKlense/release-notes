import os
import subprocess
import openai
from github import Github

# Set up API keys
openai.api_key = os.getenv("OPENAI_API_KEY")
github = Github(os.getenv("GITHUB_TOKEN"))

def get_changed_files(base: str, head: str):
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{head}"],
        capture_output=True, text=True
    )
    files = result.stdout.strip().split("\n")
    return [f for f in files if f.endswith(('.tsx', '.jsx', '.html', '.css'))]

def get_file_diffs(base: str, head: str, files: list[str]) -> str:
    if not files:
        return ""
    diff_cmd = ["git", "diff", f"{base}...{head}", "--"] + files
    result = subprocess.run(diff_cmd, capture_output=True, text=True)
    return result.stdout

def generate_cypress_test(diff: str) -> str:
    prompt = f"""
You are an expert QA engineer. Based on the following UI-related code diff, write a Cypress test that validates the visual or interactive behavior described in the change.

Respond with only the test code, no explanation.

```diff
{diff}
```
"""
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def comment_on_pr(repo_full_name: str, pr_number: int, test_code: str):
    repo = github.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    comment_body = f"""🧪 **Suggested Cypress Test**

```javascript
{test_code}
```"""
    pr.create_issue_comment(comment_body)

def main():
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_ref = os.getenv("GITHUB_REF")
    pr_number = int(pr_ref.split("/")[-1])
    base = os.getenv("GITHUB_BASE_REF")
    head = os.getenv("GITHUB_HEAD_REF")

    print(f"Comparing branches: {base}...{head}")
    changed_files = get_changed_files(base, head)

    if not changed_files:
        print("✅ No relevant UI-related files changed.")
        return

    print(f"Found UI-related files: {changed_files}")
    diff = get_file_diffs(base, head, changed_files)

    if not diff:
        print("⚠️ No diff found for UI-related files.")
        return

    print("Generating Cypress test from diff...")
    test_code = generate_cypress_test(diff)

    print("Commenting on PR with suggested test...")
    comment_on_pr(repo_name, pr_number, test_code)

if __name__ == "__main__":
    main()
