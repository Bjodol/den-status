import configparser
from flask import Flask
from flask import render_template
from datetime import datetime, timedelta
import spotipy
import subprocess
import json

app = Flask(__name__)

# Load config
cp = configparser.ConfigParser()
cp.read("settings.cfg")

spotify_user=cp.get("SPOTIFY", "username")
spotify_client_id=cp.get("SPOTIFY", "client_id")
spotify_client_secret=cp.get("SPOTIFY", "client_secret")

git_user = cp.get("CODESTATS", "username")
repos = eval(cp.get("CODESTATS", "repos"), {}, {})

port=cp.get("APP", "port", fallback=7007)


spotify_enabled = spotify_user and spotify_client_id and spotify_client_secret
toke = ""

if spotify_enabled:
    token = spotipy.util.prompt_for_user_token(
        spotify_user,
        "user-read-currently-playing",
        client_id=spotify_client_id,
        client_secret=spotify_client_secret,
        redirect_uri=f"http://localhost:{port}",
    )


def get_code_stats(repo, log_type="diff"):
    try:
        log = f'git {log_type} master --shortstat --author="{git_user}"'
        grep = f'grep -E "fil(e|es) changed"'
        awk = (
            "awk '{files+=$1; inserted+=$4; deleted+=$6; delta+=$4-$6} END {printf \""
            + f"%s %s %s %s"
            + "\", files, inserted, deleted, delta }' -"
        )

        command = " | ".join([log, grep, awk])
        output = subprocess.check_output(command, cwd=repo, shell=True)
        result = output.decode("utf-8").strip()
        return result.split() if result else [None, None, None, None]
    except Exception as e:
        print(e)
        return [None, None, None, None]


@app.route("/")
def hello():
    if spotify_enabled:
        token = spotipy.util.prompt_for_user_token(
            spotify_user,
            "user-read-currently-playing",
            client_id=spotify_client_id,
            client_secret=spotify_client_secret,
            redirect_uri=f"http://localhost:{port}",
        )
    code_stats = []
    for code_path in repos:
        repo_log = {"repoName": code_path.split("/").pop()}
        for i in ["diff", "log"]:
            files, insertions, deletions, delta = get_code_stats(code_path, i)
            repo_log[i] = {
                "files": files,
                "insertions": insertions,
                "deletions": deletions,
                "delta": delta,
            }
        code_stats.append(repo_log)

    code_stats = json.dumps(code_stats)
    return render_template("index.html", token=token, code_stats=code_stats)


@app.route("/bear-dance")
def bear_dance():
    return render_template("bear-dance.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port)
