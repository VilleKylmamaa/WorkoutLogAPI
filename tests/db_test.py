import os
import pytest
import tempfile
import datetime
import click
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection
from sqlalchemy.exc import IntegrityError

from workoutlog import create_app, db
from workoutlog.models import Workout, Exercise, Set, MaxData, WeeklyProgramming


# Enforce foreign key constraints
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    cursor.close()

# Based on http://flask.pocoo.org/docs/1.0/testing/
# and course material example
@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        
    yield app
    
    os.close(db_fd)
    os.unlink(db_fname)


def _get_workout(date_time=datetime.datetime(2021, 8, 5, 11, 30)):
    return Workout(
        date_time=date_time,
        duration=datetime.timedelta(hours=1, minutes=20),
        body_weight=71.5,
        average_heart_rate=110,
        max_heart_rate=150,
        notes="test session"
    )

def _get_exercise():
    return Exercise(
        exercise_name="Squat",
        exercise_type="Main lift"
    )
    
def _get_set(exer, workout):
    return Set(
        order_in_workout=1,
        weight=100,
        number_of_reps=8,
        reps_in_reserve=2,
        rate_of_perceived_exertion=8,
        duration=datetime.timedelta(seconds=30),
        distance=0,
        exercise=exer,
        workout=workout
    )

def _get_max_data_1(exer):
    return MaxData(
        order_for_exercise=1,
        date_time=datetime.datetime(2021, 8, 5),
        training_max=120,
        estimated_max=150,
        tested_max=140,
        exercise=exer
    )

def _get_max_data_2(exer):
    return MaxData(
        order_for_exercise=2,
        date_time=datetime.datetime(2021, 8, 6),
        training_max=120,
        estimated_max=150,
        tested_max=140,
        exercise=exer
    )

def _get_weekly_programming():
    return WeeklyProgramming(
        week_number=1,
        exercise_type="Main lift",
        intensity=70,
        number_of_sets=5,
        number_of_reps=5,
        reps_in_reserve=3,
        rate_of_perceived_exertion=7,
        duration=datetime.timedelta(hours=1, minutes=20),
        distance=0,
        average_heart_rate=100,
        notes="test programming"
    )

def test_create_instances(app):
    """
    Tests that we can create one instance of each model and save them to the
    database using valid values for all columns. After creation, test that 
    everything can be found from database, and that all relationships have been
    saved correctly.
    """
    
    with app.app_context():
        # Create everything
        workout = _get_workout()
        exercise = _get_exercise()
        set = _get_set(exercise, workout)
        max_data = _get_max_data_1(exercise)
        weekly_programming = _get_weekly_programming()

        workout.exercises.append(exercise)
        exercise.weekly_programming.append(weekly_programming)

        db.session.add(workout)
        db.session.add(exercise)
        db.session.add(set)
        db.session.add(max_data)
        db.session.add(weekly_programming)
        db.session.commit()
        
        # Check that everything exists
        assert Workout.query.count() == 1
        assert Exercise.query.count() == 1
        assert Set.query.count() == 1
        assert MaxData.query.count() == 1
        assert WeeklyProgramming.query.count() == 1
        db_workout = Workout.query.first()
        db_exercise = Exercise.query.first()
        db_set = Set.query.first()
        db_max_data = MaxData.query.first()
        db_weekly_programming = WeeklyProgramming.query.first()
        
        # Check all relationships (both sides)
        assert db_workout in db_exercise.workouts
        assert db_exercise in db_workout.exercises
        assert db_set in db_exercise.sets
        assert db_set.exercise == db_exercise
        assert db_set in db_workout.sets
        assert db_set.workout == db_workout
        assert db_max_data in db_exercise.max_data
        assert db_max_data.exercise == db_exercise
        assert db_weekly_programming in db_exercise.weekly_programming
        assert db_exercise in db_weekly_programming.exercises

def test_set_ondelete_exercise(app):
    """
    Tests that Set gets deleted by foreign key cascade when the Exercise
    is deleted
    """
    
    with app.app_context():
        workout = _get_workout()
        exercise = _get_exercise()
        set_1 = _get_set(exercise, workout)
        set_2 = _get_set(exercise, workout)
        set_2.order_in_workout = 2

        db.session.add(workout)
        db.session.add(exercise)
        db.session.add(set_1)
        db.session.add(set_2)
        db.session.commit()
        assert Set.query.count() == 2

        db.session.delete(Exercise.query.first())
        db.session.commit()
        
        assert Exercise.query.first() is None
        assert Set.query.count() == 0

def test_set_ondelete_workout(app):
    """
    Tests that all Sets for the WorkoutSession get deleted by foreign key
    cascade when the WorkoutSession is deleted
    """
    
    with app.app_context():
        workout = _get_workout()
        exercise = _get_exercise()
        set_1 = _get_set(exercise, workout)
        set_2 = _get_set(exercise, workout)
        set_2.order_in_workout = 2
        db.session.add(exercise)
        db.session.commit()
        assert Set.query.count() == 2

        db.session.delete(Workout.query.first())
        db.session.commit()
        assert Workout.query.first() is None
        assert Set.query.count() == 0

def test_max_data_ondelete_exercise(app):
    """ 
    Tests that all MaxData for the Exercise gets deleted by foreign key cascade
    when the Exercise is deleted
    """
    
    with app.app_context():
        exercise = _get_exercise()
        _get_max_data_1(exercise)
        _get_max_data_2(exercise)
        db.session.add(exercise)
        db.session.commit()
        assert MaxData.query.count() == 2

        db.session.delete(Exercise.query.first())
        db.session.commit()
        assert Exercise.query.first() is None
        assert MaxData.query.count() == 0

def test_workout_columns(app):
    """
    Tests Workout columns' non-nullable and unique restrictions
    """
    
    with app.app_context():
        # Tests that date_time is non-nullable
        workout = _get_workout()
        workout.date_time = None
        db.session.add(workout)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that date_time is unique
        workout_1 = _get_workout()
        workout_2 = _get_workout()
        db.session.add(workout_1)  
        db.session.add(workout_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that nullable columns are nullable
        workout = _get_workout()
        workout.duration = None
        workout.body_weight = None
        workout.average_heart_rate = None
        workout.max_heart_rate = None
        workout.notes = None
        db.session.add(workout)
        db.session.commit()
        assert Workout.query.first() == workout

def test_exercise_columns(app):
    """
    Tests Exercise columns' non-nullable and unique restrictions
    """
    
    with app.app_context():
        # Tests that exercise_name is non-nullable
        exercise = _get_exercise()
        exercise.exercise_name = None
        db.session.add(exercise)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that exercise_name is unique
        exercise_1 = _get_exercise()
        exercise_2 = _get_exercise()
        db.session.add(exercise_1)  
        db.session.add(exercise_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that nullable columns are nullable
        exercise = _get_exercise()
        exercise.exercise_type = None
        db.session.add(exercise)
        db.session.commit()
        assert Exercise.query.first() == exercise
        
def test_set_columns(app):
    """
    Tests Set columns' non-nullable and unique restrictions
    """
    
    with app.app_context():
        # Tests that order_in_workout is unique
        workout = _get_workout()
        exercise = _get_exercise()
        set_1 = _get_set(exercise, workout)
        set_2 = _get_set(exercise, workout)
        db.session.add(set_1)  
        db.session.add(set_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that order_in_workout for two different exercises in the same
        # workout doesn't violate uniqueness restriction
        workout = _get_workout()
        exercise_1 = _get_exercise()
        exercise_2 = _get_exercise()
        exercise_2.exercise_name = "Deadlift"
        set_1 = _get_set(exercise_1, workout)
        set_2 = _get_set(exercise_2, workout)
        db.session.add(set_1)
        db.session.add(set_2)
        assert Set.query.count() == 2
        
        db.session.rollback()

        # Tests that order_in_workout for the same exercise in two different
        # workouts doesn't violate uniqueness restriction
        workout_1 = _get_workout()
        workout_2 = _get_workout(datetime.datetime(2021, 8, 6, 11, 30))
        exercise = _get_exercise()
        set_1 = _get_set(exercise, workout_1)
        set_2 = _get_set(exercise, workout_2)
        db.session.add(set_1)
        db.session.add(set_2)
        assert Set.query.count() == 2
        
        db.session.rollback()
        
        # Tests that nullable columns are nullable
        workout = _get_workout()
        exercise = _get_exercise()
        set = _get_set(exercise, workout)
        set.weight = None
        set.number_of_reps = None
        set.reps_in_reserve = None
        set.rate_of_perceived_exertion = None
        set.duration = None
        set.distance = None
        db.session.add(set)
        db.session.commit()
        assert Set.query.first() == set

def test_max_data_columns(app):
    """
    Tests MaxData columns' non-nullable and unique restrictions
    """
    
    with app.app_context():
        # Tests that order_for_exercise is non-nullable
        exercise = _get_exercise()
        max_data = _get_max_data_1(exercise)
        max_data.order_for_exercise = None
        db.session.add(max_data)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()
        # Tests that date_time is non-nullable
        exercise = _get_exercise()
        max_data = _get_max_data_1(exercise)
        max_data.date_time = None
        db.session.add(max_data)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that the combination of exercise_id and order_for_exercise is unique
        exercise = _get_exercise()
        _get_max_data_1(exercise)
        _get_max_data_1(exercise)
        db.session.add(exercise)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that order_for_exercise alone doesn't violate uniqueness restriction
        exercise_1 = _get_exercise()
        exercise_2 = _get_exercise()
        exercise_2.exercise_name = "Deadlift"
        _get_max_data_1(exercise_1)
        _get_max_data_1(exercise_2)
        db.session.add(exercise_1)
        db.session.add(exercise_2)
        assert MaxData.query.count() == 2
        
        db.session.rollback()

        # Tests that nullable columns are nullable
        exercise = _get_exercise()
        max_data = _get_max_data_1(exercise)
        max_data.training_max = None
        max_data.estimated_max = None
        max_data.tested_max = None
        db.session.add(max_data)
        db.session.commit()
        assert max_data.query.first() == max_data


def test_weekly_programming_columns(app):
    """
    Tests WeeklyProgramming columns' non-nullable and unique restrictions
    """
    
    with app.app_context():
        # Tests that week_number is non-nullable
        weekly_programming = _get_weekly_programming()
        weekly_programming.week_number = None
        db.session.add(weekly_programming)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that exercise_type is non-nullable
        weekly_programming = _get_weekly_programming()
        weekly_programming.exercise_type = None
        db.session.add(weekly_programming)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that the combination of week_number and exercise_type is unique
        weekly_programming_1 = _get_weekly_programming()
        weekly_programming_2 = _get_weekly_programming()
        db.session.add(weekly_programming_1)  
        db.session.add(weekly_programming_2)
        with pytest.raises(IntegrityError):
            db.session.commit()
        
        db.session.rollback()

        # Tests that week_number alone doesn't violate uniqueness restriction
        weekly_programming_1 = _get_weekly_programming()
        weekly_programming_2 = _get_weekly_programming()
        weekly_programming_2.exercise_type = "Variation"
        db.session.add(weekly_programming_1)  
        db.session.add(weekly_programming_2)
        assert WeeklyProgramming.query.count() == 2
        
        db.session.rollback()

        # Tests that exercise_type alone doesn't violate uniqueness restriction
        weekly_programming_1 = _get_weekly_programming()
        weekly_programming_2 = _get_weekly_programming()
        weekly_programming_2.week_number = 2
        db.session.add(weekly_programming_1)  
        db.session.add(weekly_programming_2)
        assert WeeklyProgramming.query.count() == 2
        
        db.session.rollback()

        # Tests that nullable columns are nullable
        weekly_programming = _get_weekly_programming()
        weekly_programming.intensity = None
        weekly_programming.number_of_reps = None
        weekly_programming.number_of_sets = None
        weekly_programming.reps_in_reserve = None
        weekly_programming.rate_of_perceived_exertion = None
        weekly_programming.duration = None
        weekly_programming.distance = None
        weekly_programming.average_heart_rate = None
        weekly_programming.notes = None
        db.session.add(weekly_programming)
        db.session.commit()
        assert WeeklyProgramming.query.first() == weekly_programming