define('mod/newsfeed_pagination', [
    'jquery',
    'mod/ajax_load',
    'mod/count',
], function($, ajaxLoad, countDict) {
    $(function () {
        $('.timeline .loader').hide();
        $('.timeline .pagination').show().click(
            function () {
                var number_type = "public_num";
                var url = "/j/more/pub/" + countDict.public_num;
                ajaxLoad(url, number_type);
            });
    });
});
