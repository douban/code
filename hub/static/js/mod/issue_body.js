define('mod/issue_body', ['jquery', 'mod/upvote', 'mod/quick_emoji', 'tag-it'], function($, upvote, quick_emoji) {
    $(function(){

        // edit issue
        $('#issue-content-edit-form').ajaxForm(
            {dataType: 'json',
             delegation: true,
             success: function(r) {
                 if (r.r == '0') {
                     var issue = $('#summary');
                     issue.find('h2').html(r.title_html);
                     issue.find('.description .markdown-body').html(r.content_html);
                     // update ticket content in edit form
                     var form = $('#issue-content-edit-form');
                     form.find('#issue_title').val(r.title);
                     form.find('#issue_body').val(r.content);
                 }
                 $('#summary .content').removeClass('is-comment-editing').find('.form-content').hide();
        }});

        // close & open
        $('#issue').delegate(
            '#add-comment-form #close', 'click', function () {
                var commentForm = $('#add-comment-form');
                if (commentForm.find('[name=comment_and_close]').length == 0) {
                    var input = $('<input>').attr('type', 'hidden').attr('name', 'comment_and_close').val('1');
                    commentForm.append(input);
                }
            });

        $('#issue').delegate(
            '#add-comment-form #open', 'click', function () {
                var commentForm = $('#add-comment-form');
                if (commentForm.find('[name=comment_and_open]').length == 0) {
                    var input = $('<input>').attr('type', 'hidden').attr('name', 'comment_and_open').val('1');
                    commentForm.append(input);
                }
            });

        // delete comment
        $('#issue').delegate(
            '.delete-pr-note-button', 'click', function (e) {
                if (!confirm('Are you sure you want to delete this?')) {
                    return false;
                }
                var comment = $(this).parents('.change');
                $.getJSON($(this).attr('href'),
                        function(r) {
                            if (r.r == '1'){
                                comment.remove();
                            }
                        });
                return false;
        });

        // tabs
        $('.write-tab').live(
            'click',
            function () {
                var form = $(this).closest('.previewable-comment-form');
                $(this).closest('.previewable-comment-form').removeClass('preview-selected').addClass('write-selected');
                form.find('#write_bucket').addClass('active').end().find('#preview_bucket').removeClass('active');
            });
        $('.preview-tab').live(
            'click',
            function () {
                var form = $(this).closest('.previewable-comment-form');
                form.removeClass('write-selected').addClass('preview-selected');
                form.find('#write_bucket').removeClass('active').end().find('#preview_bucket').addClass('active');
                form.find('#preview_bucket p').html("Loading preview...");
                var url = form.find('#preview_bucket .content-body').data('api-url'),
                text = form.find('#write_bucket textarea').val();
                form.find('#preview_bucket .content-body').load(url, {text: text});
            });

        // join issue
        var JoinOrLeaveIssue = function (url, onSuccess) {
            $.post(url, function (ret) {
                if (ret.r === 0) {
                    onSuccess();
                    if (ret.participants_html) {
                        $('#participants-block').html(ret.participants_html);
                    }
                } else if (ret.r === 1 && ret.msg) {
                    alert(ret.msg);
                }
            }, 'json');
        };
        $('.join-issue-btn').click(function () {
            var Btn = $(this), _type = Btn.attr('data-type'),
                url = Btn.attr('data-url') + _type;
            if (_type === "leave") {
                JoinOrLeaveIssue(url, function () {
                    Btn.removeClass('btn-danger');
                    Btn.html('Join');
                    Btn.attr('data-type', 'join');
                });
            } else {
                JoinOrLeaveIssue(url, function () {
                    Btn.addClass('btn-danger');
                    Btn.html('Leave');
                    Btn.attr('data-type', 'leave');
                });
            }
        });

        // edit button
        $('#issue').delegate(
            '.js-edit-button', 'click',
            function () {
                var comment_content = $(this).parents('.js-edit-container').addClass('is-comment-editing').children('.content');
                //comment_content.addClass('is-comment-editing');
                comment_content.find('.form-content').show();
            });

        $('#issue').delegate(
            '.js-cancel-button', 'click',
            function () {
                var comment_content = $(this).parents('.js-edit-container');
                comment_content.removeClass('is-comment-editing');
                comment_content.find('.form-content').hide();
            });

        $('body').delegate('.js-edit-button', 'click',
            function (e) {
                var form_content = $(this).parents('.js-edit-container')
                                    .children('.content')
                                    .children('.form-content');
                if(form_content != undefined){
                    form_content.show().find('textarea').focus();
                    form_content.find('form.js-comment-update').ajaxForm(
                    {
                        dataType: 'json',
                        beforeSend: function() {
                        form_content.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                        .end().find('.loader').show();
                        },
                        success: function(r) {
                            if (r.r == 0 && r.html) {
                                if (form_content.find('textarea').attr('name') === 'pull_request_review_comment'){
                                    // FIXME:
                                    form_content.parents('.js-comments-holder').append(r.html);
                                    form_content.parents('.comment').remove();
                                } else {
                                    var comment = form_content.parents('.change');
                                    form_content.parents('#changelog').append(r.html);
                                    comment.remove();
                                }
                            }
                            return true;
                        }
                      }
                    );
                }else{
                    return false;
                }
            }
        );

        $('body').delegate('.form-content .comment-cancel-button', 'click',
            function (e) {
                var form_content = $(this).parents('.form-content');
                if(form_content != undefined){
                    form_content.hide();
                }else{
                    return false;
                }
            }
        );

        // others
        quick_emoji.enable('#new_comment_content');
        upvote.button("#upvote");

        // tag
        $('#issue-tags').tagit({input_name: 'tags', tag_list: $('.label'), fillup: JSON.parse($("#json-tags")[0].value)});

        $('.milestone-menu').delegate('a', 'click',
            function (e) {
                var $a = $(this);
                clear_milestone();
                $a.parent().addClass('active').find('input').attr('checked', true);;
            }
        );
        $('#milestone_title').on('keypress keyup keydown focus', function () {
            var $this = $(this);
            var value = $this.val();
            console.log(value);
            if (value && value !== "") {
                clear_milestone(true);
                $("#milestone_new").attr('checked', true);
            } else {
                clear_milestone();
            }
        });
        var clear_milestone = function (hide) {
            var $menu = $('.milestone-menu');
            $menu.find('li').each(function () {
                $(this).removeClass("active");
            });
            if (hide) {
                $menu.hide();
            } else {
                $menu.show();
            }
        };

    });
})
