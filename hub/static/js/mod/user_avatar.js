define('mod/user_avatar', [
    'jquery',
    'jquery-lazyload'
], function($, _) {
    var isRetinaDisplay = window.devicePixelRatio > 1;

    var patchForRetina = function(originalURL) {
      var match = /^(.+\Ws=)(\d+)(.*)$/.exec(originalURL);
      if (match === null) {
        return originalURL;
      }

      var oldSize = parseInt(match[2], 10);
      var newSize = Math.ceil(window.devicePixelRatio * oldSize);

      return match[1] + newSize.toString(10) + match[3];
    };

    var checkLoad = function() {
        var e = $(this);
        if (isRetinaDisplay) {
            var dataOriginalURL = e.attr('data-original') || e.attr('src');
            e.attr('data-original', patchForRetina(dataOriginalURL));

            e.lazyload({effect:"fadeIn", threshold:300});
        }
    };

    var loadAvatar = function () {
        // $("img.user-avatar").each(checkLoad);
        // $("img.avatar").each(checkLoad);
        // $(window).resize();
    };
    return loadAvatar;
});
