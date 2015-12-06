define('cal-heatmap', 'lib/cal-heatmap.js');

require(['jquery',
        'cal-heatmap',
        'mod/badge_info',
        'mod/praise',
        'mod/commit_graph',
        'mod/follow',
        'mod/newsfeed'],
        function($, _, _, _, _, follow){
            $('.timeline .loader').hide();
            $(function () {
                var currentURL = location.href.split('?')[0];  // remove the querystring

                if (typeof CalHeatMap != 'undefined') {
                    var getDetailByDate = function (date) {
                        $.get(currentURL + 'contribution_detail', {date:date.toISOString()},
                              function (r) {
                                  $('#contribution-details').html(r);
                              }
                             );
                    };

                    var today = new Date();
                    var cal = new CalHeatMap();
                    cal.init({id: 'cal-heatmap',
                             data: currentURL + 'contributions',
                             start: new Date(today.setMonth(today.getMonth() - 6)),
                             domain: 'month',
                             subDomain: 'day',
                             range: 8,
                             cellsize: 12,
                             onClick: function(date, count) {
                                 getDetailByDate(date);
                             }});
                    // get contribution of yesterday by default
                    var d = new Date();
                    getDetailByDate(new Date(d.setDate(d.getDate() - 1)));
                }

                follow.button(".follow-btn .btn");
            });
        });
