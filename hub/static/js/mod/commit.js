define('mod/commit', [
    'jquery',
    'jquery-tmpl',
    'jquery-caret',
    'jquery-atwho',
    'jquery-forms',
    'bootstrap',
    'mod/input-ext',
    'mod/liveupdate'
], function ($, _, _, _, _, _, inputExt, live) {
    $(function () {

        // comment & linecomment edit
        $('body').delegate('.js-comment-edit-button', 'click', function (e) {
            var form_content = $(this).parents('.comment-header')
            .next('.comment-content')
            .children('.form-content');
            if (form_content != undefined) {
                form_content.show().find('textarea').focus();
                form_content.find('form.js-comment-update').ajaxForm({
                    dataType: 'json',
                    beforeSend: function() {
                        form_content.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                        .end().find('.loader').show();
                    },
                    success: function(r) {
                        if (r.r == 0 && r.html) {
                            if (form_content.find('textarea').attr('name') === 'pull_request_review_comment'){
                                form_content.parents('.js-comments-holder').append(r.html);
                                form_content.parents('.comment').remove();
                            } else {
                                var comment = form_content.parents('.change');
                                var avatar = comment.prev('.side-avatar');
                                form_content.parents('#changelog').append(r.html);
                                comment.remove();
                                avatar.remove();
                            }
                        }
                        return true;
                    }
                });
            } else {
                return false;
            }
        });

        $('body').delegate('.form-content .comment-cancel-button', 'click', function (e) {
            var form_content = $(this).parents('.form-content');
            if (form_content != undefined) {
                form_content.hide();
            } else {
                return false;
            }
        });

        inputExt.enableEmojiInput($('#new_comment_content'));
        inputExt.shortcut2submit($('#new_comment_content'));

        $('.tabnav-tabs a').live('click', function () {
            $(this).closest('.tabnav-tabs').find('a').removeClass('selected');
            $(this).addClass('selected');
        });

        $('.write-tab').live('click', function () {
            var form = $(this).closest('.previewable-comment-form');
            $(this).closest('.previewable-comment-form').removeClass('preview-selected').addClass('write-selected');
            form.find('#write_bucket').addClass('active').end().find('#preview_bucket').removeClass('active');
        });
        $('.preview-tab').live('click', function () {
            var form = $(this).closest('.previewable-comment-form');
            form.removeClass('write-selected').addClass('preview-selected');
            form.find('#write_bucket').removeClass('active').end().find('#preview_bucket').addClass('active');
            form.find('#preview_bucket p').html("Loading preview...");
            var url = form.find('#preview_bucket .content-body').data('api-url'),
            text = form.find('#write_bucket textarea').val();
            form.find('#preview_bucket .content-body').load(url, {text: text});
        });

        $('#all-comments .delete-btn').click(function(e) {
            e.preventDefault();
            if (!confirm("Are you sure you want to delete this comment?")) {
                return;
            }
            // FIXME: global orig?
            orig = this;
            $.ajax({
                url: this.href,
                type: 'delete',
                dataType: 'json',
                success: function(resp) {
                    $(orig).parents('.comment-row').slideUp('fast');
                },
                error: function(resp) {
                    alert("Unable to delete comment");
                    console.log(resp);
                }
            });
        });
        $(".give_beer").click(function(e) {
            if (!$("#new_comment_content")[0].value) {
                $("#new_comment_content")[0].value = ":beer:";
            }
            $("#new_comment_content").focus();
        });
        $(document).delegate('#toc .minibutton', 'click', function() {
            $('#toc .content').toggle();
        });
        $(".comment-popover").popover({placement:'left'});


        var cform = $('#new_comment');
        cform.submit(function () {
            $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
            return true;
        });

    });
});
