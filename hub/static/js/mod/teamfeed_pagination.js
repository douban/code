define('mod/teamfeed_pagination', [
    'jquery',
    'mod/ajax_load',
    'mod/count',
], function($, ajaxLoad, countDict) {
    $(function () {
        var btn = $('.join-or-leave-btn');
        if (btn.length == 0) {
            btn = $('.btn-success');
        }
        var team_uid = btn.attr('data-team');
        $('.timeline .loader').hide();
        $('.timeline .pagination').show().click(
            function () {
                var number_type = "teamfeed_num";
                var url = "/j/more/team/" + team_uid + "/" + countDict.teamfeed_num;
                ajaxLoad(url, number_type);
            });
    });
});
