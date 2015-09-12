require(
    ['jquery',
    'mod/relative_date',
    'mod/user_avatar',
    'jquery-tmpl',
    'mod/input-ext'], function ($, updateRelativeDate, loadAvatar) {
        var tmpl = $("#tmpl-timeline-activity");
        //previewable-comment-form
        $('.previewable-comment-form .js-preview-tabs a.preview-tab').on('show', function(e) {
            $('#preview_bucket p').html("Loading preview...");
        }).on('shown', function(e) {
            var url = $('#preview_bucket .content-body').data('api-url');
            var text = $('#write_bucket textarea').val();
            $('#preview_bucket .content-body').load(url, {text: text});
        });

        $('.timeline .loader').hide();
        $('.timeline .pagination').show().click(
            function () {
                var id = $('.timeline .activity .action').length;
                var url = "/api/center/activity/?start=" + id + "&limit=10";
                $.ajax({type: "GET",
                        url: url,
                        dataType: "json",
                        beforeSend: function() {
                            $('.timeline .loader').show();
                        },
                        success: function(data) {
                            for (var x in data) {
                                $('.timeline .activity').append($.tmpl(tmpl, data[x]));
                            }
                            $('.timeline .loader').hide();
                            if (data.length < 10) {
                                $('.timeline .pagination').hide();
                            }
                            updateRelativeDate();
                            loadAvatar();
                        }
                });
            });
    }
);

