import datetime
from enum import unique
import click
from flask.cli import with_appcontext
from sqlalchemy import desc
from workoutlog import db



#
# Association tables for many-to-many relationships 
#

exercise_workout_association = db.Table("exercise_workout_association",
    db.Column("exercise_id", db.ForeignKey("exercise.id"), primary_key=True),
    db.Column("workout_id", db.ForeignKey("workout.workout_id"), primary_key=True)
)

exercise_programming_association = db.Table("exercise_programming_association",
    db.Column("exercise_id", db.ForeignKey("exercise.id"), primary_key=True),
    db.Column("weekly_programming_id", db.ForeignKey("weekly_programming.id"), primary_key=True)
)


#
# Models
#

class Workout(db.Model):

    workout_id = db.Column(db.Integer, primary_key=True)
    date_time = db.Column(db.DateTime, unique=True, nullable=False)
    duration = db.Column(db.Interval, nullable=True)
    body_weight = db.Column(db.Float, nullable=True)
    average_heart_rate = db.Column(db.Integer, nullable=True)
    max_heart_rate = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(1000), nullable=True)
    
    exercises = db.relationship("Exercise",
        secondary=exercise_workout_association,
        back_populates="workouts"
    )
    sets = db.relationship("Set", 
        cascade="all, delete-orphan", 
        back_populates="workout"
    )
    
    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["date_time"],
        }
        props = schema["properties"] = {}
        props["workout_id"] = {
            "description": "Identifier of the workout",
            "type": "integer"
        }
        props["date_time"] = {
            "description": "Date and time of the workout (YYYY-MM-DD HH:MM)",
            "type": "string"
        }
        props["duration"] = {
            "description": "Duration of the workout (HH:MM)",
            "type": "string"
        }
        props["body_weight"] = {
            "description": "Trainee's body weight during the day of the workout",
            "type": "number"
        }
        props["average_heart_rate"] = {
            "description": "Average heart rate during the workout",
            "type": "integer"
        }
        props["max_heart_rate"] = {
            "description": "Max heart rate during the workout",
            "type": "integer"
        }
        props["notes"] = {
            "description": "Any additional notes about the workout",
            "type": "string"
        }
        return schema


class Exercise(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    exercise_name = db.Column(db.String(100), unique=True, nullable=False)
    exercise_type = db.Column(db.String(100), nullable=True)

    workouts = db.relationship("Workout",
        secondary=exercise_workout_association,
        back_populates="exercises"
    )
    sets = db.relationship("Set",
        cascade="all, delete-orphan",
        back_populates="exercise"
    )
    max_data = db.relationship("MaxData",
        cascade="all, delete-orphan",
        back_populates="exercise"
    )
    weekly_programming = db.relationship("WeeklyProgramming",
        secondary=exercise_programming_association,
        back_populates="exercises"
    )

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["exercise_name"]
        }
        props = schema["properties"] = {}
        props["exercise_name"] = {
            "description": "Name of the exercise",
            "type": "string"
        }
        props["exercise_type"] = {
            "description": "Type of the exercise, for example main lift / variation lift / cardio",
            "type": "string"
        }
        return schema


class Set(db.Model):

    __table_args__ = (db.UniqueConstraint(
        "exercise_id",
        "workout_id",
        "order_in_workout",
        name="_exercise_session_order_uc"), )

    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id",
        ondelete="CASCADE"), nullable=False
    )
    workout_id = db.Column(db.Integer, db.ForeignKey("workout.workout_id",
        ondelete="CASCADE"), nullable=False
    )

    order_in_workout = db.Column(db.Integer, nullable=False)
    weight = db.Column(db.Float, nullable=True)
    number_of_reps = db.Column(db.Integer, nullable=True)
    reps_in_reserve = db.Column(db.Integer, nullable=True)
    rate_of_perceived_exertion = db.Column(db.Float, nullable=True)
    duration = db.Column(db.Interval, nullable=True)
    distance = db.Column(db.Float, nullable=True)

    exercise = db.relationship("Exercise", back_populates="sets")
    workout = db.relationship("Workout", back_populates="sets")

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": []
        }
        props = schema["properties"] = {}
        props["order_in_workout"] = {
            "description": "The set's order number in a workout. Automatic.",
            "type": "integer"
        }
        props["weight"] = {
            "description": "Weight used for the set",
            "type": "number"
        }
        props["number_of_reps"] = {
            "description": "Amount of repetitions achieved during the set",
            "type": "integer"
        }
        props["reps_in_reserve"] = {
            "description": "Amount of reps left in reserve during the set",
            "type": "integer"
        }
        props["rate_of_perceived_exertion"] = {
            "description": "Rate of perceived exertion (RPE) during the set",
            "type": "number"
        }
        props["duration"] = {
            "description": "Duration of the set (HH:MM)",
            "type": "string"
        }
        props["distance"] = {
            "description": "Distance travelled during the set",
            "type": "number"
        }
        return schema

    
class MaxData(db.Model):

    __table_args__ = (db.UniqueConstraint(
        "exercise_id", 
        "order_for_exercise", 
        name="_exercise_order_uc"), )

    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey("exercise.id", ondelete="CASCADE"))
    order_for_exercise = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    training_max = db.Column(db.Float, nullable=True)
    estimated_max = db.Column(db.Float, nullable=True)
    tested_max = db.Column(db.Float, nullable=True)

    exercise = db.relationship("Exercise", back_populates="max_data")

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["date"]
        }
        props = schema["properties"] = {}
        props["order_for_exercise"] = {
            "description": "Order number of the max data for the exercise. Automatic.",
            "type": "integer"
        }
        props["date"] = {
            "description": "Date of the max data",
            "type": "string"
        }
        props["training_max"] = {
            "description": "Training max of the exercise",
            "type": "number"
        }
        props["estimated_max"] = {
            "description": "Estimated max of the exercise",
            "type": "number"
        }
        props["tested_max"] = {
            "description": "Tested max of the exercise",
            "type": "number"
        }
        return schema
    

class WeeklyProgramming(db.Model):

    __table_args__ = (db.UniqueConstraint(
        "week_number",
        "exercise_type",
        name="_week_exercise_uc"), )

    id = db.Column(db.Integer, primary_key=True)
    week_number = db.Column(db.Integer, nullable=False)
    exercise_type = db.Column(db.String(100), nullable=False)
    intensity = db.Column(db.Float, nullable=True)
    number_of_sets = db.Column(db.Integer, nullable=True)
    number_of_reps = db.Column(db.Integer, nullable=True)
    reps_in_reserve = db.Column(db.Integer, nullable=True)
    rate_of_perceived_exertion = db.Column(db.Float, nullable=True)
    duration = db.Column(db.Interval, nullable=True)
    distance = db.Column(db.Float, nullable=True)
    average_heart_rate = db.Column(db.Integer, nullable=True)
    notes = db.Column(db.String(1000), nullable=True)

    exercises = db.relationship("Exercise", secondary=exercise_programming_association,
     back_populates="weekly_programming")

    @staticmethod
    def get_schema():
        schema = {
            "type": "object",
            "required": ["week_number", "exercise_type"]
        }
        props = schema["properties"] = {}
        props["week_number"] = {
            "description": "The week number for which week this programming data is for",
            "type": "integer"
        }
        props["exercise_type"] = {
            "description": "Type of the exercise for which this programming is meant for",
            "type": "string"
        }
        props["intensity"] = {
            "description": "Prescribed intensity of the exercise",
            "type": "number"
        }
        props["number_of_sets"] = {
            "description": "Prescribed number of sets",
            "type": "integer"
        }
        props["number_of_reps"] = {
            "description": "Prescribed number of reps per set",
            "type": "integer"
        }
        props["reps_in_reserve"] = {
            "description": "Prescribed amount of reps that should be left in reserve during a set",
            "type": "integer"
        }
        props["rate_of_perceived_exertion"] = {
            "description": "Prescribed rate of perceived exertion (RPE) for the sets",
            "type": "number"
        }
        props["duration"] = {
            "description": "Prescribed duration of a set or the whole session, mainly for cardio",
            "type": "string"
        }
        props["distance"] = {
            "description": "Prescribed distance traveled during a set or the whole session, mainly for cardio",
            "type": "number"
        }
        props["average_heart_rate"] = {
            "description": "Prescribed average heart rate during a set or the whole session, mainly for cardio",
            "type": "integer"
        }
        props["notes"] = {
            "description": "Any additional notes for this programming data",
            "type": "string"
        }
        return schema




#
# CLI commands for generating test data, deleting tables and creating tables
#

# Inserts Workouts, Exercises, Sets, MaxData and WeeklyProgramming to the database
@click.command("testgen")
@with_appcontext
def insert_initial_data(*args, **kwargs):
    # Week 1
    db.session.add(WeeklyProgramming(
        week_number=1,
        exercise_type="Main lift",
        intensity=70,
        number_of_sets=5,
        number_of_reps=5,
        reps_in_reserve=3
        ))
    db.session.add(WeeklyProgramming(
        week_number=1,
        exercise_type="Variation lift",
        intensity=60,
        number_of_sets=5,
        number_of_reps=7,
        reps_in_reserve=3
        ))
    db.session.add(WeeklyProgramming(
        week_number=1,
        exercise_type="Cardio",
        rate_of_perceived_exertion=6,
        duration=datetime.timedelta(minutes=20)
        ))

    # Week 2
    db.session.add(WeeklyProgramming(
        week_number=2,
        exercise_type="Main lift",
        intensity=75,
        number_of_sets=5,
        number_of_reps=4,
        reps_in_reserve=3
        ))
    db.session.add(WeeklyProgramming(
        week_number=2,
        exercise_type="Variation lift",
        intensity=65,
        number_of_sets=5,
        number_of_reps=6,
        reps_in_reserve=3
        ))
    db.session.add(WeeklyProgramming(
        week_number=2,
        exercise_type="Cardio",
        rate_of_perceived_exertion=6,
        duration=datetime.timedelta(minutes=20)
        ))

    # Week 3
    db.session.add(WeeklyProgramming(
        week_number=3,
        exercise_type="Main lift",
        intensity=80,
        number_of_sets=5,
        number_of_reps=3,
        reps_in_reserve=2
        ))
    db.session.add(WeeklyProgramming(
        week_number=3,
        exercise_type="Variation lift",
        intensity=70,
        number_of_sets=5,
        number_of_reps=5,
        reps_in_reserve=2
        ))
    db.session.add(WeeklyProgramming(
        week_number=3,
        exercise_type="Cardio",
        rate_of_perceived_exertion=7,
        duration=datetime.timedelta(minutes=30)
        ))

    # Week 4
    db.session.add(WeeklyProgramming(
        week_number=4,
        exercise_type="Main lift",
        intensity=72.5,
        number_of_sets=5,
        number_of_reps=5,
        reps_in_reserve=3
        ))
    db.session.add(WeeklyProgramming(
        week_number=4,
        exercise_type="Variation lift",
        intensity=62.5,
        number_of_sets=5,
        number_of_reps=7,
        reps_in_reserve=3
        ))
    db.session.add(WeeklyProgramming(
        week_number=4,
        exercise_type="Cardio",
        rate_of_perceived_exertion=7,
        duration=datetime.timedelta(minutes=30)
        ))

    # Week 5
    db.session.add(WeeklyProgramming(
        week_number=5,
        exercise_type="Main lift",
        intensity=77.5,
        number_of_sets=5,
        number_of_reps=4,
        reps_in_reserve=2
        ))
    db.session.add(WeeklyProgramming(
        week_number=5,
        exercise_type="Variation lift",
        intensity=67.5,
        number_of_sets=5,
        number_of_reps=6,
        reps_in_reserve=2
        ))
    db.session.add(WeeklyProgramming(
        week_number=5,
        exercise_type="Cardio",
        rate_of_perceived_exertion=8,
        duration=datetime.timedelta(minutes=40)
        ))

    # Week 6
    db.session.add(WeeklyProgramming(
        week_number=6,
        exercise_type="Main lift",
        intensity=82.5,
        number_of_sets=5,
        number_of_reps=3,
        reps_in_reserve=1
        ))
    db.session.add(WeeklyProgramming(
        week_number=6,
        exercise_type="Variation lift",
        intensity=72.5,
        number_of_sets=5,
        number_of_reps=5,
        reps_in_reserve=2
        ))
    db.session.add(WeeklyProgramming(
        week_number=6,
        exercise_type="Cardio",
        rate_of_perceived_exertion=8,
        duration=datetime.timedelta(minutes=40)
        ))

    # Workout 1 
    workout_1 = Workout(
        date_time=datetime.datetime(2021, 8, 10, 12),
        duration=datetime.timedelta(hours=1, minutes=15),
        body_weight=71.3,
        average_heart_rate=100,
        max_heart_rate=125,
        notes="Easy session"
        )
    db.session.add(workout_1)
    
    squat = Exercise(
        exercise_name="Squat",
        exercise_type="Main lift",
        workouts=[workout_1]
        )
    db.session.add(squat)
    
    bench = Exercise(
        exercise_name="Bench Press",
        exercise_type="Main lift",
        workouts=[workout_1]
        )
    db.session.add(bench)

    row = Exercise(
        exercise_name="Barbell Row",
        exercise_type="Main lift",
        workouts=[workout_1]
        )
    db.session.add(row)

    for i in range(4):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=100,
            number_of_reps=5,
            reps_in_reserve=4-i,
            exercise=squat,
            workout=workout_1
        ))

    for i in range(4):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=65,
            number_of_reps=8,
            reps_in_reserve=4-i,
            exercise=bench,
            workout=workout_1
        ))

    for i in range(4):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=70,
            number_of_reps=10,
            reps_in_reserve=4-i,
            exercise=row,
            workout=workout_1
        ))


    # Workout 2
    workout_2 = Workout(
        date_time=datetime.datetime(2021, 8, 12, 14),
        duration=datetime.timedelta(hours=1, minutes=30),
        body_weight=71.6,
        average_heart_rate=115,
        max_heart_rate=155,
        notes="Hard session"
        )
    db.session.add(workout_2)
    
    deadlift = Exercise(
        exercise_name="Deadlift",
        exercise_type="Main lift",
        workouts=[workout_2]
        )
    db.session.add(deadlift)
    
    ohp = Exercise(
        exercise_name="Overhead Press",
        exercise_type="Main lift",
        workouts=[workout_2]
        )
    db.session.add(ohp)

    for i in range(5):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=140,
            number_of_reps=5,
            reps_in_reserve=5-i,
            exercise=deadlift,
            workout=workout_2
            ))

    for i in range(5):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=47.5,
            number_of_reps=5,
            reps_in_reserve=5-i,
            exercise=ohp,
            workout=workout_2
            ))

    # Workout 3
    workout_3 = Workout(
        date_time=datetime.datetime(2021, 8, 14, 16),
        duration=datetime.timedelta(hours=1, minutes=0),
        body_weight=71.4,
        average_heart_rate=120,
        max_heart_rate=150,
        exercises=[squat, bench]
        )

    for i in range(5):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=105,
            number_of_reps=4,
            reps_in_reserve=5-i,
            exercise=squat,
            workout=workout_3
            ))
            
    for i in range(5):
        db.session.add(Set(
            order_in_workout=1+i,
            weight=70,
            number_of_reps=4,
            reps_in_reserve=5-i,
            exercise=bench,
            workout=workout_3
        ))


    # Max data
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=1,
        date=datetime.datetime(2020, 10, 10, 14),
        estimated_max=110
        ))
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=2,
        date=datetime.datetime(2020, 12, 14, 16),
        estimated_max=125
        ))
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=3,
        date=datetime.datetime(2021, 2, 14, 16),
        estimated_max=120
        ))
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=4,
        date=datetime.datetime(2021, 4, 14),
        estimated_max=130
        ))
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=5,
        date=datetime.datetime(2021, 6, 14),
        estimated_max=132.5
        ))
    db.session.add(MaxData(
        exercise=squat,
        order_for_exercise=6,
        date=datetime.datetime(2021, 8, 14),
        estimated_max=145
        ))

    db.session.add(MaxData(
        exercise=bench,
        order_for_exercise=1,
        date=datetime.datetime(2021, 6, 10),
        estimated_max=85
        ))
    db.session.add(MaxData(
        exercise=bench,
        order_for_exercise=2,
        date=datetime.datetime(2021, 8, 10),
        estimated_max=90
        ))

    db.session.add(MaxData(
        exercise=deadlift,
        order_for_exercise=1,
        date=datetime.datetime(2021, 8, 12),
        training_max=180
        ))
    db.session.add(MaxData(
        exercise=ohp,
        order_for_exercise=1,
        date=datetime.datetime(2021, 8, 12),
        training_max=60
        ))

    db.session.commit()


# Deletes the database
@click.command("delete-db")
@with_appcontext
def delete_db_command():
    db.drop_all()

# Initializes the database
@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
