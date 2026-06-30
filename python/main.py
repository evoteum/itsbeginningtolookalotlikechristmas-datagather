import logging
import shutil
import socket
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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
ssh_key_path = getenv("GIT_SSH_KEY_PATH", str(Path.home() / ".ssh" / "id_ed25519"))
git_user_name = getenv("GIT_USER_NAME", "evoteum-bot")
git_user_email = getenv("GIT_USER_EMAIL", "evoteum-bot@evoteum.com")
site_repo_url = "git@github.com:evoteum/itsbeginningtolookalotlikechristmas.git"
data_file_relative = Path("site") / "data.csv"
this_song_id = "2pXpURmn6zC5ZYDMms6fwa"
workspace = Path("workspace")
REQUEST_TIMEOUT = 30


def check_github_reachable():
    log.info("Attempting to reach github.com:22 via TCP")
    try:
        with socket.create_connection(("github.com", 22), timeout=10) as sock:
            banner = sock.recv(64).decode(errors="replace").strip()
            log.info("github.com:22 reachable, banner: %r", banner)
    except Exception as e:
        log.error("Failed to reach github.com:22: %s", e)
        raise


def get_repo():
    ssh_key = Path(ssh_key_path)
    log.info("SSH key path: %s", ssh_key_path)
    log.info("SSH key exists: %s", ssh_key.exists())
    if ssh_key.exists():
        import stat
        mode = oct(stat.S_IMODE(ssh_key.stat().st_mode))
        log.info("SSH key permissions: %s", mode)
        log.info("SSH key size: %d bytes", ssh_key.stat().st_size)
        try:
            result = subprocess.run(
                ["ssh-keygen", "-lf", ssh_key_path],
                capture_output=True, text=True, timeout=10,
            )
            log.info("SSH key fingerprint: %s", result.stdout.strip())
        except Exception as e:
            log.warning("Failed to get SSH key fingerprint: %s", e)

    check_github_reachable()

    ssh_cmd = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no -o ConnectTimeout=30 -v"
    log.info("SSH command: %s", ssh_cmd)

    if workspace.exists():
        log.info("Workspace directory exists at %s", workspace.resolve())
        try:
            log.info("Attempting to open existing repo at %s", workspace)
            repo = Repo(workspace)
            log.info("Opened existing repo, head commit: %s", repo.head.commit.hexsha)
            return repo
        except Exception as e:
            log.warning("Failed to open existing repo: %s:removing and re-cloning", e)
            shutil.rmtree(workspace)

    log.info("Attempting to clone %s into %s (depth=1)", site_repo_url, workspace)
    try:
        repo = Repo.clone_from(site_repo_url, workspace, env={"GIT_SSH_COMMAND": ssh_cmd}, depth=1)
        log.info("Clone complete, head commit: %s", repo.head.commit.hexsha)
        log.info("Remote origin URL: %s", repo.remotes.origin.url)
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
    log.info("GIT_SSH_KEY_PATH: %s", ssh_key_path)
    log.info("GIT_USER_NAME: %s", git_user_name)
    log.info("GIT_USER_EMAIL: %s", git_user_email)

    if not our_client_id or not our_client_secret:
        log.error("Missing Spotify credentials")
        sys.exit(1)

    log.info("--- Step 1: get repo ---")
    repo = get_repo()

    data_file = workspace / data_file_relative
    log.info("Data file path: %s (exists=%s)", data_file, data_file.exists())
    log.info("Data file parent dir exists: %s", data_file.parent.exists())
    if data_file.exists():
        try:
            with open(data_file) as f:
                log.info("Current data file line count: %d", sum(1 for _ in f))
        except Exception as e:
            log.warning("Failed to read existing data file: %s", e)

    log.info("--- Step 2: fetch popularity from Spotify ---")
    popularity = get_popularity(
        client_id=our_client_id,
        client_secret=our_client_secret,
        song_id=this_song_id,
    )

    log.info("--- Step 3: write data file ---")
    entry = f"{datetime.now().isoformat()}, {popularity}\n"
    log.info("Attempting to write entry to %s: %r", data_file, entry)
    try:
        with open(data_file, "a") as f:
            f.write(entry)
        log.info("Write complete")
    except Exception as e:
        log.error("Failed to write data file: %s", e)
        raise

    log.info("--- Step 4: git commit ---")
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

        log.info("--- Step 5: git push ---")
        ssh_cmd = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no -o ConnectTimeout=30 -v"
        log.info("Attempting to push to origin")
        try:
            push_info = repo.remotes.origin.push(env={"GIT_SSH_COMMAND": ssh_cmd})
            for info in push_info:
                log.info("Push result: flags=%s summary=%r", info.flags, info.summary)
                if info.flags & info.ERROR:
                    raise RuntimeError(f"Push rejected: {info.summary.strip()}")
            log.info("Push complete")
        except Exception as e:
            log.error("Failed to push to origin: %s", e)
            raise
    else:
        log.info("No changes to commit:data file unchanged")

    log.info("=== itsbeginningtolookalotlikechristmas-datagather complete ===")


if __name__ == "__main__":
    main()
