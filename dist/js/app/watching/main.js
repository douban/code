
require.config({ enable_ozma: true });


/* @source  */;

require(['jquery'], function($){
    $(function() {
        var watch_btn = $(".watch-btn");
        var countLabel = $('#watched-count');

        var updateLabelBy = function (n) {
            var count = Number(countLabel.text()) || 0;
            if (count === 0 && n <= 0) { return; }

            count += n;
            countLabel.text(count.toString());
        };

        $.each(watch_btn, function(index,value){
            $(value).click(function() {

                if($(value).hasClass('watch')) {
                    $.post("/watch/"+$(value).attr('proj_id'), function(data) {
                        if (!data.error) {
                            $(value).html('<i class="icon-eye-open"></i> Unwatch');
                            $(value).addClass('unwatch');
                            $(value).removeClass('watch');
                            updateLabelBy(1);
                        } else {
                            // show error notification to user
                            show_error("关注失败");
                        }
                    });
                }
                else{
                    $.ajax("/watch/"+$(value).attr('proj_id'), {
                        type: "DELETE",
                        success: function(data) {
                            if (!data.error) {
                                $(value).html('<i class="icon-eye-open"></i> Watch');
                                $(value).addClass('watch');
                                $(value).removeClass('unwatch');
                                updateLabelBy(-1);
                            } else {
                                show_error("取消关注失败");
                            }
                        },
                        error: function(e) {
                            show_error("取消关注失败");
                        }
                    });
                }
            });

        });

        function show_success(msg) {
            var successDiv = $(".navbar .success");
            if (successDiv.size() === 0 ) {
                successDiv= $("<div>").addClass("success").addClass("alert-success");
                $("div.navbar").append(successDiv);
            }
            successDiv.html(msg);
            successDiv.fadeOut(1500, function () {
                $(this).remove();
            });
        }

        function show_error(msg) {
            var errorDiv = $(".navbar .error");
            if (errorDiv.size() === 0 ) {
                errorDiv = $("<div>").addClass("error").addClass("alert-error");
                $("div.navbar").append(errorDiv);
            }
            errorDiv.html(msg);
        }

    });
});
