define('mod/fetch', ['jquery'], function($){

  $(function() {
    var fetch_btn = $("#fetch-btn");
    var proj_id = fetch_btn.attr("proj_id");

    fetch_btn.click(function() {
        $.ajax("/fetch/"+proj_id, {
          type: "POST",
          success: function(data) {
            if (!data.error) {
                show_success("后台已经开始更新仓库，请耐心等待.");
            } else {
              show_error("仓库更新失败.");
            }
          },
          error: function(e) {
            show_error("仓库更新失败.");
          }
        });
    });

    function show_success(msg) {
        var successDiv = $(".navbar .success");
        if (successDiv.size() === 0 ) {
            successDiv= $("<div>").addClass("success").addClass("alert-success").addClass("alert");
            $("div.pagehead").append(successDiv);
        }
        successDiv.html(msg);
        successDiv.fadeOut(5000, function () {
            $(this).remove();
        });
    }

    function show_error(msg) {
        var errorDiv = $(".navbar .error");
        if (errorDiv.size() === 0 ) {
            errorDiv = $("<div>").addClass("error").addClass("alert-error").addClass("alert");
            $("div.pagehead").append(errorDiv);
        }
        errorDiv.html(msg);
    }

  });
});
