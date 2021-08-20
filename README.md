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

1. Starting with version 3.3 of Python, all the necessary tools should be automatically included. In case they are not, you need to install [Pip](https://pypi.org/project/pip/).

2. Install required packages (Flask, Flask-RESTful, Flask-SQLAlchemy, SQLAlchemy) by running the command prompt command
 >'''pip install -e'''
in the root folder, where the file setup.py is located.

3. To run the API server in localhost, in the root folder, either run the bat file:

>start-development-server.bat

or run commands:

>set FLASK_APP=workoutlog
>
>set FLASK_ENV=development
>
>flask run

4. In a web browser, for the API, go to URL: 

>http://localhost:5000/api/

5. In a web browser, for the client, go to URL:

>http://localhost:5000/workoutlog/



# Running tests

To run the tests for the database and the API, in the root folder, either run the bat file:

>run-tests.bat

or run command:

>pytest --cov-report term-missing --cov=workoutlog




# Documentation

[GitHub Wiki](https://github.com/VilleKylmamaa/WorkoutLogAPI/wiki)

[Apiary Documentation](https://workoutlogapi.docs.apiary.io/#)





