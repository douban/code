define('jquery-scrollto', 'lib/jquery.scrollTo.js');
require(['jquery', 'jquery-unobstrusive', 'jquery-scrollto', 'mod/watch', 'jquery-tooltipster'], function($){
    $('.btn-details').tooltipster({
        content: $('<p>If this feature opening. When open a new pull request, all flake8 errors found ' +
                   'by Telchar will send to CODE. visit <a href="http://code.dapps.douban.com/telchar" ' +
                   'target="_blank">Telchar</a></p>'),
        minWidth: 300,
        maxWidth: 300,
        position: 'right',
        interactive: true
    });

    $('.mute').on('click', function (e) {
        var target = $(this);
        $.ajax({
            type: "GET",
            url: target.data('href'),
            dataType: "json",
            success: function (rs) {
                if (rs.r === 0) {
                    var $muteOn = $('.mute-on'),
                        $muteOff = $('.mute-off');
                    if (rs.status === 0) {
                        $muteOn.removeClass('btn-success');
                        $muteOff.addClass('btn-warning');
                    } else {
                        $muteOn.addClass('btn-success');
                        $muteOff.removeClass('btn-warning');
                    }
                }
            }
        });
    });

    $(".js-hook-target").on('click', function (e) {
        var target = $(this);
        var group = $(".js-hook-group");
        target.parents("li").removeClass("selected");
        target.parents("li").addClass("selected");
        group.hide();
        $(this.hash).show().scrollTo();
        e.preventDefault();
    });
});
