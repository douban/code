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
