define('d3', ['lib/d3-3.3.3.js'], function(none){
    return d3;
});

require(['jquery'
, 'd3'
, 'mod/contribut_info'
, 'mod/watch' ], function($, d3){
    //put your home code here.

    function activity_graph(data) {
        var commits = data["data"];
        var w = 30,
        h = 90;
        var x = d3.scale.linear()
        .domain([0, 1])
        .range([0, w]);
        var y = d3.scale.linear()
        .domain([0, 100])
        .rangeRound([0, h]);
        var chart = d3.select("ul.graph-container").append("svg")
        .attr("class", "chart")
        .attr("width", w * 26)
        .attr("height", h);

        chart.selectAll("rect")
        .data(commits)
        .enter().append("rect")
        .attr("x", function(d, i) { return x(i) - .5; })
        .attr("y", function(d) { return h - y(d.commits/d.commits_peak*h) - .5; })
        .attr("width", w)
        .attr("height", function(d) { return y(d.commits/d.commits_peak*h); });
    };

    function commits_graph(data1) {
        var data = data1["data"];
        var names = data1["authors"];

        var margin = {top: 20, right: 130, bottom: 30, left: 50},
        width = 940 - margin.left - margin.right,
        height = 500 - margin.top - margin.bottom;

        var parseDate = d3.time.format("%Y-%m-%d").parse;

        var x = d3.time.scale()
        .range([0, width]);

        var y = d3.scale.linear()
        .range([height, 0]);

        var color = d3.scale.category10();

        var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

        var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

        var line = d3.svg.line()
        .interpolate("basis")
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.commits); });

        var svg = d3.select("ul.commits-container").append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        color.domain(names);

        data.forEach(function(d) {
            d.date = parseDate(d.date);
        });

        var authors = names.map(function(name) {
            return {
                name: name,
                values: data.map(function(d) {
                    return {date: d.date, commits: +d[name]};
                })
            };
        });

        x.domain(d3.extent(data, function(d) { return d.date; }));

        y.domain([
                 d3.min(authors, function(c) {
            return d3.min(c.values, function(v) {
                return v.commits; }); }),
                d3.max(authors, function(c) {
                    return d3.max(c.values, function(v) {
                        return v.commits; }); })
        ]);

        svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

        svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Commits");

        var author = svg.selectAll(".author")
        .data(authors)
        .enter().append("g")
        .attr("class", "author");

        author.append("path")
        .attr("class", "line")
        .attr("d", function(d) { return line(d.values); })
        .style("stroke", function(d) { return color(d.name); });

        author.append("text")
        .datum(function(d) { return {name: d.name, value: d.values[d.values.length - 1]}; })
        .attr("transform", function(d) { return "translate(" + x(d.value.date) + "," + y(d.value.commits) + ")"; })
        .attr("x", 2)
        .attr("dy", ".35em")
        .text(function(d) { return d.name; });
    };

    function extensions_graph(data) {
        var newdata = data["data"];
        var width = 465,
        height = 400,
        radius = Math.min(width, height) / 2 ;
        var color = d3.scale.category20b();
        var arc = d3.svg.arc()
        .outerRadius(radius - 10)
        .innerRadius(0);
        var pie = d3.layout.pie()
        .sort(function(a, b) { return b.value - a.value; })
        .value(function(d) { return d.value; });
        var pie2 = d3.layout.pie()
        .sort(function(a, b) { return b.files - a.files; })
        .value(function(d) { return d.files; });
        var svg = d3.select("div.ext-lines-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .data(newdata)
        .append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

        var svg2 = d3.select("div.ext-files-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .data(newdata)
        .append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

        var arcs = svg.selectAll(".arc")
        .data(pie(newdata))
        .enter().append("g")
        .attr("class", "arc");
        arcs.append("svg:path")
        .attr("fill", function(d, i) { return color(i); })
        .attr("d", arc);

        arcs.filter(function(d) { return d.endAngle - d.startAngle > .2; }).append("svg:text")
        .attr("transform", function(d) {
            d.innerRadius = 0;
            d.outerRadius = radius;
            return "translate(" + arc.centroid(d) + ")";
        })
        .attr("text-anchor", "middle")
        .text(function(d, i) { return d.data.name+"("+d.data.loc_p+"%"+")"; });

        var arcs2 = svg2.selectAll(".arc")
        .data(pie2(newdata))
        .enter().append("g")
        .attr("class", "arc");
        arcs2.append("svg:path")
        .attr("fill", function(d, i) { return color(i); })
        .attr("d", arc);

        arcs2.filter(function(d) { return d.endAngle - d.startAngle > .2; }).append("svg:text")
        .attr("transform", function(d) {
            d.innerRadius = 0;
            d.outerRadius = radius;
            return "translate(" + arc.centroid(d) + ")";
        })
        .attr("text-anchor", "middle")
        .text(function(d, i) { return d.data.name+"("+d.data.foc_p+"%"+")"; });
        function angle(d) {
            var a = (d.startAngle + d.endAngle) * 90 / Math.PI - 90;
            return a > 90 ? a - 180 : a;
        };
    };

    function lines_graph(data) {
        var margin = {top: 20, right: 20, bottom: 30, left: 50},
        width = 940 - margin.left - margin.right,
        height = 470 - margin.top - margin.bottom;

        var newdata = data["data"];

        var parseDate = d3.time.format("%Y-%m-%d").parse;

        var x = d3.time.scale()
        .range([0, width]);

        var y = d3.scale.linear()
        .range([height, 0]);

        var xAxis = d3.svg.axis()
        .scale(x)
        .orient("bottom");

        var yAxis = d3.svg.axis()
        .scale(y)
        .orient("left");

        var line = d3.svg.line()
        .x(function(d) { return x(d.date); })
        .y(function(d) { return y(d.lines); });
        var svg = d3.select("ul.lines-container").append("svg")
        .data(newdata)
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        newdata.forEach(function(d) {
            d.date = parseDate(d.date);
            d.lines = +d.lines;
        });

        x.domain(d3.extent(newdata, function(d) { return d.date; }));
        y.domain(d3.extent(newdata, function(d) { return d.lines; }));

        svg.append("g")
        .attr("class", "x axis")
        .attr("transform", "translate(0," + height + ")")
        .call(xAxis);

        svg.append("g")
        .attr("class", "y axis")
        .call(yAxis)
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 6)
        .attr("dy", ".71em")
        .style("text-anchor", "end")
        .text("Lines");

        svg.append("path")
        .datum(newdata)
        .attr("class", "line")
        .attr("d", line);

    };

    var url = $(location).attr('href');
    $.getJSON( url + "data", function(data) {
        console.log(data);
        activity_graph(data["activity"]);
        lines_graph(data["lines"]);
        commits_graph(data["commits"]);
        extensions_graph(data["extensions"]);
    });

});
