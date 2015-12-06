define(['jquery', 'mousetrap'], function ($, mousetrap)  {
    var keywrap = function (e, action) {
        if (e.srcElement && e.srcElement.tagName == 'BODY') {
            e.preventDefault ? e.preventDefault() : (e.returnValue = false);
            action(e);
        }
    }
    Mousetrap.bind(
        'g g',
        function (e) {
            keywrap(e, function (e) {
                $("html, body").animate({scrollTop: 0});
            });
        }
    );
    Mousetrap.bind(
        'g d',
        function (e) {
            keywrap(e, function (e) {
                var tab = $('.pull-nav a[href="#discussion-pane"]');
                if (tab && !tab.parent().hasClass('active')) {
                    $("html, body").animate({scrollTop: 0});
                    tab.click();
                }
            });
        }
    );
    Mousetrap.bind(
        'g c',
        function (e) {
            keywrap(e, function (e) {
                var tab = $('.pull-nav a[href="#commits-pane"]');
                if (tab && !tab.parent().hasClass('active')) {
                    $("html, body").animate({scrollTop: 0});
                    tab.click();
                }
            });
        }
    );
    Mousetrap.bind(
        'g f',
        function (e) {
            keywrap(e, function (e) {
                var tab = $('.pull-nav a[href="#files-pane"]');
                if (tab && !tab.parent().hasClass('active')) {
                    $("html, body").animate({scrollTop: 0});
                    tab.click();
                }
            });
        }
    );
})
