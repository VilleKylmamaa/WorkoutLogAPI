import json
from datetime import datetime, timedelta
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from workoutlog.utils import strfTimedelta
from workoutlog.models import WeeklyProgramming, Exercise
from workoutlog import db
from workoutlog.utils import WorkoutLogBuilder, create_error_response
from workoutlog.constants import *


class WeeklyProgrammingCollection(Resource):

    def get(self):
        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.weeklyprogrammingcollection"))
        body.add_control_add_weekly_programming()
        body["items"] = []
        for db_weekly_programming in WeeklyProgramming.query.all():
            item = WorkoutLogBuilder(
                week_number=db_weekly_programming.week_number,
                exercise_type=db_weekly_programming.exercise_type,
                intensity=db_weekly_programming.intensity,
                number_of_reps=db_weekly_programming.number_of_reps,
                number_of_sets=db_weekly_programming.number_of_sets,
                reps_in_reserve=db_weekly_programming.reps_in_reserve,
                rate_of_perceived_exertion=db_weekly_programming.rate_of_perceived_exertion,
                duration=strfTimedelta(db_weekly_programming.duration, "{hours}h {minutes}min"),
                distance=db_weekly_programming.distance,
                average_heart_rate=db_weekly_programming.average_heart_rate,
                notes=db_weekly_programming.notes
            )
            item.add_control("self", url_for("api.weeklyprogrammingitem",
                week_number=db_weekly_programming.week_number, exercise_type=db_weekly_programming.exercise_type))
            item.add_control("profile", WEEKLY_PROGRAMMING_PROFILE)
            item.add_control_delete_weekly_programming(
                exercise_type=db_weekly_programming.exercise_type,
                week_number=db_weekly_programming.week_number)
            item.add_control_edit_weekly_programming(
                exercise_type=db_weekly_programming.exercise_type,
                week_number=db_weekly_programming.week_number)
            body["items"].append(item)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)

    def post(self, exercise_name=None):
        db_exercise = None
        if exercise_name is not None:
            db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
            if db_exercise is None:
                return create_error_response(
                    404, "Not found",
                    "No data found for exercise '{}'".format(exercise_name)
                )

        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )
        
        try:
            validate(request.json, WeeklyProgramming.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document. Missing field or incorrect type.", str(e))
        
        if len(request.json["exercise_type"]) > 100:
            return create_error_response(400, "Exercise type too long.")

        weekly_programming = WeeklyProgramming(
            week_number=request.json["week_number"],
            exercise_type=request.json["exercise_type"]
        )

        # Iterate over nullable properties in the request and ignore
        # the KeyError request.json[] from a key missing. This way the client
        # doesn't have to send nulls for columns it doesn't care about.
        for prop in request.json:
            try:
                if prop == "intensity":
                    weekly_programming.intensity = request.json[prop]
                elif prop =="number_of_sets":
                    weekly_programming.number_of_sets = request.json[prop]
                elif prop =="number_of_reps":
                    weekly_programming.number_of_reps = request.json[prop]
                elif prop =="reps_in_reserve":
                    weekly_programming.reps_in_reserve = request.json[prop]
                elif prop =="rate_of_perceived_exertion":
                    weekly_programming.rate_of_perceived_exertion = request.json[prop]
                elif prop =="duration":
                    try:
                        duration_in_time = datetime.strptime(request.json["duration"], "%H:%M")
                    except ValueError as e:
                        return create_error_response(400, "Invalid duration. " +
                            "Duration must match format HH:MM, for example 1:20", str(e))
                    duration_in_delta = timedelta(hours=duration_in_time.hour, minutes=duration_in_time.minute)
                    weekly_programming.duration = duration_in_delta
                elif prop =="distance":
                    weekly_programming.distance = request.json[prop]
                elif prop =="average_heart_rate":
                    weekly_programming.average_heart_rate = request.json[prop]
                elif prop =="max_heart_rate":
                    weekly_programming.max_heart_rate = request.json[prop]
            except KeyError:
                pass

        try:
            db.session.add(weekly_programming)
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Weekly programming for exercise type '{}' for week '{}' already exists.".format(request.json["exercise_type"], request.json["week_number"])
            )

        return Response(status=201, headers={
            "Location": url_for("api.weeklyprogrammingitem",
            exercise_type=weekly_programming.exercise_type,
            week_number=weekly_programming.week_number)
        })


class WeeklyProgrammingForExercise(Resource):

    def get(self, exercise_name):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise found with the name '{}'".format(exercise_name)
            )

        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.weeklyprogrammingforexercise", exercise_name=exercise_name))
        body.add_control("profile", WEEKLY_PROGRAMMING_PROFILE)
        body.add_control("up", url_for("api.exerciseitem", exercise_name=exercise_name))
        body["items"] = []
        for db_weekly_programming in WeeklyProgramming.query.filter_by(exercise_type=db_exercise.exercise_type).all():
            item = WorkoutLogBuilder(
                week_number=db_weekly_programming.week_number,
                exercise_type=db_weekly_programming.exercise_type,
                intensity=db_weekly_programming.intensity,
                number_of_reps=db_weekly_programming.number_of_reps,
                number_of_sets=db_weekly_programming.number_of_sets,
                reps_in_reserve=db_weekly_programming.reps_in_reserve,
                rate_of_perceived_exertion=db_weekly_programming.rate_of_perceived_exertion,
                duration=strfTimedelta(db_weekly_programming.duration, "{hours}h {minutes}min"),
                distance=db_weekly_programming.distance,
                average_heart_rate=db_weekly_programming.average_heart_rate,
                notes=db_weekly_programming.notes
            )
            item.add_control("self", url_for("api.weeklyprogrammingitem",
                exercise_name=exercise_name,
                exercise_type=db_weekly_programming.exercise_type,
                week_number=db_weekly_programming.week_number
                ))
            item.add_control("profile", WEEKLY_PROGRAMMING_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)


class WeeklyProgrammingItem(Resource):

    def get(self, week_number, exercise_type, exercise_name=None):
        db_exercise = None
        if exercise_name is not None:
            db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
            if db_exercise is None:
                return create_error_response(
                    404, "Not found",
                    "No data found for exercise '{}'".format(exercise_name)
                )

        db_weekly_programming = WeeklyProgramming.query.filter_by(week_number=week_number, exercise_type=exercise_type).first()
        if db_weekly_programming is None:
            return create_error_response(
                404, "Not found",
                "No programming data found for week '{}'".format(week_number)
            )

        body = WorkoutLogBuilder(
            week_number=db_weekly_programming.week_number,
            exercise_type=db_weekly_programming.exercise_type,
            intensity=db_weekly_programming.intensity,
            number_of_reps=db_weekly_programming.number_of_reps,
            number_of_sets=db_weekly_programming.number_of_sets,
            reps_in_reserve=db_weekly_programming.reps_in_reserve,
            rate_of_perceived_exertion=db_weekly_programming.rate_of_perceived_exertion,
            duration=strfTimedelta(db_weekly_programming.duration, "{hours}h {minutes}min"),
            distance=db_weekly_programming.distance,
            average_heart_rate=db_weekly_programming.average_heart_rate,
            notes=db_weekly_programming.notes
        )
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.weeklyprogrammingitem", week_number=week_number, exercise_type=exercise_type))
        body.add_control("profile", WEEKLY_PROGRAMMING_PROFILE)
        if db_exercise is not None:
            body.add_control("up", url_for("api.weeklyprogrammingforexercise", exercise_name=exercise_name))
        else:
            body.add_control("collection", url_for("api.weeklyprogrammingcollection"))
        body.add_control_edit_weekly_programming(exercise_type, week_number)
        body.add_control_delete_weekly_programming(exercise_type, week_number)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)


    def put(self, exercise_type, week_number):
        db_weekly_programming = WeeklyProgramming.query.filter_by(
            exercise_type=exercise_type,
            week_number=week_number
            ).first()
        
        if db_weekly_programming is None:
            return create_error_response(
                404, "Not found",
                "No weekly programming data was found for exercise type '{}' and week number '{}'".format(
                    exercise_type, week_number
                )
            )
        
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, WeeklyProgramming.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document. Missing field or incorrect type.", str(e))

        # Edit values that were included in the request and skip the rest
        for prop in request.json:
            try:
                if prop == "week_number":
                    db_weekly_programming.week_number = request.json[prop]
                elif prop =="exercise_type":
                    if len(request.json[prop]) > 100:
                        return create_error_response(400, "Exercise type too long.")
                    db_weekly_programming.exercise_type = request.json[prop]
                elif prop =="intensity":
                    db_weekly_programming.intensity = request.json[prop]
                elif prop =="number_of_sets":
                    db_weekly_programming.number_of_sets = request.json[prop]
                elif prop =="number_of_reps":
                    db_weekly_programming.number_of_reps = request.json[prop]
                elif prop =="reps_in_reserve":
                    db_weekly_programming.reps_in_reserve = request.json[prop]
                elif prop =="rate_of_perceived_exertion":
                    db_weekly_programming.rate_of_perceived_exertion = request.json[prop]
                elif prop == "duration":
                    try:
                        duration_in_time = datetime.strptime(request.json["duration"], "%H:%M")
                    except ValueError as e:
                        return create_error_response(400, "Invalid duration. " +
                            "Duration must match format HH:MM, for example 1:20", str(e))
                    duration_in_delta = timedelta(hours=duration_in_time.hour, minutes=duration_in_time.minute)
                    db_weekly_programming.duration = duration_in_delta
                elif prop =="distance":
                    db_weekly_programming.distance = request.json[prop]
                elif prop =="average_heart_rate":
                    db_weekly_programming.average_heart_rate = request.json[prop]
                elif prop =="notes":
                    db_weekly_programming.notes = request.json[prop]
            except KeyError:
                pass
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Weekly programming data for exercise type '{}' with the week number '{}' already exists.".format(
                    exercise_type,
                    week_number)
            )

        return Response(status=204)


    def delete(self, exercise_type, week_number):
        db_weekly_programming = WeeklyProgramming.query.filter_by(
            exercise_type=exercise_type,
            week_number=week_number
            ).first()

        if db_weekly_programming is None:
            return create_error_response(
                404, "Not found",
                "No weekly programming data was found for exercise type '{}' and week number '{}'".format(
                    exercise_type, week_number
                    )
            )

        db.session.delete(db_weekly_programming)
        db.session.commit()

        return Response(status=204)