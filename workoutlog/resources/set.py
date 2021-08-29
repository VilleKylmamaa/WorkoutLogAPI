import json
from datetime import datetime, timedelta
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from workoutlog.models import Set, Exercise, Workout
from workoutlog import db
from workoutlog.utils import WorkoutLogBuilder, create_error_response, strfTimedelta
from workoutlog.constants import *


class SetsWithinWorkout(Resource):

    def get(self, exercise_name, workout_id):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout found with the id '{}'".format(workout_id)
            )
        
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise found with the name '{}'".format(exercise_name)
            )

        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("profile", SET_PROFILE)
    
        path = request.endpoint
        if path == "api.sets_workouts_path":
            body.add_control("self", url_for(
                "api.sets_workouts_path",
                workout_id=workout_id,
                exercise_name=exercise_name
                )
            )
            body.add_control("profile", SET_PROFILE)
            body.add_control("up", url_for(
                "api.exerciseitem",
                workout_id=workout_id,
                exercise_name=exercise_name
                )
            )
            body.add_control_add_set(workout_id, exercise_name)
        elif path == "api.sets_exercises_path":
            body.add_control("self", url_for(
                "api.sets_exercises_path", 
                workout_id=workout_id, 
                exercise_name=exercise_name
                )
            )
            body.add_control("profile", SET_PROFILE)
            body.add_control("up", url_for(
                "api.workoutitem",
                workout_id=workout_id, 
                exercise_name=exercise_name
                )
            )
            body.add_control_add_set(workout_id, exercise_name)
        
        body["items"] = []
        for db_set in Set.query.filter_by(workout=db_workout, exercise=db_exercise).all():
            item = WorkoutLogBuilder(
                order_in_workout=db_set.order_in_workout,
                weight=db_set.weight,
                number_of_reps=db_set.number_of_reps,
                reps_in_reserve=db_set.reps_in_reserve,
                rate_of_perceived_exertion=db_set.rate_of_perceived_exertion,
                duration=strfTimedelta(db_set.duration, "{hours}h {minutes}min"),
                distance=db_set.distance
            )
            if path == "api.sets_workouts_path":
                item.add_control("self", url_for(
                    "api.set_workouts_path",
                    workout_id=workout_id, 
                    exercise_name=exercise_name, 
                    order_in_workout=db_set.order_in_workout
                    )
                )
                item.add_control_delete_set_workouts_path(
                    workout_id=db_set.workout_id,
                    exercise_name=db_exercise.exercise_name,
                    order_in_workout=db_set.order_in_workout
                )
            elif path == "api.sets_exercises_path":
                item.add_control("self", url_for(
                    "api.set_workouts_path",
                    workout_id=workout_id,
                    exercise_name=exercise_name,
                    order_in_workout=db_set.order_in_workout
                    )
                )
                item.add_control_delete_set_exercises_path(
                    workout_id=db_set.workout_id,
                    exercise_name=db_exercise.exercise_name,
                    order_in_workout=db_set.order_in_workout
                )
            item.add_control("profile", SET_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)

    def post(self, workout_id, exercise_name):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout was found with the id '{}'".format(workout_id)
            )

        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise was found with the name '{}'".format(exercise_name)
            )

        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Set.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        
        # Use the order_in_workout in the request if provided by the client
        # Otherwise generate it automatically setting it to the first available
        # number found starting from 1 and incrementing by 1
        try:
            order_in_workout = request.json["order_in_workout"]
        except KeyError:
            order_in_workout = 1
            order_numbers = []
            for db_set in Set.query.filter_by(workout=db_workout, exercise=db_exercise).all():
                order_numbers.append(db_set.order_in_workout)
            found_available_number = False
            while not found_available_number:
                if order_in_workout in order_numbers:
                    order_in_workout += 1
                else:
                    found_available_number = True

        set = Set(
            order_in_workout=order_in_workout,
            exercise=db_exercise,
            workout=db_workout
        )

        # Iterate over nullable properties in the request and ignore
        # the KeyError request.json[] from a key missing. This way the client
        # doesn't have to send nulls for columns it doesn't care about.
        for prop in request.json:
            try:
                if prop == "weight":
                    set.weight = request.json[prop]
                elif prop == "number_of_reps":
                    set.number_of_reps = request.json[prop]
                elif prop == "reps_in_reserve":
                    set.reps_in_reserve = request.json[prop]
                elif prop == "rate_of_perceived_exertion":
                    set.rate_of_perceived_exertion = request.json[prop]
                elif prop == "duration":
                    try:
                        duration_in_time = datetime.strptime(
                            request.json["duration"], "%H:%M"
                        )
                    except ValueError as e:
                        return create_error_response(400, "Invalid duration. " +
                            "Duration must match format HH:MM, for example 1:20", str(e)
                        )
                    duration_in_delta = timedelta(
                        hours=duration_in_time.hour, 
                        minutes=duration_in_time.minute
                    )
                    set.duration = duration_in_delta
                elif prop == "distance":
                    set.distance = request.json[prop]
            except KeyError:
                pass

        try:
            db.session.add(set)
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Set with order '{}' in workout '{}' for exercise '{}' " +
                "already exists.".format(
                    request.json["order_in_workout"], workout_id, exercise_name
                )
            )

        return Response(status=201, headers={
            "Location": url_for("api.set_workouts_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=set.order_in_workout)
        })


class SetItem(Resource):

    def get(self, workout_id, exercise_name, order_in_workout):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout found with the id '{}'".format(workout_id)
            )

        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise found with the name '{}'".format(exercise_name)
            )
        
        db_set = Set.query.filter_by(
            workout=db_workout,
            exercise=db_exercise,
            order_in_workout=order_in_workout
        ).first()

        if db_set is None:
            return create_error_response(
                404, "Not found",
                "No set found with the order number '{}'".format(order_in_workout)
            )

        body = WorkoutLogBuilder(
            order_in_workout=db_set.order_in_workout,
            weight=db_set.weight,
            number_of_reps=db_set.number_of_reps,
            reps_in_reserve=db_set.reps_in_reserve,
            rate_of_perceived_exertion=db_set.rate_of_perceived_exertion,
            duration=strfTimedelta(db_set.duration, "{hours}h {minutes}min"),
            distance=db_set.distance
        )
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)

        path = request.endpoint
        if path == "api.set_workouts_path":
            body.add_control("self", url_for(
                "api.set_workouts_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=order_in_workout
                )
            )
            body.add_control("profile", SET_PROFILE)
            body.add_control("collection", url_for(
                "api.sets_workouts_path",
                workout_id=workout_id,
                exercise_name=exercise_name
                )
            )
            body.add_control_edit_set_workouts_path(
                workout_id, exercise_name, order_in_workout
            )
            body.add_control_delete_set_workouts_path(
                workout_id, exercise_name, order_in_workout
            )
        elif path == "api.set_exercises_path":
            body.add_control("self", url_for(
                "api.set_exercises_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=order_in_workout
                )
            )
            body.add_control("profile", SET_PROFILE)
            body.add_control("collection", url_for(
                "api.sets_exercises_path",
                workout_id=workout_id,
                exercise_name=exercise_name
                )
            )
            body.add_control_edit_set_exercises_path(
                workout_id, exercise_name, order_in_workout
            )
            body.add_control_delete_set_exercises_path(
                workout_id, exercise_name, order_in_workout
            )

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)


    def put(self, workout_id, exercise_name, order_in_workout):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No workout was found with the id '{}'".format(workout_id)
            )

        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise was found with the name '{}'".format(exercise_name)
            )
        
        db_set = Set.query.filter_by(
            workout_id=workout_id,
            exercise_id=db_exercise.id,
            order_in_workout=order_in_workout
            ).first()
        
        if db_set is None:
            return create_error_response(
                404, "Not found",
                "No set was found with the order number '{}'".format(order_in_workout)
            )
        
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Set.get_schema())
        except ValidationError as e:
            return create_error_response(400,
                "Invalid JSON document. Missing field or incorrect type.", str(e)
            )

        # Edit values that were included in the request and skip the rest
        for prop in request.json:
            try:
                if prop == "order_in_workout":
                    db_set.order_in_workout = request.json[prop]
                    order_in_workout_for_error = request.json[prop]
                elif prop == "weight":
                    db_workout.weight = request.json[prop]
                elif prop == "number_of_reps":
                    db_workout.average_heart_rate = request.json[prop]
                elif prop == "reps_in_reserve":
                    db_workout.reps_in_reserve = request.json[prop]
                elif prop == "rate_of_perceived_exertion":
                    db_workout.rate_of_perceived_exertion = request.json[prop]
                elif prop == "duration":
                    try:
                        duration_in_time = datetime.strptime(
                            request.json["duration"], "%H:%M"
                        )
                    except ValueError as e:
                        return create_error_response(400, "Invalid duration. " +
                            "Duration must match format HH:MM, for example 1:20", str(e)
                        )
                    duration_in_delta = timedelta(
                        hours=duration_in_time.hour,
                        minutes=duration_in_time.minute
                    )
                    db_set.duration = duration_in_delta
                elif prop =="distance":
                    db_workout.distance = request.json[prop]
            except KeyError:
                pass
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Set with the order_in_workout number '{}' in workout '{}' for " +
                "exercise '{}' already exists.".format(
                    order_in_workout_for_error, workout_id, exercise_name
                )
            )

        return Response(status=204)


    def delete(self, workout_id, exercise_name, order_in_workout):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise found with the name '{}'".format(exercise_name)
            )
        
        db_set = Set.query.filter_by(
            workout_id=workout_id,
            exercise_id=db_exercise.id,
            order_in_workout=order_in_workout
        ).first()

        if db_set is None:
            return create_error_response(
                404, "Not found",
                "No set was found in workout '{}' for exercise '{}' for the " + 
                "order number '{}'".format(
                    workout_id, exercise_name, order_in_workout
                )
            )

        db.session.delete(db_set)
        db.session.commit()

        return Response(status=204)
