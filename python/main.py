import logging
import shutil
import socket
import sys
import time
from datetime import datetime
from pathlib import Path

import jwt
from dotenv import load_dotenv
from git import Repo
from os import getenv
from requests import post, get

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

load_dotenv()
our_client_id = getenv("SPOTIFY_CLIENT_ID")
our_client_secret = getenv("SPOTIFY_CLIENT_SECRET")
github_app_id = getenv("GITHUB_APP_ID")
github_app_private_key = getenv("GITHUB_APP_PRIVATE_KEY")
git_user_name = getenv("GIT_USER_NAME", "evoteum-bot")
git_user_email = getenv("GIT_USER_EMAIL", "evoteum-bot@evoteum.com")
site_repo_owner = "evoteum"
site_repo_name = "itsbeginningtolookalotlikechristmas"
site_repo_https = f"https://github.com/{site_repo_owner}/{site_repo_name}.git"
data_file_relative = Path("site") / "data.csv"
this_song_id = "2pXpURmn6zC5ZYDMms6fwa"
workspace = Path("workspace")
REQUEST_TIMEOUT = 30


def check_github_reachable():
    log.info("Attempting to reach github.com:443 via TCP")
    try:
        with socket.create_connection(("github.com", 443), timeout=10) as sock:
            log.info("github.com:443 reachable")
    except Exception as e:
        log.error("Failed to reach github.com:443: %s", e)
        raise


def get_github_app_token(app_id, private_key_pem):
    log.info("Attempting to generate GitHub App JWT (app_id=%s)", app_id)
    try:
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}
        jwt_token = jwt.encode(payload, private_key_pem, algorithm="RS256")
        log.info("JWT generated")
    except Exception as e:
        log.error("Failed to generate GitHub App JWT: %s", e)
        raise

    log.info("Attempting to get installation ID for %s/%s", site_repo_owner, site_repo_name)
    try:
        response = get(
            f"https://api.github.com/repos/{site_repo_owner}/{site_repo_name}/installation",
            headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
            timeout=REQUEST_TIMEOUT,
        )
        log.info("Installation lookup status: %d", response.status_code)
        response.raise_for_status()
        installation_id = response.json()["id"]
        log.info("Installation ID: %s", installation_id)
    except Exception as e:
        log.error("Failed to get installation ID: %s", e)
        raise

    log.info("Attempting to get installation access token")
    try:
        response = post(
            f"https://api.github.com/app/installations/{installation_id}/access_tokens",
            headers={"Authorization": f"Bearer {jwt_token}", "Accept": "application/vnd.github+json"},
            timeout=REQUEST_TIMEOUT,
        )
        log.info("Access token request status: %d", response.status_code)
        response.raise_for_status()
        token = response.json()["token"]
        log.info("Installation access token obtained (length=%d)", len(token))
        return token
    except Exception as e:
        log.error("Failed to get installation access token: %s", e)
        raise


def get_repo(token):
    authed_url = f"https://x-access-token:{token}@github.com/{site_repo_owner}/{site_repo_name}.git"

    if workspace.exists():
        log.info("Workspace directory exists at %s", workspace.resolve())
        try:
            log.info("Attempting to open existing repo at %s", workspace)
            repo = Repo(workspace)
            log.info("Opened existing repo, head commit: %s", repo.head.commit.hexsha)
            return repo
        except Exception as e:
            log.warning("Failed to open existing repo: %s — removing and re-cloning", e)
            shutil.rmtree(workspace)

    log.info("Attempting to clone %s into %s (depth=1)", site_repo_https, workspace)
    try:
        repo = Repo.clone_from(authed_url, workspace, depth=1)
        log.info("Clone complete, head commit: %s", repo.head.commit.hexsha)
        log.info("Remote origin URL: %s", site_repo_https)
        return repo
    except Exception as e:
        log.error("Failed to clone repo: %s", e)
        raise


def get_data(client_id, client_secret, song_id):
    log.info("Attempting to request Spotify auth token")
    try:
        auth_response = post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            timeout=REQUEST_TIMEOUT,
        )
        log.info("Auth response status: %d", auth_response.status_code)
        auth_response.raise_for_status()
    except Exception as e:
        log.error("Failed to obtain Spotify auth token: %s", e)
        raise

    try:
        access_token = auth_response.json()["access_token"]
        log.info("Access token obtained (length=%d)", len(access_token))
    except (KeyError, ValueError) as e:
        log.error("Failed to parse access token from auth response: %s", e)
        raise

    url = f"https://api.spotify.com/v1/tracks/{song_id}"
    log.info("Attempting to fetch track data from %s", url)
    try:
        response = get(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=REQUEST_TIMEOUT,
        )
        log.info("Track response status: %d", response.status_code)
        response.raise_for_status()
        log.info("Track data received: name=%r", response.json().get("name"))
        return response
    except Exception as e:
        log.error("Failed to fetch track data: %s", e)
        raise


def get_popularity(client_id, client_secret, song_id):
    response = get_data(client_id, client_secret, song_id)
    try:
        popularity = response.json()["popularity"]
        if popularity is None:
            raise ValueError("Spotify returned null for popularity")
        log.info("Popularity score: %d", popularity)
        return popularity
    except (KeyError, ValueError) as e:
        log.error("Failed to parse popularity from track response: %s", e)
        raise


def main():
    log.info("=== itsbeginningtolookalotlikechristmas-datagather starting ===")
    log.info("Python version: %s", sys.version)
    log.info("Working directory: %s", Path.cwd())

    log.info("SPOTIFY_CLIENT_ID: %s", f"non-empty ({len(our_client_id)} chars)" if our_client_id else "EMPTY")
    log.info("SPOTIFY_CLIENT_SECRET: %s", f"non-empty ({len(our_client_secret)} chars)" if our_client_secret else "EMPTY")
    log.info("GITHUB_APP_ID: %s", f"non-empty ({len(github_app_id)} chars)" if github_app_id else "EMPTY")
    log.info("GITHUB_APP_PRIVATE_KEY: %s", f"non-empty ({len(github_app_private_key)} chars)" if github_app_private_key else "EMPTY")
    log.info("GIT_USER_NAME: %s", git_user_name)
    log.info("GIT_USER_EMAIL: %s", git_user_email)

    if not our_client_id or not our_client_secret:
        log.error("Missing Spotify credentials — aborting")
        sys.exit(1)

    if not github_app_id or not github_app_private_key:
        log.error("Missing GitHub App credentials — aborting")
        sys.exit(1)

    check_github_reachable()

    log.info("--- Step 1: get GitHub App token ---")
    token = get_github_app_token(github_app_id, github_app_private_key)

    log.info("--- Step 2: get repo ---")
    repo = get_repo(token)

    data_file = workspace / data_file_relative
    log.info("Data file path: %s (exists=%s)", data_file, data_file.exists())
    log.info("Data file parent dir exists: %s", data_file.parent.exists())
    if data_file.exists():
        try:
            with open(data_file) as f:
                log.info("Current data file line count: %d", sum(1 for _ in f))
        except Exception as e:
            log.warning("Failed to read existing data file: %s", e)

    log.info("--- Step 3: fetch popularity from Spotify ---")
    popularity = get_popularity(
        client_id=our_client_id,
        client_secret=our_client_secret,
        song_id=this_song_id,
    )

    log.info("--- Step 4: write data file ---")
    entry = f"{datetime.now().isoformat()}, {popularity}\n"
    log.info("Attempting to write entry to %s: %r", data_file, entry)
    try:
        with open(data_file, "a") as f:
            f.write(entry)
        log.info("Write complete")
    except Exception as e:
        log.error("Failed to write data file: %s", e)
        raise

    log.info("--- Step 5: git commit ---")
    try:
        log.info("Attempting to configure git user")
        repo.config_writer().set_value("user", "name", git_user_name).release()
        repo.config_writer().set_value("user", "email", git_user_email).release()
        log.info("Git user configured as %s <%s>", git_user_name, git_user_email)
    except Exception as e:
        log.error("Failed to configure git user: %s", e)
        raise

    try:
        log.info("Attempting to stage %s", data_file_relative)
        repo.index.add([str(data_file_relative)])
        log.info("Staged %s", data_file_relative)
    except Exception as e:
        log.error("Failed to stage file: %s", e)
        raise

    diff = repo.index.diff("HEAD")
    log.info("Diff against HEAD: %d change(s)", len(diff))

    if diff:
        try:
            log.info("Attempting to commit changes")
            commit = repo.index.commit("Update data.csv with daily popularity")
            log.info("Commit created: %s", commit.hexsha)
        except Exception as e:
            log.error("Failed to create commit: %s", e)
            raise

        log.info("--- Step 6: git push ---")
        authed_url = f"https://x-access-token:{token}@github.com/{site_repo_owner}/{site_repo_name}.git"
        log.info("Attempting to push to origin via HTTPS")
        try:
            repo.remotes.origin.set_url(authed_url)
            push_info = repo.remotes.origin.push()
            for info in push_info:
                log.info("Push result: flags=%s summary=%r", info.flags, info.summary)
                if info.flags & info.ERROR:
                    raise RuntimeError(f"Push rejected: {info.summary.strip()}")
            log.info("Push complete")
        except Exception as e:
            log.error("Failed to push to origin: %s", e)
            raise
    else:
        log.info("No changes to commit — data file unchanged")

    log.info("=== itsbeginningtolookalotlikechristmas-datagather complete ===")


if __name__ == "__main__":
    main()
