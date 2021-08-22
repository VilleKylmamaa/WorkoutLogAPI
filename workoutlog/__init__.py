import json
import os
from flask import Flask, Response, send_from_directory, redirect
from flask.cli import with_appcontext
from flask_sqlalchemy import SQLAlchemy
from workoutlog.constants import *
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

db = SQLAlchemy()

# Based on http://flask.pocoo.org/docs/1.0/tutorial/factory/#the-application-factory
# Modified to use Flask SQLAlchemy
def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "development.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Enforce foreign key constraints
    @event.listens_for(Engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
         if isinstance(dbapi_connection, SQLite3Connection):
              cursor = dbapi_connection.cursor()
              cursor.execute("PRAGMA foreign_keys=ON;")
              cursor.close()

    db.init_app(app)

    from . import models
    from . import api
    
    # add CLI commands
    app.cli.add_command(models.init_db_command)
    app.cli.add_command(models.delete_db_command)
    app.cli.add_command(models.insert_initial_data)
    app.register_blueprint(api.api_bp)

    from .utils import WorkoutLogBuilder

    @app.route("/api/", methods=["GET"])
    def entry():
        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", "/api/")
        body.add_control_get_workouts()
        body.add_control_get_exercises()
        body.add_control_get_weekly_programming_all()
        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)

    @app.route(LINK_RELATIONS_URL)
    def send_link_relations_html():
        return redirect(APIARY_URL + "link-relations")

    @app.route("/profiles/<profile>/")
    def send_profile_html(profile):
        return redirect(APIARY_URL + "{}/".format(profile))

    @app.route("/workoutlog/")
    def workout_log_site():
        return app.send_static_file("html/workoutlog.html")

    @app.route('/favicon.ico') 
    def favicon(): 
        return send_from_directory(app.static_folder, "images/favicon.png")

    
    return app