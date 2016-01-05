
require.config({ enable_ozma: true });


/* @source mod/user_avatar.js */;

define('mod/user_avatar', [
  "jquery",
  "jquery-lazyload"
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

/* @source  */;

require(['jquery'
, 'mod/user_avatar'
//, 'mod/notify_pagination'
], function($, loadAvatar) {
    //TODO: add notify realtime show
    //
    $(function () {
        $('.entry').delegate('.entry-title .title', 'click', function(){
            $(this).parent().next().toggle(300);
            loadAvatar();
        });

        var removeSlow = function($this) {
            $this.fadeOut(350, function() { $this.remove();});
        };

        $('.notif-list').delegate('.mark-item', 'click', function (e) {
            var $this = $(this);
            $this.ajaxForm({
                dataType: 'json',
                success: function(r) {
                    if (r.r === 0) {
                        removeSlow($this.parents('.notif-item'));
                    }
                }
            });
        });

        $('.notif-list').delegate('.mark-entry', 'click', function (e) {
            var $this = $(this);
            $this.ajaxForm({
                dataType: 'json',
                success: function(r) {
                    if (r.r === 0) {
                        if ($this.parents('.item-body').children().length == 1) {
                            removeSlow($this.parents('.notif-item'));
                        } else {
                            removeSlow($this.parents('.entry'));
                        }
                    }
                }
            });
        });

        $('.notif-list').delegate('.mute-entry', 'click', function (e) {
            var $this = $(this);
            $this.ajaxForm({
                dataType: 'json',
                success: function(r) {
                    if (r.r === 0) {
                        $this.find('i').removeClass('icon-volume-up').addClass('icon-volume-off');
                    }
                }
            });
        });

        $('.mark-all-as-read').click(function() {
            var $this = $(this),
                type = $this.data('type');
            if(type == 'merged_pr') {
                var form = $('#merged-pr-uids');
                form.ajaxSubmit({
                    success: function() {
                        location.reload();
                    }
                });
            }
        })

    });
});
