"use strict";

const DEBUG = true;
const MASONJSON = "application/vnd.mason+json";
const PLAINJSON = "application/json";

/**
 * Functions for rendering different types of messages from the course material
 */
function renderError(jqxhr) {
    let msg = jqxhr.responseJSON["@error"]["@message"]
    alert(msg);
}

function renderMsg(msg, target) {
    if (target) {
        $(target).after("<p class='msg'>" + msg + "</p>");
    } else {
        $("div.notification").html("<p class='msg'>" + msg + "</p>");
    }
}

/**
 * Ajax get convenience function from the course material
 */
function getResource(href, renderer) {
    return $.ajax({
        url: href,
        success: renderer,
        error: renderError
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
    if (renderer == deleteSet) {
        let table_id = event["path"][4]["id"];
        let table = $("#" + table_id);
        table.addClass("remove_set_from_this");
    }
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
    let form = $("#exercise_form");
    data.exercise_name = $("input[name='exercise_name']").val();
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedExercise);
}

function getSubmittedExercise(data, status, jqxhr) {
    renderMsg("Exercise added");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, renderNewExercise);
    }
}

function renderNewExercise(body) {
    let delete_link = body["@controls"]["workoutlog:delete-from-workout"].href;

    // If there are no set forms, this is the first exercise in the workout
    if ($(".set_form").length === 0) {
        $(".workouts_table").after(
            "<h2 id='" + body.exercise_name.split(' ').join('_') + "_title'>" +
            body.exercise_name +
                "<a class='btn btn-danger' " + 
                "href='" + delete_link + "' onClick='followLink " + 
                "(event, this, deleteExerciseFromWorkout)'>" +
                "Delete</a>" +
            "</h2>"
            );
    } else {
        $(".set_form").last().after(
            "<h2 id='" + body.exercise_name.split(' ').join('_') + "_title'>" +
            body.exercise_name +
                " <a class='btn btn-danger' " + 
                "href='" + delete_link + "' onClick='followLink " + 
                "(event, this, deleteExerciseFromWorkout)'>Delete</a>" +
            "</h2>"
        );
    }

    renderTableForSets(body.exercise_name);
    getResource(
        body["@controls"]["workoutlog:sets-within-workout"].href,
        renderAddSetForm
    );
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

    // Remove ID from the previous table a set was added to and
    // give ID to the correct table where the set will be appended
    $("table").removeClass("new_set_target");
    $("#" + form_id).prev().addClass("new_set_target");

    sendData(form.attr("action"), form.attr("method"), data, getSubmittedSet);
}

function getSubmittedSet(data, status, jqxhr) {
    // Render message under the set form
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(href, appendSetRow);
    }
}

function appendSetRow(body) {
    $(".new_set_target").append(setRow(body));
}

function submitMaxData(event) {
    event.preventDefault();
    let data = {};
    let form = $("#max_data_form");
    data.date = $("input[name='date']").val();
    data.estimated_max = parseFloat($("input[name='estimated_max']").val());
    sendData(form.attr("action"), form.attr("method"), data, getSubmittedMaxData);
}

function getSubmittedMaxData(data, status, jqxhr) {
    renderMsg("Max data added", "#max_data_form");
    let href = jqxhr.getResponseHeader("Location");
    if (href) {
        getResource(
            href,
            reRenderGraph
        );
    }
}

function reRenderGraph(body) {
    getResource(body["@controls"].collection.href, renderGraph);
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

function deleteExerciseFromWorkout(body) {
    sendData(
        body["@controls"]["workoutlog:delete-from-workout"].href,
        body["@controls"]["workoutlog:delete-from-workout"].method
        ).done(function() {
            getResource(
                body["@controls"].collection.href,
                reRenderWorkout
            )
        });
}

function reRenderWorkout(body) {
    getResource(
        body["@controls"].up.href,
        renderWorkout
    )
}

function deleteSet(body) {
    sendData(
        body["@controls"]["workoutlog:delete"].href,
        body["@controls"]["workoutlog:delete"].method
        ).done(function() {
            $(".remove_set_from_this tbody th:contains('" 
                + body["order_in_workout"] + "')").parent().remove();
            $(".remove_set_from_this").removeClass("remove_set_from_this");
        });
}



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
                "<thead>" +
                    "<tr>" +
                        "<th>Date</th>" +
                        "<th>Duration</th>" +
                        "<th>Body Weight (kg)</th>" +
                        "<th>Average Heart Rate</th>" +
                        "<th>Action</th>" +
                    "</tr>" +
                "</thead>" +
                "<tbody></tbody>" +
            "</table>" +
            "<div class='form'></div>" +
        "</div>"
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
        "' onClick='followLink(event, this, " +
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
    var delete_link = "<a href='" +
        item["@controls"]["workoutlog:delete"].href +
        "' onClick='followLink(event, this, " +
        "deleteSet)'>delete</a>";
    
    return "<tr>" +
                "<th>" + item.order_in_workout + "</th>" +
                "<td>" + item.weight + "</td>" +
                "<td>" + item.number_of_reps + "</td>" +
                "<td>" + item.reps_in_reserve + "</td>" +
                "<td>" + delete_link + "</td>" +
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
    content.append("<div class='text-center mt-5'><a class='btn btn-dark' " + 
        "href='" + link + "' onClick='followLink(event, this, renderWorkouts)'>" +
        "Back to Workouts</a></div>"
    );

    // Workouts table
    content.append("<h1>" + body.date_time + "</h1>");
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
    if (body.items.length === 0) {
        content.append(
            "<h3 id='add_exercise_title'>Add Exercise to Workout</h3>"
        );
        renderAddExerciseForm(
            body["@controls"]["workoutlog:add-exercise-to-workout"]
        );
    } else { // There are exercises already
        let promises = [];
        body.items.forEach(function (exercise_item) {
            let request = $.ajax({
                url: exercise_item["@controls"]["workoutlog:sets-within-workout"].href,
                success: function(result) {
                    let exercise_name = exercise_item.exercise_name;
                    let delete_link = exercise_item["@controls"]["workoutlog:delete-from-workout"].href;
                    content.append(
                            "<h2 id='" + exercise_name.split(' ').join('_') +
                            "_title'>" + exercise_name  +
                                "<a class='btn btn-danger' " + 
                                "href='" + delete_link + "' onClick='followLink " + 
                                "(event, this, deleteExerciseFromWorkout)'>" +
                                "Delete</a>" +
                            "</h2>"
                    );
                    renderTableForSets(exercise_name);
                    result.items.forEach(function (set_item) {
                        $(".sets_table tbody").last().append(setRow(set_item));
                    });
                    renderAddSetForm(result);
                },
                error: renderError
            });
            promises.push(request);
        });
        
        // Render add exercise form after all exercises have been rendered
        $.when.apply(null, promises).done(function() {
            content.append(
                "<h3 id='add_exercise_title'>Add Exercise to Workout</h3>"
            );
            renderAddExerciseForm(
                body["@controls"]["workoutlog:add-exercise-to-workout"]
            );
        })
    }
}

function renderTableForSets(exercise_name) {
    // .split() is used because HTML doesn't allow spaces
    let title_id = exercise_name.split(' ').join('_') + "_title";
    let table_id = exercise_name.split(' ').join('_') + "_table";
    $("#" + title_id).after(
        "<table id='" + table_id + "'" +
        "class='sets_table table table-striped wrapper table-dark'></table>"
    );

    $("#" + table_id).append(
        "<thead><tr>" + 
            "<th>Set</th>" +
            "<th>Weight (kg)</th>" +
            "<th>Reps</th>" +
            "<th>RIR</th>" +
            "<th>Action</th>" +
        "</tr></thead>" +
        "<tbody></tbody>"
    );
}


function renderWorkoutEditPage(body) {
    let content = $(".content")
    content.empty();
    $(".notification").empty();

    // Back button
    let link = body["@controls"].self.href;
    content.append(
        "<div class='text-center mt-5'><a class='btn btn-dark' " + 
        "href='" + link + "' onClick='followLink(event, this, renderWorkout)'>" +
        "Back to Workout</a></div>"
    );

    // Workouts table
    content.append("<h1>" + body.date_time + "</h1>");
    renderTableForWorkouts();
    $(".workouts_table tbody").append(workoutRow(body, "none"));

    // Edit form
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
                "<label for='date_time' class='form-label'>" + 
                date_time.description + "</label>" + 
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
                "step='1' name='average_heart_rate' class='form-control mb-2'>" +
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
    let form = $("<form id='exercise_form'>");
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
    // .split() is used because HTML doesn't allow spaces
    $("#" + body.exercise_name.split(' ').join('_') + "_table").after(
        "<form id='" + body.exercise_name.split(' ').join('_') + "_form' " + 
        "class='set_form'>" + 
            "<div class='row justify-content-md-center'>" +
                "<div class='col-lg-2'>" + 
                    "<input type='number' step='0.1' name='weight' " +
                    "placeholder='weight' class='form-control mb-2 text-center'>" +
                "</div>" +
                "<div class='col-lg-2'>" + 
                    "<input type='number' name='reps' " +
                    "placeholder='reps' class='form-control mb-2 text-center'>" + 
                "</div>" +
                "<div class='col-lg-2'>" + 
                    "<input type='number' name='rir' " + 
                    "placeholder='RIR' class='form-control mb-2 text-center'>" + 
                "</div>" +
                "<div class='col-lg-2'>" + 
                    "<input type='submit' name='submit' value='Add Set' " + 
                    "class='btn btn-info'>" +
                "</div>" +
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
            "<th>Intensity (%)</th>" +
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


function renderTableForExercises() {
    $(".content").append(
        "<div class='workouts'>" +
            "<table class='exercise_table table table-striped wrapper table-dark bg-dark'>" +
                "<thead>" +
                    "<tr>" +
                        "<th>Exercise</th>" +
                        "<th>Action</th>" +
                    "</tr>" +
                "</thead>" +
                "<tbody></tbody>" +
            "</table>" +
            "<div class='form'></div>" +
        "</div>"
    );
}

function exerciseRow(item) {
    let self_link = "<a href='" + item["@controls"].self.href +
        "' onClick='followLink(event, this, renderExercise)'>show</a><br>";
    
    return "<tr>" +
            "<th>" + item.exercise_name + "</th>" +
            "<td>" + self_link + "</td>" +
            "</tr>";
}

function renderExercises(body) {
    renderNavigation("exercises");
    let content = $(".content");
    $(".notification").empty();
    content.empty();
    content.html("<h1>Trained Exercises</h1>");
    renderTableForExercises();
    
    $(".exercise_table tbody").empty();
    body.items.forEach(function (item) {
        $(".exercise_table tbody").append(exerciseRow(item));
    });
}

function renderExercise(body) {
    let content = $(".content");
    content.empty();

    // Back button
    let link = body["@controls"].collection.href;
    content.append(
        "<div class='text-center mt-5'><a class='btn btn-dark' " + 
        "href='" + link + "' onClick='followLink(event, this, renderExercises)'>" +
        "Back to Exercises</a></div>");

    // Exercise max data graph
    content.append("<h1>" + body.exercise_name + "</h2>")
    content.append("<h2>Max Data Chart</h2>");
    content.append("<div id='chartContainer' style='height: 370px; width: 100%;'></div>");
    getResource(
        body["@controls"]["workoutlog:max-data-for-exercise"].href,
        renderGraph
    ).done(function() {
        getResource(
            body["@controls"]["workoutlog:max-data-for-exercise"].href,
            renderAddMaxDataForm
        );
    });

    // Latest workouts the exercise has been trained in
    content.append("<h2>Latest Workouts</h2>");
    getResource(
        body["@controls"]["workoutlog:workouts-by-exercise"].href,
        renderWorkoutsByExercise
    );
}

function renderWorkoutsByExercise(body) {
    let content = $(".content");
    
    // If there are no exercises yet, render just the add exercise form
    if (body.items.length == 0){
        content.append("<p>This exercise hasn't been trained in any workouts yet</p>")
    } else {
        let i = 0;
        body.items.forEach(function (workout_item) {
            $.ajax({
                url: workout_item["@controls"]["workoutlog:sets-within-workout"].href,
                success: function(result) {
                    let date_time = workout_item.date_time;
                    content.append(
                        "<h3 id='" + i + "_title'>"
                        + date_time + "</h3>"
                    );
                    renderTableForSets(i.toString());
                    result.items.forEach(function (set_item) {
                        $(".sets_table tbody").last().append(setRow(set_item));
                    });
                    i++;
                },
                error: renderError
            });
        });
    }
}

function renderSetsWithoutForm(body) {
    body.items.forEach(function (item) {
        $(".sets_table tbody").last().append(setRow(item));
    });
}

// Uses API on https://canvasjs.com/jquery-charts/
function renderGraph(body) {
    if ($(".msg")) {
        $(".msg").remove();
    }

    let max_data = [];
    body.items.forEach(function (item) {
        max_data.push({ x: new Date(item.date), y: item.estimated_max });
    });

    let chartContainer = $("#chartContainer")

    if (max_data.length < 2) {
        chartContainer.after(
        "<p class='msg'>Not enough max data to form a graph has been added " + 
        "for this exercise yet. Add data with the form above.</p>"
        );
    }
    
    chartContainer.empty();
    var options = {
        animationEnabled: true,
        theme: "dark1",
        title:{
            text: "Estimated Max"
        },
        axisX:{
            valueFormatString: "YYYY MMM",
            lineColor: "#0ecae3",
        },
        axisY: {
            title: "Weight",
            suffix: " kg",
            titleFontColor: "#51CDA0",
            lineColor: "#0ecae3",
            gridColor: "grey"
        },
        toolTip:{
            shared:true
        },  
        legend:{
            cursor:"pointer",
            verticalAlign: "bottom",
            horizontalAlign: "left",
            dockInsidePlotArea: true
        },
        data: [{
            type: "line",
            showInLegend: true,
            name: "Estimated Max",
            markerType: "square",
            xValueFormatString: "YYYY-MMM-DD",
            color: "white",
            lineColor: "#51CDA0",
            yValueFormatString: "#,##0 kg",
            dataPoints: max_data
        }]
    };
    chartContainer.CanvasJSChart(options);
}

function renderAddMaxDataForm(body) {
    let ctrl = body["@controls"]["workoutlog:add-max-data"];

    getResource(body["@controls"].up.href, renderHtmlForMaxDataForm).done(function() {
        let form_id = $(".max_data_form").last().attr("id");
        let form = $("#" + form_id);
        form.attr("action", ctrl.href);
        form.attr("method", ctrl.method);
        form.submit(submitMaxData);
    });
}

function renderHtmlForMaxDataForm(body) {
    // .split() is used because HTML doesn't allow spaces
    $("#chartContainer").after(
        "<form id='max_data_form' class='max_data_form'>" +
            "<div class='row justify-content-md-center'>" +
                "<div class='col-lg-2 mt-3'>" + 
                    "<input type='text' name='date' " +
                    "placeholder='date' class='form-control mb-2 text-center'>" +
                "</div>" +
                "<div class='col-lg-2 mt-3'>" + 
                    "<input type='number' step='0.1' name='estimated_max' " +
                    "placeholder='estimated max' class='form-control mb-2 text-center'>" + 
                "</div>" +
                "<div class='col-lg-2 mt-3'>" + 
                    "<input type='submit' name='submit' value='Add Max Data' " + 
                    "class='btn btn-info'>" +
                "</div>" +
            "</div>" +
        "</form>");
}




/***** Client entry *****/

$(document).ready(function () {
    getResource("http://localhost:5000/api/workouts/", renderWorkouts);
});



