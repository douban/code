define('mod/newsfeed', [
    'jquery',
    'mod/user_avatar',
], function($, loadAvatar) {
    $(function () {
        $('.timeline').delegate('.expand-rest', 'click', function(){
            var last = $(this).parents('.expand-last');
            last.prevUntil('.expand-first').show(300);
            last.hide();
            loadAvatar();
        });
     });
});

