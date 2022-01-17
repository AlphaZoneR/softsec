import dataclasses
import functools
import logging
import os
import pathlib
import sys
import tempfile
import threading
from datetime import datetime
from itertools import tee
import time
import shutil
from typing import Container, List, Optional

import bcrypt
import bson
import dacite
import docker.models.containers
import dotenv
import flask
import flask_socketio
import git
from flask import json

import data
import dbase

dotenv.load_dotenv()

LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)

logging.getLogger("geventwebsocket.handler").setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
LOG.addHandler(handler)


class ContainerWatcherThread(threading.Thread):
    image: str
    email: str
    configuration_id: bson.ObjectId
    build_id: bson.ObjectId
    volume_mappings: List[data.VolumeMapping]
    repo_path: str

    def __init__(
        self,
        image: str,
        email: str,
        configuration_id: bson.ObjectId,
        build_id: bson.ObjectId,
        volume_mappings: List[data.VolumeMapping],
        repo_path: str,
    ):
        super().__init__()
        self.image = image
        self.email = email
        self.configuration_id = configuration_id
        self.build_id = build_id
        self.volume_mappings = volume_mappings
        self.repo_path = repo_path

    def run(self) -> None:

        volumes = list(
            map(
                lambda v: f"{os.path.join(self.repo_path, v.source)}:{v.destination}",
                self.volume_mappings,
            )
        )

        try:
            logs: bytes = docker_client.containers.run(
                self.image,
                detach=False,
                stdout=True,
                stderr=True,
                volumes=volumes,
            )

            user = dbase.get_mongo_collection("users").find_one({"email": self.email})

            user: data.User = dacite.from_dict(data_class=data.User, data=user)
            configuration: data.RepositoryConfiguration = next(
                repository
                for repository in user.repository_configurations
                if repository._id == self.configuration_id
            )

            build: data.Build = next(
                b for b in configuration.builds if b._id == self.build_id
            )

            output = "------------------------------- Run ---------------------------------\n"
            build.output += output + logs.decode() if logs else "No output"
            build.status = "FINISHED"

            dbase.get_mongo_collection("users").replace_one(
                {"_id": user._id}, dataclasses.asdict(user)
            )

            output = ""

        except Exception as e:
            LOG.error(f"There was an issue running the container. {e}")
            output = f"\nThere was an issue running the container. {e}"

        user: data.User = dacite.from_dict(
            data_class=data.User,
            data=dbase.get_mongo_collection("users").find_one({"email": self.email}),
        )

        configuration: data.RepositoryConfiguration = next(
            repository
            for repository in user.repository_configurations
            if repository._id == self.configuration_id
        )

        build: data.Build = next(
            b for b in configuration.builds if b._id == self.build_id
        )

        build.output += output
        build.status = "FINISHED"

        dbase.get_mongo_collection("users").replace_one(
            {"_id": user._id}, dataclasses.asdict(user)
        )


def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if flask.session.get("user") is None:
            return flask.redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def user_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        user = dbase.get_mongo_collection("users").find_one(
            {"email": flask.session["user"]["email"]}
        )

        if not user:
            flask.session = {}
            return flask.redirect("/")

        user: data.User = dacite.from_dict(data_class=data.User, data=user)
        return f(user, *args, **kwargs)

    return decorated_function


def are_mappings_valid(repo_fullpath: str, volume_mappings: List[data.VolumeMapping]):
    for mapping in volume_mappings:
        mapping_fullpath = pathlib.Path(os.path.join(repo_fullpath, mapping.source))
        LOG.debug(f"fullpath={mapping_fullpath}, exists={mapping_fullpath.exists()}")
        if not mapping_fullpath.exists():
            return False

    return True


def is_valid_user(user: dict) -> bool:
    return (
        user is not None
        and type(user) == dict
        and "email" in user
        and "permissions" in user
    )


if __name__ == "__main__":
    app = flask.Flask(
        __name__,
        static_url_path="/",
        static_folder="frontend",
        template_folder="templates",
    )
    app.secret_key = os.environ["APP_SECRET"]
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    for i in range(10):
        try:
            docker_client = docker.from_env()
            break
        except Exception as e:
            LOG.error(f"Error connecting to docker: {e}")

        time.sleep(i)

    dbase.seed()

    socketio = flask_socketio.SocketIO(app, async_mode="gevent", logger=True)

    @app.before_request
    def before_request():
        if (
            not is_valid_user(flask.session.get("user"))
            and "/login" not in flask.request.url
            and "/register" not in flask.request.url
            and "/register.html" not in flask.request.url
            and (
                "/api/register" not in flask.request.url
                or flask.request.method != "POST"
            )
            and (
                "/api/login" not in flask.request.url or flask.request.method != "POST"
            )
        ):
            flask.session["user"] = None
            return flask.redirect("/login")

        if flask.session.get("user") is not None and (
            "/login" in flask.request.url
            or "/register.html" in flask.request.url
            or ("/api/register" in flask.request.url and flask.request.method == "POST")
            or ("/api/login" in flask.request.url and flask.request.method == "POST")
        ):
            return flask.redirect("/index.html")

    @app.get("/")
    @user_required
    def root(user: data.User):
        permissions = flask.session["user"]["permissions"]

        all_repos = []

        if permissions == "admin":
            users = list(dbase.get_mongo_collection("users").find({}))
            users = list(map(lambda u: dacite.from_dict(data.User, u), users))

            for nuser in users:
                all_repos = [*all_repos, *nuser.repository_configurations]

        return flask.render_template(
            "index.html",
            user=user,
            datetime=datetime,
            all_repos=all_repos,
            isadmin=permissions == "admin",
        )

    @app.get("/login")
    def get_login():
        return flask.render_template("login.html")

    @app.get("/configuration/<configuration_id>/build/<build_id>")
    @user_required
    def get_build(user: data.User, configuration_id: str, build_id: str):
        try:
            configuration: data.RepositoryConfiguration = next(
                repository
                for repository in user.repository_configurations
                if str(repository._id) == configuration_id
            )

            build: data.Build = next(
                b for b in configuration.builds if str(b._id) == build_id
            )

            return flask.render_template("build.html", build=build)
        except Exception as e:
            LOG.error(
                f"There was an issue retrieveing build {build_id} for configuration {configuration_id}"
            )

            return flask.Response(
                json.dumps({"error": "Not Found!"}),
                status=404,
                mimetype="application/json",
            )

    @app.post("/api/configuration/<id>/build")
    @user_required
    def build_configuration(user: data.User, id: str):
        configuration = next(
            repository
            for repository in user.repository_configurations
            if str(repository._id) == id
        )

        repo_fullpath = os.path.join(os.environ["REPOS_PATH"], str(configuration._id))

        build = data.Build(
            "------------------------------- Build ---------------------------------\n",
            status="STARTED",
        )
        configuration.builds.append(build)

        dbase.get_mongo_collection("users").replace_one(
            {"_id": user._id}, dataclasses.asdict(user)
        )

        LOG.info(data.RepositoryConfiguration)
        tag = f"{str(configuration._id)}"
        image, tee_object = docker_client.images.build(
            path=repo_fullpath, nocache=True, quiet=False, tag=tag
        )

        for output in tee_object:
            if "stream" in output:
                build.output += f"{output['stream']}"

        configuration.last_ran_at = bson.Timestamp(datetime.now(), 0)
        build.built_at = bson.Timestamp(datetime.now(), 0)

        dbase.get_mongo_collection("users").replace_one(
            {"_id": user._id}, dataclasses.asdict(user)
        )

        ContainerWatcherThread(
            image=image,
            email=user.email,
            configuration_id=configuration._id,
            build_id=build._id,
            repo_path=repo_fullpath,
            volume_mappings=configuration.volume_mappings,
        ).start()

        return flask.Response(json.dumps({}), mimetype="application/json")

    @app.post("/api/configuration/<id>/update")
    @user_required
    def update_repository(user: data.User, id: str):
        configuration = next(
            repository
            for repository in user.repository_configurations
            if str(repository._id) == id
        )

        repo_fullpath = os.path.join(os.environ["REPOS_PATH"], str(configuration._id))

        repo = git.Repo(repo_fullpath)

        try:
            if configuration.private_key:
                with tempfile.NamedTemporaryFile("w") as temp_file:
                    temp_file.write(configuration.private_key)
                    temp_file.flush()
                    os.chmod(temp_file.name, 0o600)

                    with repo.git.custom_environment(
                        GIT_SSH_COMMAND=f"ssh -i {temp_file.name}"
                    ):
                        repo.remote().pull()
            else:
                repo.remote().pull()
        except Exception as e:
            LOG.error("There was an error pulling from the origin.", e)
            return flask.Response(
                json.dumps({"error": "There was an error pulling from the origin"}),
                status=500,
                mimetype="application/json",
            )

        return flask.Response(json.dumps({}), mimetype="application/json")

    @app.delete("/api/configuration/<id>")
    @user_required
    def delete_configuration(user: data.User, id):
        configuration = next(
            repository
            for repository in user.repository_configurations
            if str(repository._id) == id
        )

        user.repository_configurations.remove(configuration)

        dbase.get_mongo_collection("users").replace_one(
            {"_id": user._id}, dataclasses.asdict(user)
        )

        return flask.Response(json.dumps({}), mimetype="application/json")

    @app.post("/api/configuration")
    @user_required
    def new_configuration(user: data.User):
        repository_url: str = flask.request.json["repositoryUrl"]
        private_key: str = flask.request.json["privateKey"]
        volume_mappings = list(
            map(
                lambda x: dacite.from_dict(data.VolumeMapping, x),
                flask.request.json["currentMappings"],
            )
        )

        configuration = data.RepositoryConfiguration(
            repository_url=repository_url,
            private_key=private_key,
            volume_mappings=volume_mappings,
        )

        repo_fullpath = os.path.join(os.environ["REPOS_PATH"], str(configuration._id))

        try:
            if private_key:
                with tempfile.NamedTemporaryFile("w") as temp_file:
                    temp_file.write(private_key)
                    temp_file.flush()
                    os.chmod(temp_file.name, 0o600)

                    git_interface = git.Git()
                    git_interface.update_environment(
                        GIT_SSH_COMMAND=f"ssh -i {temp_file.name}"
                    )
                    git.Repo._clone(
                        git_interface, repository_url, repo_fullpath, git.GitCmdObjectDB
                    )
            else:
                git.Repo.clone_from(
                    repository_url,
                    repo_fullpath,
                )
        except Exception as e:
            LOG.error("Error cloning repository", e)
            return flask.Response(
                json.dumps({"error": "There was an issue cloning the project."}),
                status=500,
                mimetype="application/json",
            )

        if "Dockerfile" not in os.listdir(repo_fullpath):
            LOG.error("Cloning was successful, but Dockerfile was not found.")
            shutil.rmtree(repo_fullpath)
            return flask.Response(
                json.dumps(
                    {
                        "error": "The cloned repository does not contain a Dockerfile in it's root."
                    }
                ),
                status=500,
                mimetype="application/json",
            )

        if not are_mappings_valid(repo_fullpath, volume_mappings):
            LOG.error("Cloning was successful, but invalid volume mappings were given.")
            os.rmdir(repo_fullpath)
            return flask.Response(
                json.dumps({"error": "Some of the volume mappings are invalid."}),
                status=500,
                mimetype="application/json",
            )

        user.repository_configurations.append(configuration)

        dbase.get_mongo_collection("users").replace_one(
            {"_id": user._id}, dataclasses.asdict(user)
        )

        return flask.Response(json.dumps({}), mimetype="application/json")

    @app.post("/api/login")
    def login():

        email: str = flask.request.form["email"]
        password: str = flask.request.form["password"]

        user: Optional[data.User] = dbase.get_mongo_collection("users").find_one(
            {"email": email}
        )

        if not user:
            return flask.Response(
                json.dumps({"error": "Invalid username or password!"}),
                status=403,
                mimetype="application/json",
            )

        user = dacite.from_dict(data_class=data.User, data=user)

        if not bcrypt.checkpw(password.encode(), user.password):
            return flask.Response(
                json.dumps({"error": "Invalid username or password!"}),
                status=403,
                mimetype="application/json",
            )

        flask.session["user"] = {
            "email": email,
            "permissions": "admin" if email == "root@vulnb0x.xyz" else "user",
        }

        return flask.redirect("/")

    @app.post("/api/register")
    def register():
        email: str = flask.request.form.get("email")
        password: str = flask.request.form.get("password")

        if not email or len(email) < 6:
            return flask.Response(
                json.dumps({"error": "Invalid email."}),
                status=400,
                mimetype="application/json",
            )

        if not password or len(password) < 6:
            return flask.Response(
                json.dumps({"error": "Weak password."}),
                status=400,
                mimetype="application/json",
            )

        existing_user: Optional[data.User] = dbase.get_mongo_collection(
            "users"
        ).find_one({"email": email})

        if existing_user is not None:
            return flask.Response(
                json.dumps({"error": "Username already in use."}),
                status=400,
                mimetype="application/json",
            )

        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

        user = data.User(email=email, password=hashed_password)

        dbase.get_mongo_collection("users").insert_one(dataclasses.asdict(user))

        flask.session["user"] = {
            "email": email,
            "permissions": "admin" if email == "root@vulnb0x.xyz" else "user",
        }

        return flask.redirect("/")

    @app.post("/api/logout")
    def logout():
        flask.session["user"] = None

        return flask.redirect("/")

    socketio.run(app, host="0.0.0.0", port=int(os.environ["APP_PORT"]))
