define('mod/ajax_load', [
    'jquery',
    'mod/count',
    'mod/relative_date',
    'mod/user_avatar',
], function($, countDict, updateRelativeDate, loadAvatar) {
    var ajaxLoad = function(url, number_type) {
        var maxShown = 35;
        $.ajax({type: "GET",
                url: url,
                dataType: "json",
                beforeSend: function() {
                    $('.timeline .loader').show();
                },
                success: function(data) {
                    var result = data.result;
                    var length = data.length;

                    $('.timeline>ul').append(result);
                    $('.timeline .loader').hide();
                    if (length < maxShown) {
                        $('.timeline .pagination').hide();
                    } else {
                      countDict[number_type] += maxShown;
                    }
                    updateRelativeDate();
                    loadAvatar();
                }
        });
    };

    return ajaxLoad;
});
