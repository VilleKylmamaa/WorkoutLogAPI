import json
from datetime import datetime, timedelta
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from workoutlog.models import Exercise, Workout
from workoutlog import db
from workoutlog.utils import WorkoutLogBuilder, create_error_response, strfTimedelta
from workoutlog.constants import *


class WorkoutCollection(Resource):

    def get(self):
        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.workoutcollection"))
        body.add_control("profile", WORKOUT_PROFILE)
        body.add_control_add_workout()
        
        body["items"] = []
        for db_workout in Workout.query.all():
            item = WorkoutLogBuilder(
                workout_id=db_workout.workout_id,
                date_time=db_workout.date_time.strftime('%Y-%m-%d %H:%M'),
                duration=strfTimedelta(db_workout.duration, "{hours}h {minutes}min"),
                body_weight=db_workout.body_weight,
                average_heart_rate=db_workout.average_heart_rate,
                max_heart_rate=db_workout.max_heart_rate,
                notes=db_workout.notes
            )
            item.add_control("self", url_for("api.workoutitem", workout_id=db_workout.workout_id))
            item.add_control("profile", WORKOUT_PROFILE)
            item.add_control_get_exercises_within_workout(workout_id=db_workout.workout_id)
            item.add_control_edit_workout(db_workout.workout_id)
            item.add_control_delete_workout(db_workout.workout_id)
            body["items"].append(item)

        return Response(json.dumps(body, indent=4, default=str), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(
                415, "Unsupported media type", "Requests must be JSON"
            )

        try:
            validate(request.json, Workout.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document. Missing field or incorrect type.", str(e))

        try:
            workout = Workout(
                date_time=datetime.strptime(request.json["date_time"], "%Y-%m-%d %H:%M"),
            )
        except ValueError as e:
            return create_error_response(400, "Invalid datetime. " +
                "Datetime must match format YYYY-MM-DD HH:MM" + 
                ", for example 2021-8-12 14:15", str(e))

        # Iterate over nullable properties in the request and ignore
        # the KeyError request.json[] from a key missing. This way the client
        # doesn't have to send nulls for columns it doesn't care about.
        for prop in request.json:
            try:
                if prop =="duration":
                    try:
                        duration_in_time = datetime.strptime(request.json["duration"], "%H:%M")
                    except ValueError as e:
                        return create_error_response(400, "Invalid duration. " +
                            "Duration must match format HH:MM, for example 1:20", str(e))
                    duration_in_delta = timedelta(hours=duration_in_time.hour, minutes=duration_in_time.minute)
                    workout.duration = duration_in_delta
                elif prop == "body_weight":
                    workout.body_weight = request.json[prop]
                elif prop =="average_heart_rate":
                    workout.average_heart_rate = request.json[prop]
                elif prop =="max_heart_rate":
                    workout.max_heart_rate = request.json[prop]
                elif prop =="notes":
                    if len(request.json[prop]) > 1000:
                        return create_error_response(400, "Note too long.")
                    workout.notes = request.json[prop]
            except KeyError:
                pass

        try:
            db.session.add(workout)
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Workout session with datetime '{}' already exists".format(request.json["date_time"])
            )

        return Response(status=201, headers={
            "Location": url_for("api.workoutitem", workout_id=workout.workout_id)
        })


class WorkoutsByExercise(Resource):

    def get(self, exercise_name):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise found with the name '{}'".format(exercise_name)
            )

        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.workoutsbyexercise", exercise_name=exercise_name))
        body.add_control("profile", WORKOUT_PROFILE)
        body.add_control("up", url_for("api.exerciseitem", exercise_name=exercise_name))
        
        body["items"] = []
        for db_workout in Workout.query.filter(Workout.exercises.contains(db_exercise)).all():
            item = WorkoutLogBuilder(
                date_time=db_workout.date_time.strftime('%Y-%m-%d %H:%M'),
                duration=strfTimedelta(db_workout.duration, "{hours}h {minutes}min"),
                body_weight=db_workout.body_weight,
                average_heart_rate=db_workout.average_heart_rate,
                max_heart_rate=db_workout.max_heart_rate,
                notes=db_workout.notes
            )
            item.add_control("self", url_for("api.workoutitem", exercise_name=exercise_name, workout_id=db_workout.workout_id))
            item.add_control("profile", WORKOUT_PROFILE)
            item.add_control("sets-within-workout", url_for("api.sets_exercises_path", exercise_name=exercise_name, workout_id=db_workout.workout_id))
            item.add_control_edit_workout(db_workout.workout_id)
            item.add_control_delete_workout(db_workout.workout_id)
            body["items"].append(item)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)


class WorkoutItem(Resource):

    def get(self, workout_id, exercise_name=None):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout was found with the id '{}'".format(workout_id)
            )

        db_exercise = None
        if exercise_name is not None:
            db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
            if db_exercise is None:
                return create_error_response(
                    404, "Not found",
                    "No exercise was found with the name '{}'".format(exercise_name)
                )
        
        # /exercises/<exercise_name>/workouts/<workout_id>/ path
        if db_exercise is not None:
            body = WorkoutLogBuilder(
                date_time=db_workout.date_time.strftime('%Y-%m-%d %H:%M'),
                duration=strfTimedelta(db_workout.duration, "{hours}h {minutes}min"),
                body_weight=db_workout.body_weight,
                average_heart_rate=db_workout.average_heart_rate,
                max_heart_rate = db_workout.max_heart_rate
            )
            body.add_namespace("workoutlog", LINK_RELATIONS_URL)
            body.add_control("self", url_for("api.workoutitem", workout_id=workout_id, exercise_name=exercise_name))
            body.add_control("profile", WORKOUT_PROFILE)
            body.add_control("collection", url_for("api.workoutsbyexercise", exercise_name=exercise_name))
            body.add_control("sets-within-workout", url_for("api.sets_exercises_path", workout_id=workout_id, exercise_name=db_exercise.exercise_name))
            body.add_control_edit_workout(workout_id)
            body.add_control_delete_workout(workout_id)
        # /workouts/<workout_id>/ path
        else:
            body = WorkoutLogBuilder(
                workout_id=db_workout.workout_id,
                date_time=db_workout.date_time.strftime('%Y-%m-%d %H:%M'),
                duration=strfTimedelta(db_workout.duration, "{hours}h {minutes}min"),
                body_weight=db_workout.body_weight,
                average_heart_rate=db_workout.average_heart_rate,
                max_heart_rate = db_workout.max_heart_rate
            )
            body.add_namespace("workoutlog", LINK_RELATIONS_URL)
            body.add_control("self", url_for("api.workoutitem", workout_id=workout_id))
            body.add_control("profile", WORKOUT_PROFILE)
            body.add_control("collection", url_for("api.workoutcollection"))
            body.add_control_get_exercises_within_workout(workout_id=workout_id)
            body.add_control_edit_workout(workout_id)
            body.add_control_delete_workout(workout_id)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)


    def put(self, workout_id):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout was found with the id '{}'".format(workout_id)
            )

        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Workout.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document. Missing field or incorrect type.", str(e))

        # Edit values that were included in the request and skip the rest
        for prop in request.json:
            try:
                if prop == "date_time":
                    try:
                        date_time_string = datetime.strptime(request.json["date_time"], "%Y-%m-%d %H:%M")
                        for workout in Workout.query.all():
                            if workout is not Workout.query.filter_by(workout_id=workout_id).first():
                                if workout.date_time == date_time_string:
                                    return create_error_response(
                                        409, "Already exists",
                                        "Workout with date_time '{}' already exists".format(request.json["date_time"])
                                    )
                        db_workout.date_time = date_time_string
                    except ValueError as e:
                        return create_error_response(400, "Invalid datetime." +
                            "Datetime must match format YYYY-MM-DD HH:MM" + 
                            ", for example 2021-8-12 14:15", str(e))

                elif prop =="duration":
                    try:
                        duration_in_time = datetime.strptime(request.json["duration"], "%H:%M")
                    except ValueError as e:
                        return create_error_response(400, "Invalid duration. " +
                            "Duration must match format HH:MM, for example 1:20", str(e))
                    duration_in_delta = timedelta(hours=duration_in_time.hour, minutes=duration_in_time.minute)
                    db_workout.duration = duration_in_delta
                elif prop == "body_weight":
                    db_workout.body_weight = request.json[prop]
                elif prop =="average_heart_rate":
                    db_workout.average_heart_rate = request.json[prop]
                elif prop =="max_heart_rate":
                    db_workout.max_heart_rate = request.json[prop]
                elif prop =="notes":
                    if len(request.json[prop]) > 1000:
                        return create_error_response(400, "Note too long.")
                    db_workout.notes = request.json[prop]
            except KeyError:
                pass

        # Integrity errors were already checked earlier
        db.session.commit()

        return Response(status=204, headers={
            "Location": url_for("api.workoutitem", workout_id=workout.workout_id)
        })
        

    def delete(self, workout_id):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout was found with the datetime '{}'".format(workout_id)
            )

        db.session.delete(db_workout)
        db.session.commit()

        return Response(status=204)