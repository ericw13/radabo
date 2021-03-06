function drawChart(djangoData, chartType, url, token, num) {
    var data = new google.visualization.DataTable();
    data.addColumn('string','Metric');
    data.addColumn('number','Story Count');

    if (djangoData.length == 0) {
        document.getElementById('chart'+num).innerHTML = "Something went wrong, no data passed in.";
    } else {
        for (var i=0;i<djangoData.length;i++) {
           data.addRows([[djangoData[i].metric,djangoData[i].scount]]);
        } 
    }
    var options = { };

    var chart = new google.visualization.PieChart(document.getElementById('chart'+num));
    chart.draw(data, options);
    google.visualization.events.addListener(chart, 'select', function () {selectHandler(chart,data,chartType,token,url)});

    function resizeHandler() {
        chart.draw(data, options);
    }
    if (window.addEventListener) {
        window.addEventListener('resize', resizeHandler, false);
    }
    else if (window.attachEvent) {
        window.attachEvent('onresize', resizeHandler);
    }
}
function selectHandler(metaChart,metaData,option,token,url) {
    var selection = metaChart.getSelection();
       if (selection.length) {
           var pieSliceLabel = metaData.getValue(selection[0].row,0);
           post(option, pieSliceLabel,token,url)
    }
}
function post(tag, value, token, url) {
       var form = document.createElement("form");
       form.setAttribute("method", "post");
       form.setAttribute("action", url);
       var hiddenField = document.createElement("input");
       var hiddenField2 = document.createElement("input");
       hiddenField.setAttribute("type", "hidden");
       hiddenField.setAttribute("name", tag);
       hiddenField.setAttribute("value", value);
       form.appendChild(hiddenField);
       hiddenField2.setAttribute("type", "hidden");
       hiddenField2.setAttribute("name", "csrfmiddlewaretoken");
       hiddenField2.setAttribute("value", token);
       form.appendChild(hiddenField2);
       document.body.appendChild(form);
       form.submit();
}
$(window).resize(function(){
    drawChart();
}); 

function drawVelocity(djangoData, avg) {
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Sprint');
    data.addColumn('number', 'Sprint Velocity');
    data.addColumn('number', 'Average Velocity');
 
    for (var i=0;i<djangoData.length;i++) {
        data.addRows([[djangoData[i].name, djangoData[i].velocity, avg]]);
    }
    var options = {
              width: 700, 
              height: 480, 
              curveType: 'function',
              title: "Team Velocity",
              titleFontSize: 24,
              hAxis: {title: "Sprint", slantedText: true, titleFontSize: 20},
              vAxis: {title: "Story Points", baseline: 50, titleFontSize: 20},
              series: {
                 0: {pointSize: 4}
                 }
    };

    var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}

function drawRelease(djangoData) {
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Release');
    data.addColumn('number', 'Story Count');
    data.addColumn('number', 'Business Value');
 
    var total = 0;
    for (var i=0;i<djangoData.length;i++) {
        var name = djangoData[i].release__name;
        var trimmedName = name.replace(" - Enh Release","");
        data.addRows([[trimmedName, djangoData[i].count, djangoData[i].sum]]);
        total += djangoData[i].count;
    }
    var options = {
              title: "Enhancement Releases - " + total + " total stories",
              titleFontSize: 20,
              width: 700, 
              height: 480, 
              curveType: 'function',
              series: {
                0: {targetAxisIndex: 0, pointSize: 4},
                1: {targetAxisIndex: 1, pointSize: 4},
              },
              hAxis: {title: "Release", slantedText: true, titleFontSize: 16},
              vAxes: {
                0: {title: "Story Count", titleFontSize: 16},
                1: {title: "Earned Business Value", titleFontSize: 16},
              },
              legend: {position: "in"},
    };

    var chart = new google.visualization.LineChart(document.getElementById('chart_div'));
    chart.draw(data, options);
}

function drawColChart(djangoData) {
    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Status');
    data.addColumn('number', 'Count');
    data.addColumn({type: 'string', role: 'style'});

    var statusDisplay;
    var style;
    for (var i=0;i<djangoData.length;i++) {
        switch(djangoData[i].status) {
            case "B":
                statusDisplay = "Backlog";
                style = 'color: #8042ca';
                break;
            case "D":
                statusDisplay = "Defined";
                style = 'color: #428BCA';
                break;
            case "P":
                statusDisplay = "In Progress";
                style = 'color: #42C0CA';
                break;
            case "C":
                statusDisplay = "Completed";
                style = 'color: #42CA44';
                break;
            case "A":
                statusDisplay = "Accepted";
                style = 'color: #009933';
                break;
        }
        data.addRow([statusDisplay, djangoData[i].count, style]);
    }

    var view = new google.visualization.DataView(data);
    view.setColumns([0, 1,
                      {calc: "stringify",
                       sourceColumn: 1,
                       type: "string",
                       role: "annotation"},
                     2 ]);

    var options = {
              titleFontSize: 24,
              hAxis: { 
                 title: "Story Status",
                 textStyle: {fontSize: "18"},
                 titleTextStyle: {fontSize: "24"},
                     },
              vAxis: { 
                 title: "Count",
                 textStyle: {fontSize: "18"},
                 titleTextStyle: {fontSize: "24"},
              },
              legend: {position: "none"},
    };

    var chart = new google.visualization.ColumnChart(document.getElementById('chart1'));
    chart.draw(view, options);
}

function getDate(input) {
    var dtarray = input.split('-');
    dtarray[1] -= 1;
    var dt = new Date(dtarray[0], dtarray[1], dtarray[2]);
    return dt;
}

function drawGanttChart(djangoData) {

    var data = new google.visualization.DataTable();
    data.addColumn('string', 'Task ID');
    data.addColumn('string', 'Task Name');
    data.addColumn('string', 'Resource');
    data.addColumn('date', 'Start Date');
    data.addColumn('date', 'End Date');
    data.addColumn('number', 'Duration');
    data.addColumn('number', 'Percent Complete');
    data.addColumn('string', 'Dependencies');

    var id;
    var name;
    var pct;
    var startDate;
    var endDate;
    for (i=0;i<djangoData.length;i++) {

        id = djangoData[i].id;
        name = djangoData[i].name;
        startDate = djangoData[i].startDate;
        endDate = djangoData[i].endDate;
        pct = djangoData[i].percent;

        data.addRows([[id,
                       name,
                       null,
                       getDate(startDate),
                       getDate(endDate),
                       null,
                       pct,
                       null]]);
       
        //console.log(id + " " + name + " runs from " + startDate + " to " + endDate + " and is " + pct + "% complete.");
    }
    var options = {
      height: 600,
      width: 1000,
      gantt: {
              trackHeight: 50,
              criticalPathEnabled: false,
              labelStyle: {
                           fontName: "Arial",
                           fontSize: 16,
                          },
             },
    };

    var chart = new google.visualization.Gantt(document.getElementById('chart_div'));
    chart.draw(data, options);
} 
