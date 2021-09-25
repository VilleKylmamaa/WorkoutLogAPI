import json
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from workoutlog.models import Exercise, Workout, Set
from workoutlog import db
from workoutlog.utils import WorkoutLogBuilder, create_error_response
from workoutlog.constants import *


class ExerciseCollection(Resource):

    def get(self): 
        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.exercisecollection"))
        body.add_control("profile", EXERCISE_PROFILE)
        body.add_control_add_exercise()

        body["items"] = []
        for db_exercise in Exercise.query.all():
            item = WorkoutLogBuilder(
                exercise_name=db_exercise.exercise_name,
                exercise_type=db_exercise.exercise_type
            )
            item.add_control("self", url_for(
                "api.exerciseitem", 
                exercise_name=db_exercise.exercise_name
                )
            )
            item.add_control("profile", EXERCISE_PROFILE)
            item.add_control_get_workouts_by_exercise(db_exercise.exercise_name)
            item.add_control_get_max_data_for_exercise(db_exercise.exercise_name)
            item.add_control_get_weekly_programming_for_exercise(db_exercise.exercise_name)
            body["items"].append(item)

        return Response(json.dumps(body, default=str, indent=4), 200, mimetype=MASON)

    def post(self):
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Exercise.get_schema())
        except ValidationError as e:
            return create_error_response(400,
                "Invalid JSON document. Missing field or incorrect type.", str(e)
            )

        if len(request.json["exercise_name"]) == 0:
            return create_error_response(400, "Exercise name is missing.")

        if len(request.json["exercise_name"]) > 100:
            return create_error_response(400, "Exercise name too long.")

        exercise = Exercise(
            exercise_name=request.json["exercise_name"]
        )

        # exercise_type is optional
        exercise_type = request.json.get("exercise_type")
        if exercise_type:
            if len(exercise_type) > 100:
                return create_error_response(400, "Exercise type too long.")
            exercise.exercise_type = exercise_type

        try:
            db.session.add(exercise)
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Exercise with name '{}' already exists.".format(
                    request.json["exercise_name"]
                )
            )

        return Response(status=201, headers={
            "Location": url_for("api.exerciseitem", exercise_name=exercise.exercise_name)
        })


class ExercisesWithinWorkout(Resource):

    def get(self, workout_id):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No data found for workout session with id {}".format(workout_id)
            )

        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.exerciseswithinworkout", workout_id=workout_id))
        body.add_control("profile", EXERCISE_PROFILE)
        body.add_control("up", url_for("api.workoutitem", workout_id=workout_id))
        body.add_control_add_exercise_to_workout(workout_id)
        
        body["items"] = []
        for db_exercise in Exercise.query.filter(Exercise.workouts.contains(db_workout)).all():
            item = WorkoutLogBuilder(
                exercise_name=db_exercise.exercise_name,
                exercise_type=db_exercise.exercise_type
            )
            item.add_control(
                "self", url_for(
                    "api.exerciseitem",
                    workout_id=workout_id,
                    exercise_name=db_exercise.exercise_name)
                )
            item.add_control("profile", EXERCISE_PROFILE)
            item.add_control("workoutlog:sets-within-workout", url_for(
                "api.sets_workouts_path",
                workout_id=workout_id,
                exercise_name=db_exercise.exercise_name)
            )
            item.add_control_get_max_data_for_exercise(db_exercise.exercise_name)
            item.add_control_get_weekly_programming_for_exercise(db_exercise.exercise_name)
            item.add_control_delete_exercise_from_workout(workout_id,db_exercise.exercise_name)
            body["items"].append(item)

        return Response(json.dumps(body, default=str, indent=4), 200, mimetype=MASON)

    def post(self, workout_id):
        db_workout = Workout.query.filter_by(workout_id=workout_id).first()
        if db_workout is None:
            return create_error_response(
                404, "Not found",
                "No data found for workout session with id {}".format(workout_id)
            )
        
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, Exercise.get_schema())
        except ValidationError as e:
            return create_error_response(400,
                "Invalid JSON document. Missing field or incorrect type.", str(e)
            )

        if len(request.json["exercise_name"]) == 0: 
            return create_error_response(400, "Exercise name is missing.")
            
        if len(request.json["exercise_name"]) > 100:
            return create_error_response(400, "Exercise name too long.")
            
        db_exercise = Exercise.query.filter_by(exercise_name=request.json["exercise_name"]).first()
        # Create a new exercise if it doesn't exist yet
        if db_exercise is None:
            exercise = Exercise(
                exercise_name=request.json["exercise_name"],
            )
            try:
                if len(request.json["exercise_type"]) > 100:
                    return create_error_response(400, "Exercise type too long.")
                exercise.exercise_type = request.json["exercise_type"]
            except KeyError:
                pass
            db.session.add(exercise)
            try:
                db_workout.exercises.append(exercise)
            except IntegrityError:
                return create_error_response(
                    409, "Already exists",
                    "Exercise with name '{}' already exists in workout '{}'".format(
                        request.json["exercise_name"], db_workout.workout_id
                    )
                )
            db.session.commit()
        else: # The exercise already exists and can be added to the collection
            for exercise in db_workout.exercises:
                if exercise == db_exercise:
                    return create_error_response(
                        409, "Already exists",
                        "Exercise with name '{}' already exists in workout '{}'".format(
                            request.json["exercise_name"], db_workout.workout_id
                        )
                    )
            else:
                db_workout.exercises.append(db_exercise)
                exercise = db_exercise # For passing to the Location header
                db.session.commit()

        return Response(status=201, headers={
            "Location": url_for(
                "api.exerciseitem", 
                workout_id=workout_id, 
                exercise_name=exercise.exercise_name
            )
        })


class ExerciseItem(Resource):

    def get(self, exercise_name, workout_id=None):
        db_workout = None
        if workout_id is not None:
            db_workout = Workout.query.filter_by(workout_id=workout_id).first()
            if db_workout is None:
                return create_error_response(
                    404, "Not found",
                    "No data found for workout session '{}'".format(workout_id)
                )
        
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No data found for exercise '{}'".format(exercise_name)
            )

        body = WorkoutLogBuilder(
            exercise_name=db_exercise.exercise_name,
            exercise_type=db_exercise.exercise_type
        )
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)

        if db_workout is not None:
            body.add_control("self", url_for(
                "api.exerciseitem", 
                workout_id=workout_id, 
                exercise_name=exercise_name
                )
            )
            body.add_control("profile", EXERCISE_PROFILE)
            body.add_control("collection", url_for(
                "api.exerciseswithinworkout", 
                workout_id=workout_id
                )
            )
            body.add_control(
                "workoutlog:sets-within-workout", url_for(
                    "api.sets_workouts_path",
                    workout_id=workout_id,
                    exercise_name=exercise_name
                    )
                )
            body.add_control_delete_exercise_from_workout(
                db_workout.workout_id,
                exercise_name
                )
        else:
            body.add_control("self", url_for(
                "api.exerciseitem",
                exercise_name=exercise_name
                )
            )
            body.add_control("profile", EXERCISE_PROFILE)
            body.add_control("collection", url_for("api.exercisecollection"))
            body.add_control_get_workouts_by_exercise(exercise_name)
        body.add_control_get_max_data_for_exercise(exercise_name)
        body.add_control_get_weekly_programming_for_exercise(exercise_name)
        body.add_control_edit_exercise(exercise_name)
        body.add_control_delete_exercise(exercise_name)

        return Response(json.dumps(body, default=str, indent=4), 200, mimetype=MASON)


    def put(self, exercise_name):
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
            validate(request.json, Exercise.get_schema())
        except ValidationError as e:
            return create_error_response(400,
                "Invalid JSON document. Missing field or incorrect type.", str(e)
            )

        # Edit values that were included in the request and skip the rest
        for prop in request.json:
            try:
                if prop == "exercise_name":
                    if len(request.json[prop]) == 0:
                        return create_error_response(400, "Exercise name is missing.")
                    if len(request.json[prop]) > 100:
                        return create_error_response(400, "Exercise name too long.")
                    db_exercise.exercise_name = request.json[prop]
                elif prop == "exercise_type":
                    if len(request.json[prop]) > 100:
                        return create_error_response(400, "Exercise type too long.")
                    db_exercise.exercise_type = request.json[prop]
            except KeyError:
                pass
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Exercise with name '{}' already exists.".format(
                    request.json["exercise_name"]
                )
            )

        return Response(status=204)

    
    def delete(self, exercise_name, workout_id=None):
        db_workout = None
        if workout_id is not None:
            db_workout = Workout.query.filter_by(workout_id=workout_id).first()
            if db_workout is None:
                return create_error_response(
                    404, "Not found",
                    "No data found for workout session '{}'".format(workout_id)
                )
    
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise was found with the name '{}'".format(exercise_name)
            )
        
        if db_workout is not None: # Delete exercise from workout
            for db_set in Set.query.filter_by(workout=db_workout, exercise=db_exercise).all():
                db.session.delete(db_set)
            db_workout.exercises.remove(db_exercise)
            db.session.commit()
        else: # Delete workout form database altogether
            db.session.delete(db_exercise)
            db.session.commit()

        return Response(status=204)