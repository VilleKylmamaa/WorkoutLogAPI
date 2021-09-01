import json
import os
import pytest
import tempfile
import datetime
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event

from workoutlog import create_app, db
from workoutlog.models import Workout, Exercise, Set, MaxData, WeeklyProgramming
from workoutlog.utils import strfTimedelta


# Enforce foreign key constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# Based on http://flask.pocoo.org/docs/1.0/testing/
# and course material example
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        _populate_db()
        
    yield app.test_client()
    
    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)


def _populate_db():
    # Workouts
    workout_1 = Workout(
        date_time=datetime.datetime(2021, 6, 7, 9, 10),
        duration=datetime.timedelta(hours=1, minutes=20),
        body_weight=71.5
        )
    db.session.add(workout_1)
    
    workout_2 = Workout(
        date_time=datetime.datetime(2022, 7, 8, 10, 11),
        duration=datetime.timedelta(hours=1, minutes=30),
        body_weight=71.3
        )
    db.session.add(workout_2)
    
    # Exercises
    squat = Exercise(
        exercise_name="Squat",
        exercise_type="Main lift",
        workouts=[workout_1]
        )
    db.session.add(squat)

    paused_squat = Exercise(
        exercise_name="Paused Squat",
        exercise_type="Variation lift",
        workouts=[workout_2]
        )
    db.session.add(paused_squat)

    # Sets
    for i in range(3):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=100,
            number_of_reps=8,
            reps_in_reserve=4-i,
            exercise=squat,
            workout=workout_1
        ))

    for i in range(3):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=80,
            number_of_reps=8,
            reps_in_reserve=4-i,
            exercise=paused_squat,
            workout=workout_2
        ))  
    # Max data
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=1,
        date=datetime.date.today(),
        training_max=140
        ))
    
    db.session.add(MaxData(
        exercise=paused_squat,
        order_for_exercise=1,
        date=datetime.date.today(),
        training_max=120
        ))

    db.session.add(MaxData(
        exercise=paused_squat,
        order_for_exercise=2,
        date=datetime.date.today(),
        training_max=145
        ))
    
    # WeeklyProgramming
    db.session.add(WeeklyProgramming(
        week_number=1,
        exercise_type="Main lift",
        intensity=70,
        number_of_sets=5,
        number_of_reps=5,
        reps_in_reserve=3
        ))

    db.session.add(WeeklyProgramming(
        week_number=2,
        exercise_type="Main lift",
        intensity=75,
        number_of_sets=4,
        number_of_reps=7,
        reps_in_reserve=2
        ))

    db.session.commit()


def _get_workout_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
            "workout_id": 3,
            "date_time": datetime.datetime(2020, 12, 24, 12, 15).strftime('%Y-%m-%d %H:%M'),
            "duration": "1:45",
            "body_weight": 72,
            "average_heart_rate": 110,
            "max_heart_rate": 150,
            "notes": "hi :D",
            }
    
def _get_exercise_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
            "exercise_name": "Deadlift",
            "exercise_type": "Main lift"
            }

def _get_set_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
            "order_in_workout": 4,
            "weight": 115,
            "number_of_reps": 6,
            "reps_in_reserve": 1,
            "rate_of_perceived_exertion": 9,
            "duration": "1:30",
            "distance": 0
            }

def _get_max_data_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
            "order_for_exercise": 3,
            "date": datetime.date(2020, 12, 24).strftime('%Y-%m-%d'),
            "training_max": 140,
            "estimated_max": 150,
            "tested_max": 145
            }

def _get_weekly_programming_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
            "week_number": 3,
            "exercise_type": "Main lift",
            "intensity": 0.8,
            "number_of_reps": 5,
            "number_of_sets": 5,
            "reps_in_reserve": 3,
            "rate_of_perceived_exertion": 7,
            "duration": "0:30",
            "distance": 0,
            "average_heart_rate": 100,
            "notes": "yee"
            }


def _check_namespace(client, response):
    """
    Checks that the "workoutlog" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """
    
    ns_href = response["@namespaces"]["workoutlog"]["name"]
    resp = client.get(ns_href)
    assert resp.status_code == 302
    
def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """
    
    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    if ctrl == "profile":
        assert resp.status_code == 302
    else:
        assert resp.status_code == 200
    
def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """
    
    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204
    
def _check_control_put_method(ctrl, client, obj, resource):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid resource against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    if resource == "workout":
        body = _get_workout_json()
        body["workout_id"] = obj["workout_id"]
    elif resource == "exercise":
        body = _get_exercise_json()
        body["exercise_name"] = obj["exercise_name"]
    elif resource == "set":
        body = _get_set_json()
        body["order_in_workout"] = obj["order_in_workout"]
    elif resource == "max_data":
        body = _get_max_data_json()
        body["order_for_exercise"] = obj["order_for_exercise"]
        body["date"] = obj["date"]
    elif resource == "weekly_programming":
        body = _get_weekly_programming_json()
        body["exercise_type"] = obj["exercise_type"]
        body["week_number"] = obj["week_number"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204
    
def _check_control_post_method(ctrl, client, obj, resource):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid resource against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """
    
    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    if resource == "workout":
        body = _get_workout_json()
    elif resource == "exercise":
        body = _get_exercise_json()
    elif resource == "set":
        body = _get_set_json()
    elif resource == "max_data":
        body = _get_max_data_json()
    elif resource == "weekly_programming":
        body = _get_weekly_programming_json()
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201



class TestApiEntry(object):
    
    RESOURCE_URL = "/api/"

    # test GET method and that all methods exist for WorkoutCollection
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)


class TestWorkoutCollection(object):
    
    RESOURCE_URL = "/api/workouts/"

    # test GET method and that all methods exist for WorkoutCollection
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method("workoutlog:add-workout", client, body, "workout")
        assert len(body["items"]) == 2
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    # test POST method for WorkoutCollection
    def test_post(self, client):
        valid = _get_workout_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + "3/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200

        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # test with invalid date_time format
        valid["date_time"] = "999"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # send string over 1000 characters as notes field for 400
        long_string = ""
        for i in range(1001):
            long_string += "a"
        valid["notes"] = long_string
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # remove date_time field for 400
        valid.pop("date_time")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestWorkoutsByExercise(object):
    
    RESOURCE_URL = "/api/exercises/Squat/workouts/"

    # test GET method and that all methods exist for WorkoutsByExercise
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("up", client, body)
        assert len(body["items"]) == 1
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

   
class TestWorkoutItem(object):
    
    RESOURCE_URL = "/api/workouts/1/"
    INVALID_URL = "/api/workouts/42/"
    
    # test GET method and that all methods exist for WorkoutItem
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, "workout")
        _check_control_delete_method("workoutlog:delete", client, body)

        # test get with invalid url
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    # test PUT method for WorkoutItem
    def test_put(self, client):
        valid = _get_workout_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another workout's date_time (unique)
        valid["date_time"] = datetime.datetime(2022, 7, 8, 10, 11).strftime('%Y-%m-%d %H:%M')
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid
        valid["date_time"] = datetime.datetime(2025, 12, 12, 12, 12).strftime('%Y-%m-%d %H:%M')
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # send string over 1000 characters as notes field for 400
        long_string = ""
        for i in range(1001):
            long_string += "a"
        valid["notes"] = long_string
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # remove date_time field for 400
        valid.pop("date_time")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
    # test DELETE method for WorkoutItem
    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404


class TestExerciseCollection(object):
    
    RESOURCE_URL = "/api/exercises/"

    # test GET method and that all methods exist for ExerciseCollection
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method("workoutlog:add-exercise", client, body, "exercise")
        assert len(body["items"]) == 2
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    # test POST method for ExerciseCollection
    def test_post(self, client):
        valid = _get_exercise_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + valid["exercise_name"] + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # remove optional exercise_type field for 201
        valid["exercise_name"] = "new text"
        valid.pop("exercise_type")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # send string over 100 characters as exercise_name field for 400
        long_string = ""
        for i in range(101):
            long_string += str(i)
        valid["exercise_name"] = long_string
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        valid["exercise_name"] = "Renew for next test"

        # send string over 100 characters as exercise_type field for 400
        long_string = ""
        for i in range(101):
            long_string += str(i)
        valid["exercise_type"] = long_string
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # send empty string "" as exercise_name field for 400
        valid["exercise_name"] = ""
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # remove exercise_name field for 400
        valid.pop("exercise_name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestExercisesWithinWorkout(object):
    
    RESOURCE_URL = "/api/workouts/1/exercises/"

    # test GET method and that all methods exist for ExercisesWithinWorkout
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method("workoutlog:add-exercise-to-workout", client, body, "exercise")
        assert len(body["items"]) == 1
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    # test POST method for ExercisesWithinWorkout
    def test_post(self, client):
        valid = _get_exercise_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + str(valid["exercise_name"]) + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # send string over 100 characters as exercise_name field for 400
        long_string = ""
        for i in range(101):
            long_string += "a"
        valid["exercise_name"] = long_string
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        valid["exercise_name"] = "Renew for next test"

        # send string over 100 characters as exercise_type field for 400
        long_string = ""
        for i in range(101):
            long_string += str(i)
        valid["exercise_type"] = long_string
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # send empty string "" as exercise_name field for 400
        valid["exercise_name"] = ""
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # remove exercise_name field for 400
        valid.pop("exercise_name")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

   
class TestExerciseItem(object):
    
    RESOURCE_URL = "/api/exercises/Squat/"
    INVALID_URL = "/api/exercises/meme/"
    EXERCISE_WITHIN_WORKOUT_URL = "/api/workouts/1/exercises/Squat/"
    
    # test GET method and that all methods exist for ExerciseItem
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, "exercise")
        _check_control_delete_method("workoutlog:delete", client, body)

        # test get with invalid url
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    # test GET method and that all methods exist for ExerciseItem within a workout
    def test_get_within_workout(self, client):
        resp = client.get(self.EXERCISE_WITHIN_WORKOUT_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, "exercise")
        _check_control_delete_method("workoutlog:delete-from-workout", client, body)

    # test PUT method for ExerciseItem
    def test_put(self, client):
        valid = _get_exercise_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another exercise's exercise_name (unique)
        valid["exercise_name"] = "Paused Squat"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid
        valid["exercise_name"] = "Squat"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # send string over 100 characters as exercise_name field for 400
        long_string = ""
        for i in range(101):
            long_string += "a"
        valid["exercise_name"] = long_string
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        valid["exercise_name"] = "Renew for next test"

        # send string over 100 characters as exercise_type field for 400
        long_string = ""
        for i in range(101):
            long_string += str(i)
        valid["exercise_type"] = long_string
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # remove exercise_name field for 400
        valid.pop("exercise_name")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
    
    # test DELETE for ExerciseItem
    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404     


class TestSetsWithinWorkout(object):
    
    WORKOUTS_URL = "/api/workouts/1/exercises/Squat/sets/"
    EXERCISES_URL = "/api/exercises/Squat/workouts/1/sets/"
    INVALID_WORKOUTS_URL = "/api/workouts/999/exercises/Squat/sets/"
    INVALID_EXERCISES_URL = "/api/workouts/1/exercises/sqwweat/sets/"

    # test GET method and that all methods exist for SetsWithinWorkout
    def test_get(self, client):
        resp = client.get(self.WORKOUTS_URL)
        assert resp.status_code == 200
        resp = client.get(self.EXERCISES_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method("workoutlog:add-set", client, body, "set")
        assert len(body["items"]) == 3
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

        # test invalid links
        resp = client.get(self.INVALID_WORKOUTS_URL)
        assert resp.status_code == 404
        resp = client.get(self.INVALID_EXERCISES_URL)
        assert resp.status_code == 404

    # test POST method for SetsWithinWorkout
    def test_post(self, client):
        valid = _get_set_json()
        
        # test with wrong content type
        resp = client.post(self.WORKOUTS_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # test with valid and see that it exists afterward
        resp = client.post(self.WORKOUTS_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.WORKOUTS_URL + str(valid["order_in_workout"]) + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.WORKOUTS_URL, json=valid)
        assert resp.status_code == 409

        # test with invalid urls
        resp = client.post(self.INVALID_WORKOUTS_URL, data=valid)
        assert resp.status_code == 404
        resp = client.post(self.INVALID_EXERCISES_URL, data=valid)
        assert resp.status_code == 404

        # test that request can be sent without order_in_workout field
        # in which case it will be auto-generated
        valid.pop("order_in_workout")
        resp = client.post(self.WORKOUTS_URL, json=valid)
        assert resp.status_code == 201

        # test sending float to integer column
        valid["number_of_reps"] = 5.555
        resp = client.post(self.WORKOUTS_URL, json=valid)
        assert resp.status_code == 400
        valid["number_of_reps"] = 5

        # test sending float to integer column
        valid["duration"] = "invalid duration"
        resp = client.post(self.WORKOUTS_URL, json=valid)
        assert resp.status_code == 400

      

class TestSetItem(object):

    WORKOUTS_URL = "/api/workouts/1/exercises/Squat/sets/1/"
    EXERCISES_URL = "/api/exercises/Squat/workouts/1/sets/1/"
    INVALID_WORKOUTS_URL = "/api/workouts/999/exercises/Squat/sets/999/"
    INVALID_EXERCISES_URL = "/api/workouts/1/exercises/sqwweat/sets/999/"
    
    # test GET method all methods exist for SetItem
    def test_get(self, client):
        resp = client.get(self.WORKOUTS_URL)
        assert resp.status_code == 200
        resp = client.get(self.EXERCISES_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, "set")
        _check_control_delete_method("workoutlog:delete", client, body)

        # test invalid links
        resp = client.get(self.WORKOUTS_URL)
        assert resp.status_code == 404
        resp = client.get(self.INVALID_EXERCISES_URL)
        assert resp.status_code == 404

    # test PUT method for SetItem
    def test_put(self, client):
        valid = _get_set_json()
        
        # test with wrong content type
        resp = client.put(self.WORKOUTS_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_WORKOUTS_URL, json=valid)
        assert resp.status_code == 404
        
        # test with valid
        resp = client.put(self.WORKOUTS_URL, json=valid)
        assert resp.status_code == 204
    
    # test DELETE method for SetItem
    def test_delete(self, client):
        resp = client.delete(self.WORKOUTS_URL)
        assert resp.status_code == 204
        resp = client.delete(self.WORKOUTS_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_WORKOUTS_URL)
        assert resp.status_code == 404     
    

class TestMaxDataForExercise(object):
    
    RESOURCE_URL = "/api/exercises/Squat/max-data/"
    INVALID_URL = "/api/exercises/sqweuurqweh/max-data/"

    # test GET method and that all methods exist for MaxDataForExercise
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method("workoutlog:add-max-data", client, body, "max_data")
        assert len(body["items"]) == 1
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

        # test get with invalid url
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    # test POST method for MaxDataForExercise
    def test_post(self, client):
        valid = _get_max_data_json()

        # test post with invalid url
        resp = client.post(self.INVALID_URL, data=valid)
        assert resp.status_code == 404
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL + str(valid["order_for_exercise"]) + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        # test that request can be sent without order_for_exercise field
        # in which case it will be auto-generated
        valid.pop("order_for_exercise")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # test with invalid date format
        valid["date"] = "111222"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        
        # remove date field for 400
        valid.pop("date")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestMaxDataItem(object):
    
    RESOURCE_URL = "/api/exercises/Paused%20Squat/max-data/1/"
    INVALID_URL_EXERCISE = "/api/exercises/SWQEQER/max-data/1/"
    INVALID_URL_ORDER = "/api/exercises/Squat/max-data/999/"
    
    # test GET method all methods exist for MaxDataItem
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, "max_data")
        _check_control_delete_method("workoutlog:delete", client, body)

        # test get with invalid urls
        resp = client.get(self.INVALID_URL_EXERCISE)
        assert resp.status_code == 404
        resp = client.get(self.INVALID_URL_ORDER)
        assert resp.status_code == 404

    # test PUT method for MaxDataItem
    def test_put(self, client):
        valid = _get_max_data_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test get with invalid urls
        resp = client.put(self.INVALID_URL_EXERCISE, json=valid)
        assert resp.status_code == 404
        resp = client.put(self.INVALID_URL_ORDER, json=valid)
        assert resp.status_code == 404
        
        # test with valid
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
    
    # test DELETE method for MaxDataItem
    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL_EXERCISE)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL_ORDER)
        assert resp.status_code == 404     
    

class TestWeeklyProgrammingCollection(object):
    
    RESOURCE_URL = "/api/weekly-programming/"

    # test GET method and that all methods exist for WeeklyProgrammingCollection
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_post_method("workoutlog:add-weekly-programming", client, body, "weekly_programming")
        assert len(body["items"]) == 2
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)

    # test POST method for WeeklyProgrammingCollection
    def test_post(self, client):
        valid = _get_weekly_programming_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["Location"].endswith(self.RESOURCE_URL
               + "Main%20lift" + "/" + str(valid["week_number"]) + "/")
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # send string over 100 characters as exercise_type field for 400
        long_string = ""
        for i in range(101):
            long_string += str(i)
        valid["exercise_type"] = long_string
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400

        # remove exercise_type field for 400
        valid.pop("exercise_type")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400


class TestWeeklyProgrammingForExercise(object):
    
    RESOURCE_URL = "/api/exercises/Squat/weekly-programming/"

    # test GET method and that all methods exist for WeeklyProgrammingForExercise
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("up", client, body)
        assert len(body["items"]) == 2
        for item in body["items"]:
            _check_control_get_method("self", client, item)
            _check_control_get_method("profile", client, item)


class TestWeeklyProgrammingItem(object):
    
    RESOURCE_URL = "/api/weekly-programming/Main%20lift/1/"
    INVALID_URL = "/api/weekly-programming/Main%20lift/999/"
    
    # test GET method all methods exist for WeeklyProgrammingItem
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("profile", client, body)
        _check_control_get_method("collection", client, body)
        _check_control_put_method("edit", client, body, "weekly_programming")
        _check_control_delete_method("workoutlog:delete", client, body)

        # test get with invalid url
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    # test PUT method for WeeklyProgrammingItem
    def test_put(self, client):
        valid = _get_weekly_programming_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another weekly programming data entry's week_number
        valid["week_number"] = 2
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid
        valid["week_number"] = 1
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204

        # send string over 100 characters as exercise_type field for 400
        long_string = ""
        for i in range(101):
            long_string += str(i)
        valid["exercise_type"] = long_string
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # remove week_number field for 400
        valid.pop("week_number")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
    
    # test DELETE for WeeklyProgrammingItem
    def test_delete(self, client):
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404     