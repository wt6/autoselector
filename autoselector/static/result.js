$(document).ready(function(){

    //Create array of datapoints for graph of depreciation, in format [[age, value], ...] using array of values
    var depreciationArr = [];
    for (i=0; i<depreciation.length; i++){
        if (typeof(depreciation[i]) === "number"){
            // for selected age make point size larger
            if (i == age){
                depreciationArr.push([i, depreciation[i], 'point {size: 6;}']);
            }
            else{
                depreciationArr.push([i, depreciation[i], null]);
            }
        }
    }

    // Generate graph of car value and costs for result.html
    // Load the Visualization API and the corechart package.
    google.charts.load('current', {'packages':['corechart'], 'language': 'en-GB'});

    // Set a callback to run when the Google Visualization API is loaded.
    google.charts.setOnLoadCallback(drawChart);

    // Callback that creates and populates the data table,
    // instantiates the line chart, passes in the data and
    // draws it.
    function drawChart() {
        // Create the data table.
        var data = new google.visualization.DataTable();
        data.addColumn('number', 'Age');
        data.addColumn('number', 'Value');
        data.addColumn({type: 'string', role: 'style'});
        data.addRows(depreciationArr);

        // Set chart options
        var options = {
            title:'Depreciation',
            curveType: 'function',
            legend: { position: 'right' },
            hAxis: {title: 'Vehicle Age', format: '##'},
            vAxis: {format: 'currency', title: 'Estimated Value'},
            pointSize: 4,
        };

        // Instantiate and draw our chart, passing in some options.
        var chart = new google.visualization.LineChart(document.getElementById('graph'));
        chart.draw(data, options);
      }

    // Find values of vehicle at new, at the selected age and at 3 years past selected age
    var initValue = null;
    var selectedAgeValue = null;
    var futureValue = null;
    for (i=0; i < depreciationArr.length; i++){
        if (depreciationArr[i][0] == 0){
            initValue = depreciationArr[i][1];
        }
        if (depreciationArr[i][0] == age){
            selectedAgeValue = depreciationArr[i][1];
        }
        if (depreciationArr[i][0] == age+3){
            futureValue = depreciationArr[i][1];
        }
    }

    // Calculate percentage depreciation rate from new to selected age
    var pastDepreciation = null;
    var futureDepreciation = null;
    if (initValue > 0 && selectedAgeValue != null){
        pastDepreciation = Math.round(100 * (1 - selectedAgeValue / initValue));
    }
    else if (initValue <= 0 && selectedAgeValue != null){
        pastDepreciation = 0;
    }

    // Calculate percentage depreciation rate over next 3 years from selected age
    if (selectedAgeValue > 0 && futureValue != null){
        futureDepreciation = Math.round(100 * (1 - futureValue / selectedAgeValue));
    }
    else if (selectedAgeValue <= 0 && futureValue != null){
        futureDepreciation = 0;
    }

    // If calculated depreciation values are available, display past and future depreciation estimates at top of 'result' webpage
    if (pastDepreciation != null)
    {
        $("#pastDepreciation").text("At this age the vehicle will have already lost approximately " + pastDepreciation + "% of it's original value!");
    }
    if (futureDepreciation != null)
    {
        $("#futureDepreciation").text("In the next 3 years you can expect this vehicle to depreceate by approximately " + futureDepreciation + "%.");
    }
});