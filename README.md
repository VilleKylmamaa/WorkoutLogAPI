# PWP SUMMER 2021

The project is for the Programmable Web Summer 2021 course in the University of Oulu.



# PROJECT NAME

Workout Log API



# Group information
Student 1. Ville Kylmämaa, email: ville.kylmamaa@gmail.com

---

This project is a RESTful Web API designed to provide functionalities to build many kinds of workout logs. It offers a robust database structure to store all the useful data from workouts. The API is built with flexibility in mind and so most data columns are nullable so that the client can choose which ones to utilize. It can be used to build workout log applications for either strength/hypertrophy training or cardio training, or both.

The API is implemented with Flask, is a micro web framework written in Python. The database is implemented with SQLite utilizing the SQLAlchemy database toolkit for Python.

An example workout log client utilizing is provided. The client is impolemented with HTML, CSS, JavaScript and jQuery.



# Installation

1. If not already installed, install the newest version of [Python](https://www.python.org/downloads/) and [Pip](https://pypi.org/project/pip/).

2. (Optional) Use [virtual environment](https://docs.python.org/3/tutorial/venv.html). A virtual environment is a private copy of the Python interpreter onto which you can install packages privately, without affecting the global Python interpreter installed in your system. In the root folder, to create the virtual environment, run the command:

```
python3 -m venv venv
```

Then start using the virtual enviroment with the command:

in Windows:

```
venv\Scripts\activate.bat
```

in Mac or Linux:

```
source venv/bin/activate
```


3. Install the project and required libraries (Flask, Flask-RESTful, Flask-SQLAlchemy, SQLAlchemy, etc.). In the root folder, where the setup.py and requirements.txt files are located, run the following command prompt commands:
 
 ```
 pip install -r requirements.txt
 pip install -e
 ```

4. To run the API in localhost run the bat file:

```
start-server.bat
```

or run the following commands:

```
set FLASK_APP=workoutlog
set FLASK_ENV=development
flask run
```

5. To populate the database run the bat file:

```
reset-db.bat
```

Note that it also resets the database, i.e. removes all data entries and repopulates it with test data.

or run the following commands:

```
set FLASK_APP=workoutlog
flask init-db
flask testgen
```


6. API is now running in localhost:5000.

For the API, go to URL: 

>http://localhost:5000/api/

For the client, go to URL:

>http://localhost:5000/workoutlog/



# Running tests

1. Project and the required libraries should be installed. If not, see above in the installment section.

2. To run the tests for the database and the API, in the root folder, either run the bat file:

```
run-tests.bat
```

or run command:

```
pytest --cov-report term-missing --cov=workoutlog
```


# Documentation

[GitHub Wiki](https://github.com/VilleKylmamaa/WorkoutLogAPI/wiki)

[Apiary Documentation](https://workoutlogapi.docs.apiary.io/#)



---

Ville Kylmämaa



