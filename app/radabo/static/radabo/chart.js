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
