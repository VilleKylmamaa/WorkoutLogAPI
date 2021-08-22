import json
from datetime import datetime
from jsonschema import validate, ValidationError
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from workoutlog.models import MaxData, Exercise
from workoutlog import db
from workoutlog.utils import WorkoutLogBuilder, create_error_response
from workoutlog.constants import *


class MaxDataForExercise(Resource):

    def get(self, exercise_name):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No data found for exercise '{}'".format(exercise_name)
            )

        body = WorkoutLogBuilder()
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.maxdataforexercise", exercise_name=exercise_name))
        body.add_control("up", url_for("api.exerciseitem", exercise_name=exercise_name))
        body.add_control_add_max_data(exercise_name)
        
        body["items"] = []
        for db_max_data in MaxData.query.filter_by(exercise=db_exercise).all():
            item = WorkoutLogBuilder(
                order_for_exercise=db_max_data.order_for_exercise,
                date_time=db_max_data.date_time.strftime('%Y-%m-%d %H:%M'),
                training_max=db_max_data.training_max,
                estimated_max=db_max_data.estimated_max,
                tested_max=db_max_data.tested_max
            )
            item.add_control("self", url_for("api.maxdataitem",
             order_for_exercise=db_max_data.order_for_exercise, exercise_name=exercise_name))
            item.add_control("profile", MAX_DATA_PROFILE)
            body["items"].append(item)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)

    def post(self, exercise_name):
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
            validate(request.json, MaxData.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document. Missing field or incorrect type.", str(e))

        # Use the order_for_exercise in the request if provided by the client
        # Otherwise generate it automatically setting it to the first available
        # number found starting from 1 and incrementing by 1
        try:
            order_for_exercise = request.json["order_for_exercise"]
        except KeyError:
            order_for_exercise = 1
            order_numbers = []
            for db_max_data in MaxData.query.filter_by(exercise=db_exercise).all():
                order_numbers.append(db_max_data.order_for_exercise)
            found_available_number = False
            while not found_available_number:
                if order_for_exercise in order_numbers:
                    order_for_exercise += 1
                else:
                    found_available_number = True
        
        try:
            max_data = MaxData(
                order_for_exercise=order_for_exercise,
                date_time=datetime.strptime(request.json["date_time"], "%Y-%m-%d %H:%M"),
                exercise=db_exercise
            )
        except ValueError as e:
            return create_error_response(400, "Invalid datetime" +
                "Datetime must match format YYYY-MM-DD HH:MM", str(e))

        # Iterate over nullable properties in the request and ignore
        # the KeyError request.json[] from a key missing. This way the client
        # doesn't have to send nulls for columns it doesn't care about.
        for prop in request.json:
            try:
                if prop == "training_max":
                    max_data.training_max = request.json[prop]
                elif prop =="estimated_max":
                    max_data.estimated_max = request.json[prop]
                elif prop =="tested_max":
                    max_data.tested_max = request.json[prop]
            except KeyError:
                pass

        try:
            db.session.add(max_data)
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Max data for exercise '{}' with order number '{}' already exists.".format(exercise_name, request.json["order_for_exercise"])
            )

        return Response(status=201, headers={
            "Location": url_for("api.maxdataitem",
            exercise_name=exercise_name,
            order_for_exercise=max_data.order_for_exercise)
        })


class MaxDataItem(Resource):

    def get(self, exercise_name, order_for_exercise):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No data found for exercise '{}'".format(exercise_name)
            )
        
        db_max_data = MaxData.query.filter_by(exercise=db_exercise, order_for_exercise=order_for_exercise).first()
        if db_max_data is None:
            return create_error_response(
                404, "Not found",
                "No data found for max data '{}'".format(order_for_exercise)
            )

        body = WorkoutLogBuilder(
            order_for_exercise=db_max_data.order_for_exercise,
            date_time=db_max_data.date_time.strftime('%Y-%m-%d %H:%M'),
            training_max=db_max_data.training_max,
            estimated_max=db_max_data.estimated_max,
            tested_max=db_max_data.tested_max
        )
        body.add_namespace("workoutlog", LINK_RELATIONS_URL)
        body.add_control("self", url_for("api.maxdataitem", order_for_exercise=order_for_exercise, exercise_name=exercise_name))
        body.add_control("profile", MAX_DATA_PROFILE)
        body.add_control("collection", url_for("api.maxdataforexercise", exercise_name=exercise_name))
        body.add_control_edit_max_data(exercise_name, order_for_exercise)
        body.add_control_delete_max_data(exercise_name=exercise_name, order_for_exercise=order_for_exercise)

        return Response(json.dumps(body, indent=4), 200, mimetype=MASON)


    def put(self, exercise_name, order_for_exercise):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No exercise was found with the name '{}'".format(exercise_name)
            )
        
        db_max_data = MaxData.query.filter_by(
            exercise_id=db_exercise.id,
            order_for_exercise=order_for_exercise
            ).first()
        
        if db_max_data is None:
            return create_error_response(
                404, "Not found",
                "No max data was found for exercise '{}' for order number '{}'".format(
                    exercise_name, order_for_exercise
                )
            )
        
        if not request.json:
            return create_error_response(
                415, "Unsupported media type",
                "Requests must be JSON"
            )

        try:
            validate(request.json, MaxData.get_schema())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document. Missing field or incorrect type.", str(e))

        # Edit values that were included in the request and skip the rest
        for prop in request.json:
            try:
                if prop == "order_for_exercise":
                    db_max_data.order_for_exercise = request.json[prop]
                    order_for_exercise_for_error = request.json[prop]
                elif prop == "date_time":
                    try:
                        date_time_string = datetime.strptime(request.json["date_time"], "%Y-%m-%d %H:%M")
                        for max_data in MaxData.query.all():
                            if max_data is not MaxData.query.filter_by(exercise=db_exercise, order_for_exercise=order_for_exercise).first():
                                if max_data.date_time == date_time_string:
                                    return create_error_response(
                                        409, "Already exists",
                                        "Workout with date_time '{}' already exists".format(request.json["date_time"])
                                    )
                        db_max_data.date_time = date_time_string
                    except ValueError as e:
                        return create_error_response(400, "Invalid datetime." +
                            "Datetime must match format YYYY-MM-DD HH:MM", str(e))
                elif prop == "training_max":
                    db_max_data.training_max = request.json[prop]
                elif prop =="estimated_max":
                    db_max_data.estimated_max = request.json[prop]
                elif prop =="tested_max":
                    db_max_data.tested_max = request.json[prop]
            except KeyError:
                pass
        
        try:
            db.session.commit()
        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Max data for exercise '{}' with the order number '{}' already exists.".format(
                    exercise_name, order_for_exercise_for_error)
            )

        return Response(status=204)


    def delete(self, exercise_name, order_for_exercise):
        db_exercise = Exercise.query.filter_by(exercise_name=exercise_name).first()
        if db_exercise is None:
            return create_error_response(
                404, "Not found",
                "No data found for exercise '{}'".format(exercise_name)
            )

        db_max_data = MaxData.query.filter_by(
            exercise_id=db_exercise.id,
            order_for_exercise=order_for_exercise
            ).first()
        
        if db_max_data is None:
            return create_error_response(
                404, "Not found",
                "No max data was found for exercise '{}' for order number '{}'".format(
                    exercise_name, order_for_exercise
                )
            )

        db.session.delete(db_max_data)
        db.session.commit()

        return Response(status=204)

