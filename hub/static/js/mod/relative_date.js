define('mod/relative_date', [
    'jquery',
    'lib/date.extensions'
], function($) {
    var updateRelativeDate = function () {
        $('.js-relative-date').each(
            function (i, el) {
                var el = $(el);
                var t = (el.attr('datetime') || el.attr('data-time')).split(/[- : + T]/);
                var d = new Date(t[0], t[1]-1, t[2], t[3], t[4], t[5]);
                !isNaN(d.getTime()) && el.html(d.toRelativeTime({nowThreshold:60*1000}));
            });
    };
        return updateRelativeDate;
    });
