"use strict";

const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

/**
 * Functions for rendering different types of messages from the course material
 */
function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"]
    $("div.notification").html("<p class='error'>" + msg + "</p>");
}

function renderMsg(msg) {
    $("div.notification").html("<p class='msg'>" + msg + "</p>");
}

/**
 * Ajax get convenience function from the course material
 */
function getResource(href, renderer) {
    return $.ajax({
        url: href,
        success: renderer,
        error: renderError,
        async: false // Temporary, fix show workout page
    });
}


/**
 * Ajax send data convenience function from the course material
 */
function sendData(href, method, item, postProcessor) {
    return $.ajax({
        url: href,
        type: method,
        data: JSON.stringify(item),
        contentType: PLAINJSON,
        processData: false,
        success: postProcessor,
        error: renderError
    });
}

/**
 * Prevents default behaviour from links, such as link opening a web page,
 * and instead sends the link to a renderer function, from the course material
 */
 function followLink(event, a, renderer) {
    event.preventDefault();
    getResource($(a).attr("href"), renderer);
}



/***** Submit functions for preparing data to be sent to sendData() *****/

function submitWorkout(event) {
    event.preventDefault();

    let data = {};
    let form = $(".content form");
    data.date_time = $("input[name='date_time']").val();
    data.duration = $("input[name='duration']").val();
    data.body_weight = parseFloat($("input[name='body_weight']").val());
    data.average_heart_rate = parseFloat($("input[name='average_heart_rate']").val());
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedWorkout);
}

function getSubmittedWorkout(data, status, jqxhr) {
    renderMsg("Success");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, renderWorkout);
    }
}

function submitExercise(event) {
    event.preventDefault();

    let data = {};
    let form = $(".content form.exercise_form");
    data.exercise_name = $("input[name='exercise_name']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedExercise);
}

function getSubmittedExercise(data, status, jqxhr) {
    renderMsg("Exercise added");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, getExercisesWithinWorkoutLink);
    }
}

function getExercisesWithinWorkoutLink(body) {
    getResource(body["@controls"].collection.href, reRenderWorkout);
}

function reRenderWorkout(body) {
    getResource(body["@controls"].up.href, renderWorkout);
}

function submitSet(event) {
    event.preventDefault();

    // There are multiple forms on the same page for the different exercises.
    // Get id of the form with event.target.id to get the right data
    let form = $("#" + event.target.id);
    let form_id = form.attr("id");
    let data = {};
    data.weight = parseFloat($("#" + form_id + " input[name='weight']").val());
    data.number_of_reps = parseInt($("#" + form_id + " input[name='reps']").val());
    data.reps_in_reserve = parseInt($("#" + form_id + " input[name='rir']").val());

    // Give ID to the correct table where the set will be appended
    $("#" + form_id).prev().attr("id", "new_set_target");

    sendData(form.attr("action"), form.attr("method"), data, getSubmittedSet);
}

function getSubmittedSet(data, status, jqxhr) {
    console.log(data);
    renderMsg("Set added");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendSetRow);
    }
}

function appendSetRow(body) {
    $("#new_set_target").append(setRow(body));
    $("#new_set_target").removeAttr('id'); // Remove the ID after the addition
}



/***** Delete functions *****/

function deleteWorkout(body) {
    sendData(
        body["@controls"]["workoutlog:delete"].href,
        body["@controls"]["workoutlog:delete"].method
        ).done(function() {
            getResource(
                body["@controls"].collection.href,
                renderWorkouts
            )
        });
}


/* 
var self_link = "<a href='" + item["@controls"].self.href +
"' onClick='followLink(event, this, renderWorkout)'>show</a><br>";
 */

/***** Functions for rendering Workouts pages *****/

function renderNavigation(page) {
    $("div.navbar-nav").html(
        "<a id='workouts' class='nav-item nav-link' href='/api/workouts/' " + 
        "onClick='followLink(event, this, renderWorkouts)'>Workouts</a>" +
        "<a id='exercises' class='nav-item nav-link' href='/api/exercises/' " + 
        "onClick='followLink(event, this, renderExercises)'>Exercises</a>" +
        "<a id='program' class='nav-item nav-link' href='/api/weekly-programming/'" + 
        "onClick='followLink(event, this, renderProgramming)'>Training Program</a>");
    if (page === "workouts") {
        $(".nav-item").removeClass("active");
        $("#workouts").addClass("active");
    } else if (page === "exercises") {
        $(".nav-item").removeClass("active");
        $("#exercises").addClass("active");
    } else if (page === "program") {
        $(".nav-item").removeClass("active");
        $("#program").addClass("active");
    }
}

function renderTableForWorkouts() {
    $(".content").append(
        "<div class='workouts'>" +
            "<table class='workouts_table table table-striped wrapper table-dark bg-dark'>" +
                "<thead></thead>" +
                "<tbody></tbody>" +
            "</table>" +
            "<div class='form'></div>" +
        "</div>"
    );
    $(".workouts_table thead").last().append(
        "<tr>" +
            "<th>Date</th>" +
            "<th>Duration</th>" +
            "<th>Body Weight (kg)</th>" +
            "<th>Average Heart Rate</th>" +
            "<th>Action</th>" +
        "</tr>"
    );
}

function workoutRow(item, switch_actions) {
    var self_link = "<a href='" + item["@controls"].self.href +
        "' onClick='followLink(event, this, renderWorkout)'>show</a><br>";
    if (switch_actions === "switch_actions") {
        self_link = "";
    }
    
    var edit_link = "";
    if (switch_actions === "switch_actions") {
        edit_link = "<a href='" + item["@controls"].self.href +
        "' onClick='followLink(event, this, renderWorkoutEditPage)'>edit</a><br>";
    }

    var delete_link = "<a href='" +
        item["@controls"]["workoutlog:delete"].href +
        "' onClick='followLink(event, this," +
        "deleteWorkout)'>delete</a>";
    
    return "<tr>" +
            "<th>" + item.date_time + "</th>" +
            "<td>" + item.duration + "</td>" +
            "<td>" + item.body_weight + "</td>" +
            "<td>" + item.average_heart_rate + "</td>" +
            "<td>" + self_link + edit_link + delete_link + "</td>" +
            "</tr>";
}

function setRow(item) {
    return "<tr>" +
            "<th>" + item.order_in_workout + "</th>" +
            "<td>" + item.weight + "</td>" +
            "<td>" + item.number_of_reps + "</td>" +
            "<td>" + item.reps_in_reserve + "</td>" +
            "</tr>";
}

function renderWorkouts(body) {
    renderNavigation("workouts");
    let content = $(".content");
    $(".notification").empty();
    content.empty();
    content.append("<h1>Workouts</h1>");

    // Workouts table
    renderTableForWorkouts();
    $(".workouts_table tbody").empty();
    body.items.forEach(function (item) {
        $(".workouts_table tbody").append(workoutRow(item));
    });

    // Workout form
    content.append("<hr>");
    content.append("<h2>Add New Workout</h2>");
    renderWorkoutForm(body["@controls"]["workoutlog:add-workout"]);
}

function renderWorkout(body) {
    let content = $(".content");
    content.empty();
    $(".notification").empty();

    // Back button
    let link = body["@controls"].collection.href;
    content.append("<div class='text-center'><a class='btn btn-dark' href='' " +
                  "onClick='followLink(event, '" + link + "', renderWorkout)'>" +
                  "Back to Workouts</a></div>");

    // Workouts table
    content.append("<h1>" + body.date_time + "<h2>");
    renderTableForWorkouts();
    $(".workouts_table tbody").append(workoutRow(body, "switch_actions"));

    getResource(
        body["@controls"]["workoutlog:exercises-within-workout"].href,
        renderExercisesWithinWorkout
    );
}

function renderExercisesWithinWorkout(body) {
    let content = $(".content");
    
    // If there are no exercises yet, render just the add exercise form
    if (body.items.length > 0){
        // Work around the asynchronous nature of ajax calls
        content.append("<h3>" + body.items[0].exercise_name + "</h3>");
        renderTableForSets();
        let i = 1;
        body.items.forEach(function (item) {
            getResource(
                item["@controls"]["workoutlog:sets-within-workout"].href,
                renderSets
            ).done(function() {
                if (i < body.items.length) {
                    let this_exercise = body.items[i].exercise_name;
                    content.append("<h3>" + this_exercise + "</h3>");
                    renderTableForSets();
                    i++;
                }
                // render add exercise form after all sets are rendered
                else if (i === body.items.length){
                    content.append("<h2>Add Exercise to Workout</h2>");
                    renderAddExerciseForm(body["@controls"]["workoutlog:add-exercise-to-workout"]);
                }
            });
        });
    } else {
        content.append("<h2>Add Exercise to Workout</h2>");
        renderAddExerciseForm(body["@controls"]["workoutlog:add-exercise-to-workout"]);
    }
}

function renderTableForSets() {
    $(".content").append(
        "<table class='sets_table table " +
            "table-striped wrapper table-dark'>" +
        "<thead><tr>" + 
            "<th>Set</th>" +
            "<th>Weight (kg)</th>" +
            "<th>Reps</th>" +
            "<th>RIR</th>" +
        "</tr></thead>" +
        "<tbody></tbody>"
    );
}

function renderSets(body) {
    body.items.forEach(function (item) {
        $(".sets_table tbody").last().append(setRow(item));
    });

    renderAddSetForm(body);
}

function renderWorkoutEditPage(body) {
    let content = $(".content")
    content.empty();
    $(".notification").empty();
    renderTableForWorkouts();

    // Back button
    let link = body["@controls"].collection.href;
    content.html("<div class='text-center'><a class='btn btn-dark' href='' " +
                  "onClick='followLink(event, '" + link + "', renderWorkout)'>" +
                  "Back to Workouts</a></div>");

    // Workouts table
    content.append("<h1>" + body.date_time + "<h2>");
    renderTableForWorkouts();
    $(".workouts_table tbody").append(workoutRow(body, "none"));

    // Workout form
    $(".content").append("<hr>");
    content.append("<h2>Edit This Workout Information</h2>")
    renderWorkoutForm(body["@controls"].edit);
}


/***** Functions for rendering forms  *****/

function renderWorkoutForm(ctrl) {
    let form = $("<form>");
    let date_time = ctrl.schema.properties.date_time;
    let duration = ctrl.schema.properties.duration;
    let body_weight = ctrl.schema.properties.body_weight;
    let average_heart_rate = ctrl.schema.properties.average_heart_rate;
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitWorkout);

    // First row of inputs
    form.append(
        "<div class='row'>" +
            "<div class='col'>" +
                "<label for='date_time' class='form-label'>"
                + date_time.description + "</label>" +
                "<input placeholder='date and time' type='text' " + 
                "name='date_time' class='form-control mb-2'></div>" +
            "<div class='col'>" +
                "<label for='duration' class='form-label'>"
                + duration.description + "</label>" +
                "<input placeholder='duration' type='text' name='duration' " + 
                "class='form-control mb-2'></div></div>"
        );
    // Second row of inputs
    form.append(
        "<div class='row'>" + 
            "<div class='col'>" + 
                "<label for='body_weight' class='form-label'>"
                 + body_weight.description + "</label>" +
                "<input placeholder='body weight' type='number' step='0.1' " + 
                "name='body_weight' class='form-control mb-2'></div>" +
            "<div class='col'>" +
                "<label for='average_heart_rate' class='form-label'>"
                + average_heart_rate.description + "</label>" + 
                "<input placeholder='average heart rate' type='number' " + 
                "step='0.1' name='average_heart_rate' class='form-control mb-2'>" +
                "</div></div>"
        );

    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });

    if (ctrl.method === "POST") {
        var submit_button_text = "Add Workout";
    } else {
        var submit_button_text = "Edit Workout";
    }

    form.append("<div class='text-center'>" + 
        "<input type='submit' name='submit' value='" + submit_button_text + "'" + 
        "class='btn btn-info text-center mt-3'></div></form>"
        );

    $(".content").append(form);
}

function renderAddExerciseForm(ctrl) {
    let form = $("<form class='exercise_form'>");
    form.attr("action", ctrl.href);
    form.attr("method", ctrl.method);
    form.submit(submitExercise);

    form.append(
        "<div class='row'>" +
            "<div class='col'>" + 
                "<input type='text' name='exercise_name'" +
                "placeholder='Name of the exercise' class='new_exercise_input " +
                "form-control mb-2'>" +
            "</div>" +
        "</div>"
         );
    form.append(
        "<div class='text-center'>" + 
            "<input type='submit' name='submit' value='Add Exercise'" + 
            "class='btn btn-info text-center mt-3'>" + 
        "</div></form>"
        );

    ctrl.schema.required.forEach(function (property) {
        $("input[name='" + property + "']").attr("required", true);
    });
    $(".content").append(form);
}

function renderAddSetForm(body) {
    let ctrl = body["@controls"]["workoutlog:add-set"];

    getResource(body["@controls"].up.href, renderHtmlForSetForm).done(function() {
        let form_id = $(".set_form").last().attr("id");
        let form = $("#" + form_id);
        form.attr("action", ctrl.href);
        form.attr("method", ctrl.method);
        form.submit(submitSet);
    });
}

function renderHtmlForSetForm(body) {
    $(".content").append(
        "<form id='" + body.exercise_name.split(' ').join('_') + "' class='set_form'>" + 
            "<div class='row justify-content-md-center'>" +
                "<div class='col-lg-2'>" + 
                    "<input type='number' step='0.1' name='weight' " +
                    "placeholder='weight' class='form-control mb-2 text-center'></div>" +
                "<div class='col-lg-2'>" + 
                    "<input type='number' name='reps' " +
                    "placeholder='reps' class='form-control mb-2 text-center'></div>" +
                "<div class='col-lg-2'>" + 
                    "<input type='number' name='rir' " + 
                    "placeholder='RIR' class='form-control mb-2 text-center'></div>" +
                "<div class='col-lg-2'>" + 
                    "<input type='submit' name='submit' value='Add Set' " + 
                    "class='btn btn-info new_set_submit'></div>" +
            "</div>" +
        "</form>");
}


/***** Functions for rendering Training Program pages  *****/

function renderTableForProgrammingLifting() {
    $(".content").append(
        "<div class='programming'>" +
            "<table class='programming_table table table-striped wrapper table-dark bg-dark'>" +
                "<thead></thead>" +
                "<tbody></tbody>" +
            "</table>" +
            "<div class='form'></div>" +
        "</div>"
    );
    $(".programming_table thead").last().append(
        "<tr>" +
            "<th>Week</th>" +
            "<th>Intensity</th>" +
            "<th>Sets</th>" +
            "<th>Reps</th>" +
            "<th>RIR</th>" +
        "</tr>"
    );
}

function renderTableForProgrammingCardio() {
    $(".content").append(
        "<div class='programming'>" +
            "<table class='programming_table table table-striped wrapper table-dark bg-dark'>" +
                "<thead></thead>" +
                "<tbody></tbody>" +
            "</table>" +
            "<div class='form'></div>" +
        "</div>"
    );
    $(".programming_table thead").last().append(
        "<tr>" +
            "<th>Week</th>" +
            "<th>Duration</th>" +
            "<th>RPE</th>" +
        "</tr>"
    );
}

function programmingRowLifting(item) {
    return "<tr>" +
                "<th>" + item.week_number + "</th>" +
                "<td>" + item.intensity + "</td>" +
                "<td>" + item.number_of_sets + "</td>" +
                "<td>" + item.number_of_reps + "</td>" +
                "<td>" + item.reps_in_reserve + "</td>" +
            "</tr>";
}

function programmingRowCardio(item) {
    return "<tr>" +
                "<th>" + item.week_number + "</th>" +
                "<td>" + item.duration + "</td>" +
                "<td>" + item.rate_of_perceived_exertion + "</td>" +
            "</tr>";
}

function renderProgramming(body) {
    renderNavigation("program");
    let content = $(".content");
    content.html("<h1>Training Program</h1>");

    // Main lift programming table
    content.append("<h2>Main Lift</h2>");
    renderTableForProgrammingLifting();
    body.items.forEach(function (item) {
        if (item.exercise_type === "Main lift") {
            $(".programming_table tbody").append(programmingRowLifting(item));
        }
    });

    // Variation lift programming table
    content.append("<h2>Variation Lift</h2>");
    renderTableForProgrammingLifting();
    body.items.forEach(function (item) {
        if (item.exercise_type === "Variation lift") {
            $(".programming_table tbody").last().append(programmingRowLifting(item));
        }
    });

    // Cardio programming table
    content.append("<h2>Cardio</h2>");
    renderTableForProgrammingCardio();
    body.items.forEach(function (item) {
        if (item.exercise_type === "Cardio") {
            $(".programming_table tbody").last().append(programmingRowCardio(item));
        }
    });
}



/***** Functions for rendering Exercises pages *****/

function renderExercises(body) {
    renderNavigation("exercises");
    let content = $(".content");
    content.html("<h1>Exercises</h1>");
    content.append("<h2>Work in Progress</h2>");
}



/***** Client entry *****/

$(document).ready(function () {
    getResource("http://localhost:5000/api/workouts/", renderWorkouts);
});








