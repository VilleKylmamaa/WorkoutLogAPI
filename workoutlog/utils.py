import json
from flask import Response, request, url_for
from workoutlog.constants import *
from workoutlog.models import *


# MasonBuilder from course material
class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.
        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.
        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.
        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

class WorkoutLogBuilder(MasonBuilder):

    ### GET convenience functions ###

    def add_control_get_workouts(self):
        self.add_control(
            "workoutlog:workouts-all",
            url_for("api.workoutcollection"),
            method="GET",
            title="Get all workouts in the database"
        )

    def add_control_get_exercises(self):
        self.add_control(
            "workoutlog:exercises-all",
            url_for("api.exercisecollection"),
            method="GET",
            title="Get all exercises in the database"
        )

    def add_control_get_weekly_programming_all(self):
        self.add_control(
            "workoutlog:weekly-programming-all",
            url_for("api.weeklyprogrammingcollection"),
            method="GET",
            title="Get all weekly programming data in the database"
        )

    def add_control_get_exercises_within_workout(self, workout_id):
        self.add_control(
            "workoutlog:exercises-within-workout",
            url_for("api.exerciseswithinworkout", workout_id=workout_id),
            method="GET",
            title="Get all exercises done within this workout"
        )

    def add_control_get_workouts_by_exercise(self, exercise_name):
        self.add_control(
            "workoutlog:workouts-by-exercise",
            url_for("api.workoutsbyexercise", exercise_name=exercise_name),
            method="GET",
            title="Get all workouts in which this exercise has been done"
        )

    def add_control_get_max_data_for_exercise(self, exercise_name):
        self.add_control(
            "workoutlog:max-data-for-exercise",
            url_for("api.maxdataforexercise", exercise_name=exercise_name),
            method="GET",
            title="Get all max data for this exercise"
        )

    def add_control_get_weekly_programming_for_exercise(self, exercise_name):
        self.add_control(
            "workoutlog:weekly-programming-for-exercise",
            url_for("api.weeklyprogrammingforexercise", exercise_name=exercise_name),
            method="GET",
            title="Get all weekly programming data for this exercise"
        )


    ### POST convenience functions ###

    def add_control_add_workout(self):
        self.add_control(
            "workoutlog:add-workout",
            url_for("api.workoutcollection"),
            method="POST",
            encoding="json",
            title="Add a new workout",
            schema=Workout.get_schema()
        )
    
    def add_control_add_exercise(self):
        self.add_control(
            "workoutlog:add-exercise",
            url_for("api.exercisecollection"),
            method="POST",
            encoding="json",
            title="Add a new exercise",
            schema=Exercise.get_schema()
        )
    
    def add_control_add_exercise_to_workout(self, workout_id):
        self.add_control(
            "workoutlog:add-exercise-to-workout",
            url_for("api.exerciseswithinworkout", workout_id=workout_id),
            method="POST",
            encoding="json",
            title="Add a new exercise to this workout",
            schema=Exercise.get_schema()
        )
    
    def add_control_add_set(self, workout_id, exercise_name):
        self.add_control(
            "workoutlog:add-set",
            url_for(
                "api.sets_workouts_path",
                workout_id=workout_id, 
                exercise_name=exercise_name
            ),
            method="POST",
            encoding="json",
            title="Add a new set",
            schema=Set.get_schema()
        )
    
    def add_control_add_max_data(self, exercise_name):
        self.add_control(
            "workoutlog:add-max-data",
            url_for("api.maxdataforexercise", exercise_name=exercise_name),
            method="POST",
            encoding="json",
            title="Add a new max data entry",
            schema=MaxData.get_schema()
        )
    
    def add_control_add_weekly_programming(self):
        self.add_control(
            "workoutlog:add-weekly-programming",
            url_for("api.weeklyprogrammingcollection"),
            method="POST",
            encoding="json",
            title="Add a new weekly programming data entry",
            schema=WeeklyProgramming.get_schema()
        )


    ### PUT convenience functions ###

    def add_control_edit_workout(self, workout_id):
        self.add_control(
            "edit",
            url_for("api.workoutitem", workout_id=workout_id),
            method="PUT",
            encoding="json",
            title="Edit this workout",
            schema=Workout.get_schema()
        )
        
    def add_control_edit_exercise(self, exercise_name):
        self.add_control(
            "edit",
            url_for("api.exerciseitem", exercise_name=exercise_name),
            method="PUT",
            encoding="json",
            title="Edit this exercise",
            schema=Exercise.get_schema()
        )
        
    def add_control_edit_set_workouts_path(self, workout_id, exercise_name, order_in_workout):
        self.add_control(
            "edit",
            url_for("api.set_workouts_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=order_in_workout
                ),
            method="PUT",
            encoding="json",
            title="Edit this set",
            schema=Set.get_schema()
        )

    def add_control_edit_set_exercises_path(self, workout_id, exercise_name, order_in_workout):
        self.add_control(
            "edit",
            url_for("api.set_exercises_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=order_in_workout),
            method="PUT",
            encoding="json",
            title="Edit this set",
            schema=Set.get_schema()
        )
        
    def add_control_edit_max_data(self, exercise_name, order_for_exercise):
        self.add_control(
            "edit",
            url_for("api.maxdataitem",
                exercise_name=exercise_name,
                order_for_exercise=order_for_exercise
                ),
            method="PUT",
            encoding="json",
            title="Edit this max data entry",
            schema=MaxData.get_schema()
        )
        
    def add_control_edit_weekly_programming(self, exercise_type, week_number):
        self.add_control(
            "edit",
            url_for("api.weeklyprogrammingitem",
                exercise_type=exercise_type,
                week_number=week_number
                ),
            method="PUT",
            encoding="json",
            title="Edit this weekly programming entry",
            schema=WeeklyProgramming.get_schema()
        )
    

    ### DELETE convenience functions ###

    def add_control_delete_workout(self, workout_id):
        self.add_control(
            "workoutlog:delete",
            url_for("api.workoutitem", workout_id=workout_id),
            method="DELETE",
            title="Delete this workout"
        )
    
    def add_control_delete_exercise(self, exercise_name):
        self.add_control(
            "workoutlog:delete",
            url_for("api.exerciseitem", exercise_name=exercise_name),
            method="DELETE",
            title="Delete this exercise"
        )
    
    def add_control_delete_exercise_from_workout(self, workout_id, exercise_name):
        self.add_control(
            "workoutlog:delete-from-workout",
            url_for("api.exerciseitem", workout_id=workout_id, exercise_name=exercise_name),
            method="DELETE",
            title="Remove this exercise from this workout"
        )

    def add_control_delete_set_workouts_path(self, workout_id, exercise_name, order_in_workout):
        self.add_control(
            "workoutlog:delete",
            url_for("api.set_workouts_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=order_in_workout),
            method="DELETE",
            title="Delete this set"
        )

    def add_control_delete_set_exercises_path(self, workout_id, exercise_name, order_in_workout):
        self.add_control(
            "workoutlog:delete",
            url_for("api.set_exercises_path",
                workout_id=workout_id,
                exercise_name=exercise_name,
                order_in_workout=order_in_workout),
            method="DELETE",
            title="Delete this set"
        )

    def add_control_delete_max_data(self, exercise_name, order_for_exercise):
        self.add_control(
            "workoutlog:delete",
            url_for("api.maxdataitem",
                exercise_name=exercise_name,
                order_for_exercise=order_for_exercise),
            method="DELETE",
            title="Delete this workout"
        )

    def add_control_delete_weekly_programming(self, exercise_type, week_number):
        self.add_control(
            "workoutlog:delete",
            url_for(
                "api.weeklyprogrammingitem",
                exercise_type=exercise_type,
                week_number=week_number
            ),
            method="DELETE",
            title="Delete this weekly programming data"
        )


"""
Creates an error message in Mason format
"""
def create_error_response(status_code, title, message=None):
    resource_url = request.path
    body = MasonBuilder(resource_url=resource_url)
    body.add_error(title, message)
    body.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(body, indent=4), status_code, mimetype=MASON)

"""
Turns timedelta object to a string for the purpose of making it JSON serializable.
frmt should be a string with timedelta arguments given in {} brackets.

Source: https://stackoverflow.com/questions/8906926/formatting-timedelta-objects
"""
def strfTimedelta(timedelta, frmt):
    if timedelta == None:
        return None
    else:
        days = {"days": timedelta.days}
        days["hours"], remainder = divmod(timedelta.seconds, 3600)
        days["minutes"], days["seconds"] = divmod(remainder, 60)
        return frmt.format(**days)