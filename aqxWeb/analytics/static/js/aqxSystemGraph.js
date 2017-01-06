"use strict";

var aqxgraph;
if (!aqxgraph) {
    aqxgraph = {};
}

(function () {

    /* ##################################################################################################################
       MAIN CHART LOADING FUNCTIONS
       #################################################################################################################### */

    function drawChart(){
        var graphType = document.getElementById(aqxgraph.GRAPH_TYPE).value;
        var xType = "Time";
        var status = document.getElementById("selectStatus").value;

        // Get measurement types to display on the y-axis
        var yTypes = $("#selectYAxis").val();
        var numberOfEntries = document.getElementById(aqxgraph.NUM_ENTRIES_ELEMENT_ID).value;

        // Generate a data Series for each y-value type, and assign them all to the CHART
        updateChartDataPointsHC(aqxgraph.CHART, xType, yTypes, graphType, numberOfEntries, status).redraw();
    }

    function updateChartDataPointsHC(chart, xType, yTypeList, graphType, numberOfEntries, status){

        // Clear the old chart's yAxis and dataPoints. Unfortunately this must be done manually.
        chart = clearOldGraphValues(chart);

        // Determine if any measurements are not already tracked in systems_and_measurements
        var activeMeasurements = getAllActiveMeasurements();
        var measurementsToFetch = _.difference(yTypeList, activeMeasurements);

        // If there are any measurements to fetch, get the ids then pass those to the API along with the system names
        // and add the new dataPoints to the systems_and_measurements object
        if (measurementsToFetch.length > 0) {
            var measurementIDList = [];
            _.each(measurementsToFetch, function(measurement){
                measurementIDList.push(measurement_types_and_info[measurement].id);
            });
            callAPIForNewData(measurementIDList, 100);
		    callAPIForNewData(measurementIDList, 200);
        }

        // Handle the x axis, for now just using time
        // TODO: Expand to handle changing x axes
        chart.xAxis[0].setTitle({ text: aqxgraph.XAXIS_TITLE });

        // Get dataPoints and their configs for the chart, using systems_and_measurements and add them
        var newDataSeries = getDataPointsForPlotHC(chart, xType, yTypeList, graphType, numberOfEntries, status);
        _.each(newDataSeries, function(series) {
            chart.addSeries(series);
        });
        return chart;
    }

    // TODO: This will need to be re-evaluated to incorporate non-time x-axis values. For now, stubbing xType for this.
    function getDataPointsForPlotHC(chart, xType, yTypeList, graphType, numberOfEntries, status) {

        // DataPoints to add to chart
        var dataPointsList = [];

        // The name of a system and the y variable for which it is missing data
        var missingYTypes = [];

        // Track the number of axes being used
        var numAxes = 0;

        // Axis dict ensures that each variable is plotted to the same, unique axis for that variable
        // i.e. nitrate values for each system to axis 0, pH values for each system to axis 1, etc.
        var axes = {};
        _.each(yTypeList, function(axis) {
            axes[axis] = {isAxis:false};
        });

        // Begin iterating through the systems
        _.each(systems_and_measurements, function(system, j) {

            var measurements = system.measurement;
            // Used to link measurements to the same system
            var linkedTo = false;

            // Loop through selected measurement types
            _.each(yTypeList, function(yType) {

                // Then find matching types in the systems_and_measurements object
                _.each(measurements, function(measurement) {
                    if (_.isEqual(measurement.type.toLowerCase(), yType.toLowerCase()) &&
                        _.isEqual(measurement.status, status)) {
                        var systemId = system.system_uid;

                        // Check if there is data for this system and measurement type
                        if (measurement.values.length > 0) {

                            // Has this variable been assigned an axis yet?
                            // If not, create the axis and assign to a variable. This variables isAxis is now true,
                            // an axis is assigned, and the numAxes increments
                            if (!axes[yType].isAxis) {
                                chart.addAxis(createYAxis(yType, aqxgraph.COLORS[numAxes], (numAxes % 2) , measurement_types_and_info[yType].unit));
                                axes[yType].isAxis = true;
                                axes[yType].axis = numAxes++;
                            }
                            var yAxis = axes[yType].axis;
                            // IMPORTANT: MEASUREMENT VALUES should be sorted by date to display
                            var dataValues = measurement.values;
                            if (!_.isEmpty(numberOfEntries)) {
                                dataValues = _.last(dataValues, numberOfEntries);
                            }
                            // Push valid dataPoints and their configs to the list of dataPoints to plot
                            dataPointsList.push(
                                getDataPoints(system.name, dataValues, graphType, systemId, linkedTo,
                                              aqxgraph.COLORS[yAxis], yAxis,
                                              aqxgraph.DASHSTYLES[j],
                                              aqxgraph.MARKERTYPES[j], yType));
                            linkedTo = true;
                        }

                        // If there is no data, we will warn the user for this system and variable
                        else{
                            missingYTypes.push(system.name + "-" + yType);
                        }
                    }
                });
            });
        });

        // Warn the user about missing data
        if (missingYTypes.length > 0){
            $('#alert_placeholder').html(getAlertHTMLString("Missing values for: " + missingYTypes.toString(), aqxgraph.DANGER));
        }
        return dataPointsList;
    }

    /* ##################################################################################################################
       AJAX CALLS TO GRAB NEW DATA
       #################################################################################################################### */

    /**
     * Take measurement data object from AJAX response, and add to the global systems_and_measurements data
     * @param data
     * @param statusID
     */
    function addNewMeasurementData(data, statusID){
        console.log('success',data);
        var systems = data.response;

        // Loop through existing systems in the systems_and_measurements object
        _.each(systems, function(system) {
            var systemMeasurements = system.measurement;
            _.each(systemMeasurements, function(measurement) {
                measurement.status = statusID.toString()
            });
            _.each(systems_and_measurements, function(existingSystem){
                // Match systems in the new data by id, and then add the new measurements
                // to the list of existing measurements
                if (_.isEqual(existingSystem.system_uid, system.system_uid)){
                    existingSystem.measurement = existingSystem.measurement.concat(systemMeasurements);
                }
            });
        });
    }

    function processAJAXResponse(data, status){
        if("error" in data){
            console.log("Server returned an error...");
            console.log(data);
            throw "AJAX request reached the server but returned an error!";
        } else {
            console.log("here");
            addNewMeasurementData(data, status);
        }
    }

    /**
     * Sends an AJAX POST request to call for new, untracked measurement data for each system
     * @param measurementIDList
     * @param statusID
     */
    function callAPIForNewData(measurementIDList, statusID){
        $.ajax({
            type: 'POST',
            contentType: 'application/json;charset=UTF-8',
            dataType: 'json',
            async: false,
            url: '/dav/aqxapi/v1/measurements/plot',
            data: JSON.stringify({systems: selectedSystemIDs, measurements: measurementIDList, status: statusID}, null, '\t'),
            // Process API response
            success: function(data){
                processAJAXResponse(data, statusID)
            },
            // Report any AJAX errors
            error: ajaxError
        });
    }

    function ajaxError(jqXHR, textStatus, errorThrown){
        var redirectLink = 'error';
        alert('Unable to access the server... Look at the console (F12) for more information!');
        console.log('jqXHR:');
        console.log(jqXHR);
        console.log('textStatus:');
        console.log(textStatus);
        console.log('errorThrown:');
        console.log(errorThrown);
        window.location.href = redirectLink;
    }

    /* ##################################################################################################################
       HELPER FUNCTIONS
       #################################################################################################################### */
    /**
     * Returns a list of all y-variables currently being stored
     * @returns {Array} - An array of all measurement types currently being stored
     */
    function getAllActiveMeasurements() {
        // Grab all measurement types in the checklist
        var activeMeasurements = [];
        var systemMeasurements = _.first(systems_and_measurements).measurement;
        _.each(systemMeasurements, function(measurement) {
            activeMeasurements.push(measurement.type.toLowerCase());
        });
        return activeMeasurements;
    }

    /**
     * Removes any data series' and y-axes from the given chart
     * @param chart
     * @returns {*}
     */
    function clearOldGraphValues(chart) {
        // Clear yAxis
        while(chart.yAxis.length > 0) {
            chart.yAxis[0].remove(true);
        }
        // Clear series data
        while (chart.series.length > 0) {
            chart.series[0].remove(true);
        }
        return chart;
    }

    function setDefaultYAxis() {
        $("#selectYAxis").chosen({
            max_selected_options: aqxgraph.MAXSELECTIONS,
            no_results_text: "Oops, nothing found!",
            width: "100%"
        });
        $('#selectYAxis').val('');
        $('#selectYAxis option[value=' + aqxgraph.DEFAULT_Y_VALUE + ']').prop('selected', true);
        $('#selectYAxis').trigger("chosen:updated");
    }

    function getAlertHTMLString(alertText, type){
        return '<div class="alert alert-' + type + '"><a class="close" data-dismiss="alert">×</a><span>' +alertText + '</span></div>';
    }

    function getDataPoints(systemName, dataPoints, graphType, id, linkedTo, color, yAxis, dashStyle, markerType, yType) {
        var series = { name: systemName + ',' + yType,
                       type: graphType,
                       data: dataPoints,
                       color: color,
                       id: id,
                       yAxis: yAxis,
                       dashStyle: dashStyle,
                       marker: {symbol: markerType}
                     };
        if (linkedTo) {
            series.linkedTo = id;
        }
        return series;
    }

    function createYAxis(yType, color, opposite, units){
        var unitLabel;
        if (units) {
            unitLabel = (_.isEqual(units, "celsius")) ? "°C" : units;
        } else {
            unitLabel = "";
        }
        return { // Primary yAxis
            title:
            {
                text: yType,
                style: {color: color}
            },
            labels:
            {
                format: '{value} ' + unitLabel,
                style: {color: color}
            },
            showEmpty: false,
            lineWidth: 1,
            tickWidth: 1,
            gridLineWidth: 1,
            opposite: opposite,
            gridLineColor: '#707073',
            lineColor: '#707073',
            minorGridLineColor: '#505053',
            tickColor: '#707073'
        };
    }

    /* ##################################################################################################################
       PAGE-DRIVING FUNCTIONS
       ################################################################################################################### */

    /**
     *  main - Sets behaviors for Submit and Reset buttons, populates y-axis dropdown, and checks nitrate as default y-axis
     */
    aqxgraph.main = function() {

        // Select the default y-axis value
        setDefaultYAxis();

        $("#selectStatus option[text='pre-established']").attr("selected","selected");

        // When the submit button is clicked, redraw the graph based on user selections
        $('#submitbtn').on('click', function() {
            $('#alert_placeholder').empty();
            drawChart();
        });

        // Reset button, returns dropdowns to default, clears checklist, and displays default nitrate vs time graph
        $('#resetbtn').on('click', function(){

            // Reset X Axis selection to default
            $('#selectXAxis option').prop(aqxgraph.SELECTED, function() {
                return this.defaultSelected;
            });

            // Reset Graph Type selection to default
            $('#selectGraphType option').prop(aqxgraph.SELECTED, function() {
                return this.defaultSelected;
            });

            $('#' + aqxgraph.NUMBER_OF_ENTRIES + ' option').prop(aqxgraph.SELECTED, function() {
                return this.defaultSelected;
            });
            $('#alert_placeholder').empty();
            $('#analyzeContainer').show();

            // Select the default y-axis value
            setDefaultYAxis();
            drawChart();
        });

        $('#selectYAxis').bind("chosen:maxselected", function () {
            $('#alert_placeholder').html(getAlertHTMLString("You can select up to " + aqxgraph.MAXSELECTIONS + " systems", 'danger'));
        });
    };

    /**
     * loadChart - On window load, populates the Chart
     */
    window.onload = function() {
        aqxgraph.HC_OPTIONS = {
            chart: {
                renderTo: 'analyzeContainer',
                type: 'line',
                zoomType: 'xy',
                backgroundColor: aqxgraph.BACKGROUND,
                plotBorderColor: '#606063'
            },
            title: {
                text: aqxgraph.CHART_TITLE,
                style: {
                    color: '#E0E0E3'
                }
            },
            credits: {
                style: {
                    color: '#666'
                }
            },
            tooltip: {
                formatter: tooltipFormatter,
                crosshairs: [true,true]
            },
            legend: {
                itemStyle: {
                    color: '#E0E0E3'
                },
                enabled: true,
                labelFormatter: function() {
                    return '<span>'+ this.name.split(",")[0] + '</span>';
                },
                symbolWidth: 60
            },
            xAxis: {
                minPadding: 0.05,
                maxPadding: 0.05,
                title:
                {
                    text: aqxgraph.XAXIS_TITLE,
                    style: {color: 'white   '}
                }
            },
            exporting: {
                csv: {
                    columnHeaderFormatter: function(series){
                        var name_and_variable = series.name.split(",");
                        return name_and_variable[0] + '-' + name_and_variable[1];
                    }
                }
            },
            showInLegend: true,
            series: []
        };
        try {
            aqxgraph.CHART = new Highcharts.Chart(aqxgraph.HC_OPTIONS);
        } catch(err){
            console.log("Unable to initialize Highcharts Chart object!");
            console.log(err.stack);
        }
        Highcharts.setOptions(Highcharts.theme);
        // Render chart based on default page setting. i.e. x-axis & graph-type dropdowns, and the y-axis checklist
        drawChart();
    };

    function tooltipFormatter(){
        var tooltipInfo = this.series.name.split(",");
        var yVal = tooltipInfo[1];
        var units = measurement_types_and_info[yVal].unit;
        units = (units) ? units : "";
        units = (_.isEqual(units, "celsius")) ? "°C" : units;
        yVal = yVal.charAt(0).toUpperCase() + yVal.slice(1);
        var datetime = this.point.date.split(" ");
        var eventString = "";
        if (this.point.annotations) {
            console.log('event found');
            eventString = "<br><p>Most recent event(s): </p>";
            _.each(this.point.annotations, function (event) {
                console.log(event);
                eventString = eventString + '<br><p>' + annotationsMap[event.id]+ " at " + event.date + '<p>'
            });
        }
        return '<b>' + tooltipInfo[0] + '</b>' +
            '<br><p>' + yVal + ": " + this.y + ' ' + units + '</p>' +
            '<br><p>Hours in cycle: ' + this.x + '</p>' +
            '<br><p>Measured on: ' + datetime[0] + '</p>' +
            '<br><p>At time: ' + datetime[1] +'</p>' +
            eventString;
    }
}());
