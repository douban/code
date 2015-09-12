/*
使用commit graph：
 - 必须有id属性
 - 元素加上class="commit-graph"
 - 设置data-source：/<repo_name>/graph/commits
 - 设置data-color

TODO: 等后端可以获取owner的commits统计时可以生成participation graph
*/

define('d3', ['lib/d3-3.3.3.js'], function() {
    return d3;
});

define('mod/commit_graph', [
    'jquery',
    'd3'
], function() {
    $('.commit-graph').each(function() {
        var id = $(this).attr('id'),
            url = $(this).attr('data-source'),
            color = $(this).attr('data-color') || '#f5f5f5',
            width = $(this).width(),
            height = $(this).height();

        $.getJSON(url, function(data) {
            var w = (width - data.total) / data.total,
                h = height;

            var x = d3.scale.linear()
                .domain([0, 1])
                .range([0, w]);

            var y = d3.scale.linear()
                .domain([0, height])
                .rangeRound([0, h]);

            var chart = d3.select('#' + id).append('svg')
                          .attr('class', 'chart')
                          .attr('width', width)
                          .attr('height', height);
            chart.selectAll('rect').data(data.all)
                .enter().append('rect')
                .attr('x', function(d, i) {
                   return x(i) + 1 * i;
                })
                .attr('y', function(d) {
                   return h - y(d * h);
                })
                .attr('width', w)
                .attr('height', function(d) {
                   return y(d * h);
                })
                .attr('fill', color);
        });
    });
});
