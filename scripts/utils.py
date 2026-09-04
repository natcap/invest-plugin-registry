# /// script
# requires-python = ">=3.6"
# dependencies = [
# ]
# ///
import re
from urllib.parse import urlparse

PLUGIN_TYPES = {
    "preprocessing": "Preprocessing",
    "postprocessing": "Postprocessing",
    "workflow": "Workflow",
    "invest_model_variant": "InVEST Model Variant",
    "new_model": "New Model",
    "other": "Other"
}


def construct_base_url(git_url, version):
    # Sanitize for safety:
    git_url = git_url.strip()
    version = version.strip()

    normalized_url = re.sub(r'\.git$', '', git_url)
    parsed = urlparse(normalized_url)
    host = parsed.hostname or ''
    path_parts = parsed.path.strip('/').split('/')
    org, repo = path_parts[0], path_parts[1]

    if host == 'github.com':
        return f"https://raw.githubusercontent.com/{org}/{repo}/refs/tags/{version}/FILENAME"

    return f"https://{host}/api/v4/projects/{org}%2F{repo}/repository/files/FILENAME/raw?ref={version}"


def get_base_repo_url(git_repo):
    return re.sub(r'\.git$', '', git_repo).rstrip('/')


def get_issues_link(git_repo, pyproject_toml):
    repo_url = get_base_repo_url(git_repo)
    return pyproject_toml['project']['urls'].get(
        'Issues', f"{repo_url}/issues")


def get_docs_link(git_repo, pyproject_toml):
    repo_url = get_base_repo_url(git_repo)

    docs_link = pyproject_toml['project']['urls'].get(
            'Documentation', repo_url)
    if not docs_link.startswith('http'):
        # Assume it's a filepath relative to the root of the repo
        docs_link = f"{repo_url}/{docs_link.lstrip('/')}"
    return docs_link


def format_contact(contacts, include_name_and_email=False):
    contacts_list = []

    for contact in contacts:
        name = contact.get('name')
        email = contact.get('email')
        if not name and not email:
            pass
        if name and email and include_name_and_email:
            contacts_list.append(f"{name} ({email})")
        elif name:
            contacts_list.append(name)
        else:
            contacts_list.append(email)

    return contacts_list
