define('mod/watch', ['jquery'], function($){

  $(function() {
    var watch_btn = $("#watch-btn");
    var countLabel = $('#watched-count');
    var proj_id = watch_btn.attr("proj_id");

    var updateLabelBy = function (n) {
        var count = Number(countLabel.text()) || 0;
        if (count === 0 && n <= 0) { return; }

        count += n;
        countLabel.text(count.toString());
    };

    watch_btn.click(function() {

      if(watch_btn.hasClass('watch')) {
        $.post("/watch/"+proj_id, function(data) {
          if (!data.error) {
            watch_btn.text('Unwatch');
            watch_btn.addClass('unwatch');
            watch_btn.removeClass('watch');
            updateLabelBy(1);
          } else {
            // show error notification to user
            show_error("关注失败");
          }
        });
      }
      else{
        $.ajax("/watch/"+proj_id, {
          type: "DELETE",
          success: function(data) {
            if (!data.error) {
              watch_btn.text('Watch');
              watch_btn.addClass('watch');
              watch_btn.removeClass('unwatch');
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
