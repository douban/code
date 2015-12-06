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
