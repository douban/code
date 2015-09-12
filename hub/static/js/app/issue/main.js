define('mousetrap', 'lib/mousetrap.js');
define('tag-it', 'lib/tag-it.js');

require(['jquery',
        'jquery-caret',
        'jquery-atwho',
        'jquery-forms',
        'bootstrap',
        'lib/pixastic.custom',
        'mod/liveupdate',
        'mod/relative_date',
        'mod/input-ext',
        'mod/user_following',
        'mod/user_avatar',
        'mod/watch',
        'mod/user_profile_card',
        'mod/tasklist',
        'mod/issue_body',
        'tag-it',
        'mousetrap'],
        function ($, _, _, _, _, _, live, updateRelativeDate, inputExt, userFollowing) {
            $(function () {
                // FIXME: comment edit后不显示相对时间

                // liveupdate
                var channel_id = "code_issue_"+$('#issue').attr('data-url');

                // people in room
                live.emit('ready', {channel: channel_id, msg: ''});
                $('textarea#new_comment_content').live('keypress', (function(e) {
                    var username = $('textarea#new_comment_content').data('current-user');
                    live.emit('ready', {channel: channel_id, type: 'typing', username: username});
                }));

                // new comment
                $('#add-comment-form').ajaxForm(
                    {dataType: 'json',
                        delegation: true,
                        beforeSend: function () {
                            var commentForm = $('#add-comment-form');
                            commentForm.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                            .end().find('.loader').show();
                        },
                        success: function(r) {
                            var commentForm = $('#add-comment-form');
                            if (r.r == 0) {
                                if (r.reload && r.redirect_to) {
                                    window.location.href = r.redirect_to;
                                    return true;
                                } else if (r.html && r.participants_html) {
                                    commentForm.find('textarea').val('');
                                    $('#changelog').append(r.html);
                                    $('#participants-block').html(r.participants_html);
                                    live.emit('ready', {channel: channel_id, msg:r.html});
                                }
                            } else if(r.error){
                                alert(r.error);
                            }
                            commentForm.removeClass('submitting').find('button[type="submit"]').attr('disabled', false)
                            .removeClass('disabled').end().find('.loader').hide();
                            updateRelativeDate();
                            return true;
                        }});

                        // inputExt
                        var loadCommentInputExt = function () {
                            var participants = JSON.parse($('#participants').val() || '[]');
                            var teams = JSON.parse($('#all-teams').val() || '[]');
                            var following = userFollowing.val();
                            var users = $.unique(
                                participants.concat(following, teams)
                            );
                            $('textarea#new_comment_content, textarea#issue_body')
                                .atwho("@", {data:users, limit:7});

                            var newCommentInput = $('textarea#new_comment_content');
                            inputExt.enableEmojiInput(newCommentInput);
                            inputExt.enablePullsInput(newCommentInput);
                            inputExt.shortcut2submit(newCommentInput);
                            inputExt.enableZenMode(newCommentInput);
                            inputExt.enableQuickQuotes(newCommentInput);

                            var uploader = $('#form-file-upload'),
                                textarea = $('#add-comment-form').find('textarea');
                            inputExt.enableUpload(uploader, textarea);
                        };
                        loadCommentInputExt();

                        $('#fav-button').click(function (e) {
                                var btn = $(this),
                                data = {tid: btn.data('tid'),
                                        tkind: btn.data('tkind')};
                                if (!btn.hasClass('faved')) {
                                    $.post('/j/fav/', data,
                                           function (r) {
                                               if (r.r == 0) {
                                                   btn.addClass('faved');
                                               }
                                           }, 'json');
                                } else {
                                    $.ajax({url: '/j/fav/',
                                            type: 'DELETE',
                                            data: data,
                                            dataType: 'json',
                                            success: function(r) {
                                                if (r.r == 0) {
                                                    btn.removeClass('faved');
                                                }
                                            }
                                           });
                                }
                        });
            });
        }
);
