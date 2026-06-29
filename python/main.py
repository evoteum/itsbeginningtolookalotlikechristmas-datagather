from dotenv import load_dotenv
from os import getenv
from pathlib import Path
from datetime import datetime
from requests import post, get
from git import Repo

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


def get_repo():
    ssh_cmd = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
    if workspace.exists():
        return Repo(workspace)
    return Repo.clone_from(site_repo_url, workspace, env={"GIT_SSH_COMMAND": ssh_cmd}, depth=1)


def get_popularity(client_id, client_secret, song_id):
    auth_response = post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "client_credentials"},
        auth=(client_id, client_secret),
    )
    auth_response.raise_for_status()
    access_token = auth_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {access_token}"}
    response = get(f"https://api.spotify.com/v1/tracks/{song_id}", headers=headers)
    response.raise_for_status()
    return response.json()["popularity"]


def main():
    repo = get_repo()
    data_file = workspace / data_file_relative

    popularity = get_popularity(
        client_id=our_client_id,
        client_secret=our_client_secret,
        song_id=this_song_id,
    )

    with open(data_file, "a") as f:
        f.write(f"{datetime.now().isoformat()}, {popularity}\n")

    repo.config_writer().set_value("user", "name", git_user_name).release()
    repo.config_writer().set_value("user", "email", git_user_email).release()
    repo.index.add([str(data_file_relative)])
    if repo.index.diff("HEAD"):
        repo.index.commit("Update data.csv with daily popularity")
        ssh_cmd = f"ssh -i {ssh_key_path} -o StrictHostKeyChecking=no"
        repo.remotes.origin.push(env={"GIT_SSH_COMMAND": ssh_cmd})


if __name__ == "__main__":
    print('Getting Christmassyness!')
    main()
