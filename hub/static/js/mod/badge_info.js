define('mod/badge_info', [
    'jquery',
    'jquery-lazyload',
    'bootstrap',
    'mustache'
], function($, _, Mustache) {

    $(function() {
        $("img.badgeInfo").lazyload();
        $(".badgeInfo").each(function(){
            var options = {
                title: $(this).attr('data-title'),
                content: $(this).attr('data-reason')
            };
            $(this).popover(options);
        });
    });

});
