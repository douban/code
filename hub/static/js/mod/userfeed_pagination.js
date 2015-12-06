define('mod/userfeed_pagination', [
    'jquery',
    'mod/ajax_load',
    'mod/count',
], function($, ajaxLoad, countDict) {
    $(function () {
        $('.timeline .loader').hide();
        $('.timeline .pagination').show().click(
            function () {
                var number_type = "userfeed_num";
                var url = "/j/more/userfeed/" + countDict.userfeed_num;
                ajaxLoad(url, number_type);
        });
    })
});

