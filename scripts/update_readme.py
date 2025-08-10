import os
import re
import sys
import json
from urllib.request import Request, urlopen


GITHUB_API = "https://api.github.com"


def fetch_repo(owner: str, repo: str, token: str | None) -> dict:
    url = f"{GITHUB_API}/repos/{owner}/{repo}"
    req = Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    with urlopen(req) as resp:
        return json.load(resp)


def replace_between(mark_start: str, mark_end: str, new_text: str, content: str) -> str:
    pattern = re.compile(
        rf"(<!--\s*{re.escape(mark_start)}\s*-->)(.*?)(<!--\s*{re.escape(mark_end)}\s*-->)",
        re.DOTALL,
    )
    return pattern.sub(rf"\1{new_text}\3", content, count=1)


def update_readme(readme_path: str) -> bool:
    owner = os.getenv("GH_USERNAME") or os.getenv("GITHUB_REPOSITORY", ":").split(":")[0]
    if not owner:
        raise RuntimeError("GH_USERNAME not set")
    token = os.getenv("GITHUB_TOKEN")

    targets = [
        {
            "repo": "video_proctor",
            "name_start": "video_proctor_name:start",
            "name_end": "video_proctor_name:end",
            "desc_start": "video_proctor_desc:start",
            "desc_end": "video_proctor_desc:end",
        },
        {
            "repo": "Sustinlyze360",
            "name_start": "sustinlyze360_name:start",
            "name_end": "sustinlyze360_name:end",
            "desc_start": "sustinlyze360_desc:start",
            "desc_end": "sustinlyze360_desc:end",
        },
    ]

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    original = content

    for t in targets:
        try:
            data = fetch_repo(owner, t["repo"], token)
        except Exception as e:
            print(f"WARN: failed to fetch {t['repo']}: {e}")
            continue

        repo_name = data.get("name") or t["repo"]
        description = (data.get("description") or "").strip()
        if not description:
            description = ""

        content = replace_between(t["name_start"], t["name_end"], repo_name, content)
        if description:
            content = replace_between(t["desc_start"], t["desc_end"], description, content)

    changed = content != original
    if changed:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(content)
    return changed


def main() -> int:
    readme_path = os.path.join(os.getcwd(), "README.md")
    changed = update_readme(readme_path)
    print("README updated" if changed else "README already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


