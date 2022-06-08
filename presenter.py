from typing import Union
import argparse
import pickle
import shutil
import sys
import os

from flask_talisman import Talisman
from flask_seasurf import SeaSurf
from flask import (
    render_template,
    redirect,
    url_for,
    request,
    session,
    Flask,
)

from config import app_config


app = Flask(__name__)
app.secret_key = app_config["secret_key"]
csrf = SeaSurf(app)
Talisman(app,
    force_https=False,
    session_cookie_secure=False,
    content_security_policy={
        "img-src": "'self'",
    }
)

_refresh_time: int = int(app_config["refresh_time_sec"]*1e3)

def add_presentation(name: str) -> None:
    if name in get_presentations():
        print("Error, a presentation with that name already exists",
            file=sys.stderr
        )
        sys.exit(1)
    name = name.replace(" ", "_")
    html_path = os.path.join(
        "templates", app_config["presentations_html"], f"{name}.html"
    )
    iamges_path = os.path.join(app_config["presentations_images"], name)
    with open(html_path, "w") as file:
        file.write(r"{% extends 'presentation.html' %}")
    os.mkdir(iamges_path)
    print("Presentation successfully created.\n" \
        "Add images to present by ordering them " \
        "numerically by their name, ex:\n1.png, 2.png, 3.png\n" \
        f"in the following folder: '{iamges_path}'"
    )

def delete_presentation(name: str) -> None:
    if not name in get_presentations():
        print(f"Error, presentation '{name}' not found.\n" \
            "Make sure you enter the spaces correctly",
            file=sys.stderr
        )
        sys.exit(1)
    name = name.replace(" ", "_")
    html_path = os.path.join(
        "templates", app_config["presentations_html"], f"{name}.html"
    )
    iamges_path = os.path.join(app_config["presentations_images"], name)
    os.remove(html_path)
    shutil.rmtree(iamges_path)
    print("Presentation successfully deleted")

def set_session(presentation: str, token: str) -> None:
    session["presentation"] = presentation
    session["token"] = token

def is_valid_host() -> bool:
    return "token" in session \
        and session["token"] == app_config["auth_token"]

def get_presentations() -> list[str]:
    presentations_path = os.path.join(
        "templates", app_config["presentations_html"]
    )
    return [os.path.splitext(f)[0].replace("_", " ") \
        for f in os.listdir(presentations_path)]

def get_presentations_status() -> dict[str, int]:
    if not os.path.exists(app_config["presentations_cache"]):
        default_presentations = {
            presentation: 0
            for presentation in get_presentations()
        }
        update_presentations_status(default_presentations)
    with open(app_config["presentations_cache"], "rb") as file:
        presentations = pickle.load(file)
    return presentations

def update_presentations_status(presentations: dict[str, int]) -> None:
    with open(app_config["presentations_cache"], "wb") as file:
        pickle.dump(presentations, file)

@app.route("/", methods=["GET"])
def index():
   return render_template(
            "index.html",
            presentations=get_presentations()
        )

@app.route("/watch/", methods=["POST"])
def watch():
    if not "presentation" in request.form \
            or not request.form["presentation"] in get_presentations():
        return redirect(url_for("index"))
    pres_name = request.form["presentation"].replace(" ", "_")
    slides = [os.path.split(slide)[1] \
        for slide in os.listdir(f"static/images/{pres_name}")]
    extensions = [os.path.splitext(slide)[1] for slide in slides]
    slide_num = [int(os.path.splitext(slide)[0]) for slide in slides]
    slide_num.sort()
    slides = [f"{name}{ext}" for name, ext in zip(slide_num, extensions)]
    return render_template(
            os.path.join(
                app_config["presentations_html"],
                f"{pres_name}.html"
            ),
            slides=slides,
            presentation=pres_name,
            refresh_time=_refresh_time
        )

@app.route("/host/", methods=["GET", "POST"])
def host():
    if request.method == "GET":
        if not is_valid_host():
            return render_template(
                    "login.html",
                    presentations=get_presentations()
                )
        else:
            return render_template("host.html")
    elif request.method == "POST":
        if not "token" in request.form \
                or not "presentation" in request.form \
                or request.form["token"] != app_config["auth_token"] \
                or not request.form["presentation"] in get_presentations():
            return redirect(url_for("index"))
        presentation = request.form["presentation"]
        set_session(
            presentation,
            request.form["token"]
        )
        pres_status = get_presentations_status()
        if not presentation in pres_status:
            pres_status[presentation] = 0
            update_presentations_status(pres_status)
        return render_template("host.html")
    return redirect(url_for("index"))

@app.route("/controller/", methods=["POST"])
def controller():
    if not any([field in ("terminate", "previous", "next") \
            for field in request.form]):
        return redirect(url_for("index"))
    pres_status = get_presentations_status()
    pres = session["presentation"]
    total_slides = len(os.listdir(
        f"static/images/{pres.replace(' ', '_')}"
    ))
    if not pres in pres_status:
        pres_status[pres] = 0
    if "terminate" in request.form:
        pres_status[pres] = 0
        update_presentations_status(pres_status)
        session.clear()
    if "previous" in request.form:
        if pres_status[pres] == 0:
            pres_status[pres] = total_slides-1
        else:
            pres_status[pres] -= 1
        update_presentations_status(pres_status)
    if "next" in request.form:
        if pres_status[pres] == total_slides-1:
            pres_status[pres] = 0
        else:
            pres_status[pres] += 1
        update_presentations_status(pres_status)
    return redirect(url_for("host"))

@app.route("/status/", methods=["POST"])
def status():
    if not "presentation" in request.form:
        return redirect(url_for("index"))
    pres_status = get_presentations_status()
    presentation = request.form["presentation"].replace("_", " ")
    return str(pres_status[presentation]) if presentation in pres_status \
            else "0"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pilot your presentations with ease"
    )
    parser.add_argument("-n", "--new",
        type=str, help="Add a new presentation"
    )
    parser.add_argument("-d", "--delete",
        type=str, help="Delete a presentation"
    )
    parser.add_argument("-f", "--flask",
        action=argparse.BooleanOptionalAction,
        help="Run with Flask as a server",
        type=bool
    )
    args = parser.parse_args()
    if args.new is not None:
        add_presentation(args.new)
    if args.delete is not None:
        delete_presentation(args.delete)
    if args.flask:
        app.run(
            host=app_config["flask_host"],
            port=app_config["flask_port"]
        )