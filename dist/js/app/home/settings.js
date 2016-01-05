
require.config({ enable_ozma: true });


/* @source mod/proj_del_btn.js */;

define('mod/proj_del_btn', [
  "jquery",
  "bootbox"
], function($) {
    var delProj = function (proj, onSuccess) {
        bootbox.confirm("Are you sure?", function(confirmed) {
            if (confirmed) {
                $.post('/' + proj + '/remove', function (ret) {
                    if (ret.r === 1) {
                        onSuccess();
                    } else {
                        bootbox.alert(ret.err);
                    }
                }, 'json');
            }
        });
    };

    $('.my_projects li').hover(
        function () {$(this).addClass('hover');},
        function () {$(this).removeClass('hover');}
    );

    $('.my_projects li .delete-btn').click(function () {
        var delBtn = $(this), proj = delBtn.attr('data-proj');
        delProj(proj, function () { delBtn.closest('li').remove(); });
    });

    $('#settings-del-proj').click(function () {
        var delBtn = $(this), proj = delBtn.attr('data-proj');
        delProj(proj, function () { window.location = '/'; });
    });
});

/* @source mod/confirm.js */;

define('mod/confirm', [
  "jquery",
  "bootbox"
], function($){

    $("a.confirm").click(function(e) {
        e.preventDefault();
        var location = $(this).attr('href');
        bootbox.confirm("Are you sure?", function(confirmed) {
             if(confirmed){
                 window.location.replace(location);
             }
        });
    });

});

/* @source mod/watch.js */;

define('mod/watch', [
  "jquery"
], function($){

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

/* @source  */;

require(['jquery', 'bootstrap', 'mod/watch', 'mod/confirm', 'mod/proj_del_btn'], function($) {
    // remove committer
    var showRev = function () {
        $(this).children('.del-committer-btn').animate({
            top: '-=23'
        }, 500);
    },
    hideRev = function () {
        $(this).children('.del-committer-btn').animate({
            top: '+=23'
        }, 500);
    },
    delCommitter = function () {
        var username = $(this).prev().attr('title');
        $('#del-committer-modal .username').val(username);
        $('.del-committer-name').text(username);
    },
    delGroup = function () {
        var username = $(this).prev().attr('title');
        $('#del-group-modal .group').val(username);
        $('.del-group-name').text(username);
    };
    $('.info-container .avatar').bind('mouseenter', showRev);
    $('.info-container .avatar').bind('mouseleave', hideRev);
    $('.del-committer-btn').bind('click', delCommitter);
    $('.del-group-btn').bind('click', delGroup);
    $('.js-repository-name').on('keypress keyup keydown focus', function () {
        var rule = /[^0-9A-Za-z_\.]/g;
        var note = $(".js-form-note");
        var button = $(".js-rename-repository-button");
        var $this = $(this);
        note.html("Will be renamed as <code>" + this.value.replace(rule, "-") + "</code>");
        rule.test(this.value) ? note.is(":hidden") && note.fadeIn() : this.value || note.fadeOut();
        this.value && this.value !== $(this).attr("data-original-name") ? button.prop("disabled", !1) : button.prop("disabled", !0);
    });
    $('#product').on('change', function() {
        var select = $(this);
        var project_name = select.data('project-name');
        $.ajax({
            type: 'POST',
            data: JSON.stringify({
                'content': select.val()
            }),
            contentType: 'application/json; charset=UTF-8',
            url: '/api/repos/' + project_name + '/product/',
            dataType: 'json',
            success: function (ret) {
                if (ret.status == 201) {
                    select.find('option:selected').removeAttr('selected');
                    select.find('option[value="' + ret.content + '"]').attr("selected",true);
                }
            }
        });
    });
    $('#update_summary').on('click', function() {
        var btn = $(this);
        var summary = btn.parent().find('#summary')[0].value;
        var project_name = btn.data('project-name');
        $.ajax({
            type: 'POST',
            data: JSON.stringify({
                'content': summary
            }),
            contentType: 'application/json; charset=UTF-8',
            url: '/api/repos/' + project_name + '/summary/',
            dataType: 'json',
            success: function (ret) {
                location.reload();
            }
        });
    });
    $('#intern_banned').on('click', function() {
        var checkbox = $(this);
        var banned = null;
        var type = 'DELETE';
        var project_name = checkbox.data('project-name');
        if (checkbox.attr("checked") == "checked") {
            banned = 'on';
            type = 'POST';
        }
        $.ajax({
            type: type,
            data: JSON.stringify({
                'content': banned
            }),
            contentType: 'application/json; charset=UTF-8',
            url: '/api/repos/' + project_name + '/intern_banned/',
            dataType: 'json',
            success: function (ret) {
                if (ret && ret.content == 'on'){
                    checkbox.prop("checked", "checked");
                }
            }
        });
    });
    $('#default_branch').on('change', function() {
        var select = $(this);
        var project_name = select.data('project-name');
        $.ajax({
            type: 'POST',
            data: JSON.stringify({
                'content': select.val()
            }),
            contentType: 'application/json; charset=UTF-8',
            url: '/api/repos/' + project_name + '/default_branch/',
            dataType: 'json',
            success: function (ret) {
                if (ret.status == 201) {
                    select.find('option:selected').removeAttr('selected');
                    select.find('option[value="' + ret.content + '"]').attr("selected",true);
                }
            }
        });
    });
    $('#can_push').on('click', function() {
        var checkbox = $(this);
        var banned = null;
        var type = 'POST';
        var project_name = checkbox.data('project-name');
        if (checkbox.attr("checked") == "checked") {
            banned = 'on';
            type = 'DELETE';
        }
        $.ajax({
            type: type,
            data: JSON.stringify({
                'content': banned
            }),
            contentType: 'application/json; charset=UTF-8',
            url: '/api/repos/' + project_name + '/can_push/',
            dataType: 'json',
            success: function (ret) {
                if (ret && ret.content == 'on'){
                    checkbox.prop("checked", "checked");
                }
            }
        });
    });
});
