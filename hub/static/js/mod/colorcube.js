define(
    ['jquery'],
    function ($) {
        var colorcube = {}, cubeWnd;
        var showCubeWnd = function (el) {
            el = $(el);
            if (!cubeWnd) {
                cubeWnd = $('<div id="color" class="colorcube"></div>').appendTo('body');
            }
            var pos = el.offset();
            pos = {top:pos.top - 40, left:pos.left + el.width()/2 -15};
            cubeWnd.show().offset(pos).css({'background-color':el.data('color')});
        };
        colorcube.init = function (opts) {
            if (opts.target) {
                $(opts.target).delegate(
                    '.line .color', 'mouseenter mouseleave', function (e) {
                        if (e.type === 'mouseenter') {
                            showCubeWnd(this);
                        } else {
                            cubeWnd.hide();
                        }
                    });
            }
        };
        return colorcube;
    }
);
