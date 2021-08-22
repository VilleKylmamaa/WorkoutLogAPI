from flask import Blueprint
from flask_restful import Api

from workoutlog.resources.workout import WorkoutCollection, WorkoutsByExercise, WorkoutItem
from workoutlog.resources.exercise import ExerciseCollection, ExercisesWithinWorkout, ExerciseItem
from workoutlog.resources.set import SetsWithinWorkout, SetItem
from workoutlog.resources.weekly_programming import WeeklyProgrammingCollection, WeeklyProgrammingForExercise, WeeklyProgrammingItem
from workoutlog.resources.max_data import MaxDataForExercise, MaxDataItem

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

api.add_resource(WorkoutCollection, "/workouts/")
api.add_resource(WorkoutsByExercise, "/exercises/<exercise_name>/workouts/")
    
# Two paths for the same resource
api.add_resource(WorkoutItem,
    "/workouts/<workout_id>/",
    "/exercises/<exercise_name>/workouts/<workout_id>/"
    )

api.add_resource(ExerciseCollection, "/exercises/")
api.add_resource(ExercisesWithinWorkout, "/workouts/<workout_id>/exercises/")

# Two paths for the same resource
api.add_resource(ExerciseItem,
    "/exercises/<exercise_name>/",
    "/workouts/<workout_id>/exercises/<exercise_name>/",
    )

# Two paths for the same resource
# Endpoints are used to differentiate the paths because the keywords are the
# same, just in a different order.
api.add_resource(SetsWithinWorkout, "/workouts/<workout_id>/exercises/<exercise_name>/sets/", endpoint="sets_workouts_path")
api.add_resource(SetsWithinWorkout, "/exercises/<exercise_name>/workouts/<workout_id>/sets/", endpoint="sets_exercises_path")

# Two paths for the same resource
# Endpoints are used to differentiate the paths because the keywords are the
# same, just in a different order.
api.add_resource(SetItem, "/workouts/<workout_id>/exercises/<exercise_name>/sets/<order_in_workout>/", endpoint="set_workouts_path")
api.add_resource(SetItem, "/exercises/<exercise_name>/workouts/<workout_id>/sets/<order_in_workout>/", endpoint="set_exercises_path")

api.add_resource(MaxDataForExercise, "/exercises/<exercise_name>/max-data/")
api.add_resource(MaxDataItem, "/exercises/<exercise_name>/max-data/<order_for_exercise>/")

api.add_resource(WeeklyProgrammingCollection, "/weekly-programming/")
api.add_resource(WeeklyProgrammingForExercise, "/exercises/<exercise_name>/weekly-programming/")
api.add_resource(WeeklyProgrammingItem,
    "/weekly-programming/<exercise_type>/<week_number>/",
    "/exercises/<exercise_name>/weekly-programming/<exercise_type>/<week_number>/",)