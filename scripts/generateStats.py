import requests
import subprocess
import os
import tempfile
import json

GITHUB_ORG = "RPA-TJ-Lille"
HEADERS = {"Accept": "application/vnd.github+json"}

def get_repos():
    url = f"https://api.github.com/orgs/{GITHUB_ORG}/repos?per_page=100&type=public"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def get_contributors(repo):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo}/contributors"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    return [contrib["login"] for contrib in response.json()]

def get_downloads(repo):
    url = f"https://api.github.com/repos/{GITHUB_ORG}/{repo}/releases"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return 0
    downloads = 0
    for release in response.json():
        for asset in release.get("assets", []):
            downloads += asset.get("download_count", 0)
    return downloads

def count_lines_of_code(repo_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "clone", repo_url], cwd=tmpdir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        repo_name = repo_url.split("/")[-1]
        result = subprocess.run(["cloc", repo_name, "--json"], cwd=tmpdir, capture_output=True, text=True)
        try:
            data = json.loads(result.stdout)
            return data.get("Python", {}).get("code", 0)
        except json.JSONDecodeError:
            return 0

def inject_stats_in_readme(html_block):
    readme_path = "profile/README.md"
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_tag = "<!-- STATS_START -->"
    end_tag = "<!-- STATS_END -->"

    if start_tag in content and end_tag in content:
        before = content.split(start_tag)[0] + start_tag + "\n"
        after = "\n" + end_tag + content.split(end_tag)[1]
        new_content = before + html_block + after

        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("✅ Statistiques injectées dans README.md")
    else:
        print("⚠️ Balises STATS_START / STATS_END non trouvées dans README.md")

def main():
    print("🔄 Récupération des dépôts...")
    repos = get_repos()

    total_lines = 0
    total_downloads = 0
    all_contributors = set()

    for repo in repos:
        name = repo["name"]
        print(f"📦 {name}")

        repo_url = repo["clone_url"]
        lines = count_lines_of_code(repo_url)
        downloads = get_downloads(name)
        contributors = get_contributors(name)

        total_lines += lines
        total_downloads += downloads
        all_contributors.update(contributors)

    html_stats = f"""
<table>
<tr><td>🔢 Nombre total de projets</td><td><strong>{len(repos)}</strong></td></tr>
<tr><td>💻 Lignes de code cumulées</td><td><strong>{total_lines}</strong></td></tr>
<tr><td>📂 Dépôts GitHub publics</td><td><strong>{len(repos)}</strong></td></tr>
<tr><td>👨‍💻 Contributeurs uniques</td><td><strong>{len(all_contributors)}</strong></td></tr>
<tr><td>📥 Téléchargements totaux</td><td><strong>{total_downloads}</strong></td></tr>
</table>
""".strip()

    inject_stats_in_readme(html_stats)

if __name__ == "__main__":
    main()
