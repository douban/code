define('mousetrap', 'lib/mousetrap.js');

require([
        'jquery',
        'jquery-caret',
        'jquery-atwho',
        'jquery-forms',
        'bootstrap',
        'lib/pixastic.custom',
        'mod/liveupdate',
        'mod/input-ext',
        'mod/quick_emoji',
        'mod/user_following',
        'mod/watch',
        //'mod/commit',  // delegate of .js-comment-edit-button // plz refac...
        'mod/diff',   // diff js
        'mod/user_profile_card',
        'mod/tasklist',
        'mod/mute',
        'mousetrap',
        'mod/pull_key',
    ],
    function ($, _, _, _, _, _, live, inputExt, quick_emoji, userFollowing) {
        $(function () {
            var channel_id = "code_pr_"+$('.discussion-tab-link').attr('data-url');
            var linecomment_channel_id = channel_id + 'linecomment';
            live.emit('ready', {channel: channel_id, msg: ''});
            $('textarea#new_comment_content').live(
                'keypress',
                (function (e) {
                    var username = $('textarea#new_comment_content').data('current-user');
                    live.emit('ready', {channel: channel_id, type: 'typing', username: username});
                })
            );

            // pull-nav
            var getAnchor = function (url) {
                var index = url.indexOf('#');
                if (index != -1) {
                    return url.substring(index + 1);
                }
                return '';
            };
            var loadTabContent = function (tab, isFirstLoad) {
                var container = $('#' + $(tab).attr('data-tab-container')),
                    url = $(tab).attr('data-j-url');

                if (container && container.children().length == 0) {
                    $('.loader').show();
                    container.load(url, {}, function () {
                        $('.loader').hide();
                        if (container.is('#discussion-pane') || container.is('#files-pane') || container.is("#commits-pane")) {
                            loadMergeGuide(container, function(st){
                                window.initState = st;
                            });

                            loadCommentInputExt();

                            $('#watch-ci').on('click', function(){
                                if ($(this).attr('checked')) {
                                    CINotification.init();
                                    window.ciWatcher = window.setInterval(function(){
                                        loadMergeGuide(container, function(st){
                                            var msg, prName = $('h2').text();
                                            if (st !== window.initState) {
                                                if (st === 'clean') {
                                                    msg = 'PR "'+ prName +'" can merge now';
                                                    clearTimeout(window.ciWatcher);
                                                } else if (st === 'error') {
                                                    msg = 'PR "'+ prName +'" occurred an error';
                                                    window.initState = 'error';
                                                } else if (st === 'dirty') {
                                                    msg = 'PR "'+ prName +'" got a qaci';
                                                    window.initState = 'dirty';
                                                } else {
                                                    msg = 'Something wrong... ping xutao!'
                                                }
                                                CINotification.create('Code need your Attention!', msg);
                                            }
                                        });
                                    }, 5000);
                                } else {
                                    clearTimeout(window.ciWatcher);
                                }
                            });

                        }
                        if (isFirstLoad) {
                            var anchor = getAnchor(location.href);
                            if (anchor !== '') {
                                var anchorEl = $(document.getElementById(anchor));
                                if (anchorEl.length > 0) {
                                    $('html, body').animate({scrollTop:anchorEl.offset().top}, 500);
                                }
                            }
                        }
                    });
                }
            };

            /* notification */
            var CINotification = {
                init: function () {
                    var webkitNotify = window.webkitNotifications,
                        notify = window.Notification;

                    if (webkitNotify) {
                        var st = webkitNotify.checkPermission();
                        if (st === 1) {
                            webkitNotify.requestPermission();
                        } else if (st === 2) {
                            alert('你拒绝了通知授权，请在通知设置里打开。')
                        }
                    } else if (notify && notify.permission !== "granted") {
                        notify.requestPermission(function (status) {
                            if (notify.permission !== status) {
                                notify.permission = status;
                            }
                        });
                    }
                },

                create: function(title,msg) {
                    var webkitNotify = window.webkitNotifications,
                        notify = window.Notification,
                        icon = '/static/img/code_lover.png';

                    if (webkitNotify) {
                        if (webkitNotify.checkPermission() != 0) {
                            message.init();
                        } else {
                            var n = webkitNotify.createNotification(icon,title, msg);
                            n.show();
                            /*
                            n.ondisplay = function() { };
                            n.onclose = function() { };
                            setTimeout(function(){n.cancle}, 5000);
                            */
                        }
                    } else if (notify) {
                        if (notify.permission == "granted") {
                            var n = new notify(title, { icon: icon, body: msg });
                        } else {
                            message.init();
                        }
                    }
                }
            }

            $('.pull-nav a[data-toggle="tab"]').on('show', function (e) {
                window.history.pushState('', '', $(e.target).attr('data-url'));
                loadTabContent($(e.target), false);
            });
            loadTabContent($('.pull-nav .active a'), true);
            var tabUrls = [], tabs = {};
            $('.pull-nav a[data-toggle="tab"]').each(
                function (i, t) {
                    var url = $(t).attr('data-url');
                    tabUrls.push(url);
                    tabs[url] = $(t);
                });
            $(window).bind(
                "popstate", function(e) {
                    var location = e.target.location,
                    path = location.href.split(location.protocol + '//' + location.host)[1],
                    anchorIndex = path.indexOf('#');
                    if (anchorIndex !== -1) {
                        path = path.substring(0, anchorIndex);
                    }
                    if (path) {
                        for (var i=0, l=tabUrls.length; i<l; i++) {
                            if (path === tabUrls[i]) {
                                tabs[tabUrls[i]].tab('show');
                                break;
                            }
                        }
                    }
                });

            // ticket-content-edit-form
            $('#ticket-content-edit-form').ajaxForm({
                dataType: 'json',
                delegation: true,
                success: function(r) {
                    if (r.r == '0') {
                        var ticket = $('#ticket');
                        ticket.find('h2').html(r.title_html);
                        ticket.find('.comment-content .comment-body').html(r.content_html);
                        // update ticket content in edit form
                        $('#ticket-content-edit-form').find('#issue_title').val(r.title);
                        $('#ticket-content-edit-form').find('#issue_body').val(r.content);
                    }
                    $('#ticket .comment-content').removeClass('is-comment-editing');
                }
            });

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

            $('#discussion-pane').delegate('.comment-edit-button', 'click', function () {
                $('#ticket .comment-content').addClass('is-comment-editing').find('.form-content').show();
            });
            $('#discussion-pane').delegate('.comment-cancel-button', 'click', function () {
                $('#ticket .comment-content').removeClass('is-comment-editing');
            });

            $('#discussion-pane').delegate(
                '#fav-button', 'click', function (e) {
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

            // diff_image
            $('#files-pane').delegate('#diff_image', 'click', function() {
                var imgid = $(this).attr("imgid");
                $("#org_image_div_"+imgid).hide();
                $("#diff_image_div_"+imgid).show();
                Pixastic.process(
                    document.getElementById("result_pic_"+imgid),
                    "blend",
                    {
                        mode: "difference",
                        image: $("#new_pic_"+imgid).get(0)
                    }
                );
            });
            $('#files-pane').delegate('#up_image', 'click', function(){
                var imgid = $(this).attr("imgid");
                $("#org_image_div_"+imgid).show();
                $("#diff_image_div_"+imgid).hide();
            });

            // pull files-pane patch toggle
            $('body').delegate('#files-pane #files div.meta', 'click', function(e){
                if (!$(e.target).parents('.actions').length > 0){
                    var inline = $(this).siblings('div .inline');
                    var side = $(this).siblings('div .side');
                    if (inline.css('display') === 'none' && side.css('display') === 'none'){
                        inline.show();
                        side.hide();
                    }else{
                        inline.hide();
                        side.hide();
                    }
               }
            });

            // merge guide
            var loadMergeGuide = function (container, cb) {
                if (!container)
                    return;
                var mergeGuide = container.find('#merge-guide');
                if (mergeGuide.length) {
                    var url = mergeGuide.attr('data-url');
                    mergeGuide.load(
                        url,
                        function () {
                            var mergeForm = mergeGuide.find('.merge-form'),
                            cancelBtn = mergeGuide.find('#merge-pr-cancel-btn');
                            mergeGuide.find('#merge-pr-confirm-btn').click(function () {
                                $(this).closest('.mergeable.clean').hide();
                                mergeForm.show();
                            });
                            cancelBtn.click(function () {
                                if (!$(this).hasClass('disabled')) {
                                    mergeForm.hide();
                                    mergeGuide.find('.mergeable.clean').show();
                                }
                            });
                            mergeForm.submit(function () {
                                $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                                cancelBtn.addClass('disabled');
                                var username = $('textarea#new_comment_content').data('current-user');
                                live.emit('ready', {channel: channel_id, type: 'merge', username: username});
                                return true;
                            });

                            cb(container.find('.merge-branch').data('mst'));
                        }
                    );
                }
            };

            $('#discussion-pane').delegate('#add-comment-form #close', 'click', function () {
                var commentForm = $('#add-comment-form');
                if (commentForm.find('[name=comment_and_close]').length == 0) {
                    var input = $('<input>').attr('type', 'hidden').attr('name', 'comment_and_close').val('1');
                    commentForm.append(input);
                }
            });

            $('#discussion-pane').delegate('#add-comment-form #reopen', 'click', function () {
                var commentForm = $('#add-comment-form');
                if (commentForm.find('[name=comment_and_reopen]').length == 0) {
                    var input = $('<input>').attr('type', 'hidden').attr('name', 'comment_and_reopen').val('1');
                    commentForm.append(input);
                }
            });

            $('#discussion-pane').delegate('.outdated_mark', 'click', function () {
                $(this).toggle();
                $(this).next().toggle();
            });

            // delete pr comment
            $('#discussion-pane').delegate('.change-header .delete-pr-note-button', 'click', function (e) {
                if (!confirm('Are you sure you want to delete this?')) {
                    return false;
                }
                var comment = $(this).parents('.change');
                var avatar = comment.prev('.side-avatar');
                $.getJSON(
                    $(this).attr('href'),
                    function(r) {
                        if (r.r == '1'){
                            comment.remove();
                            avatar.remove();
                        }
                    }
                );
                return false;
            });

            $('#add-comment-form').ajaxForm({
                dataType: 'json',
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
                        } else if (r.html) {
                            commentForm.find('textarea').val('');
                            $('#changelog').append(r.html);
                            live.emit('ready', {channel: channel_id, msg:r.html});
                        }
                    } else if(r.error){
                        alert(r.error);
                    }
                    commentForm.removeClass('submitting').find('button[type="submit"]').attr('disabled', false)
                    .removeClass('disabled').end().find('.loader').hide();
                    return true;
                }
            });

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

            var loadCommentInputExt = function () {
                if ($('#participants').length > 0) {
                    var participants = JSON.parse($('#participants').val());
                    var teams = JSON.parse($('#all-teams').val() || '[]');
                    var following = userFollowing.val();
                    var users = $.unique(
                        participants.concat(following, teams)
                    );
                    $('textarea#new_comment_content, textarea#issue_body')
                        .atwho("@", {data:users, limit:7});
                }
                var newCommentInput = $('textarea#new_comment_content');
                inputExt.enableEmojiInput(newCommentInput);
                inputExt.enablePullsInput(newCommentInput);
                inputExt.shortcut2submit(newCommentInput);
                inputExt.enableZenMode(newCommentInput);
                inputExt.enableQuickQuotes(newCommentInput);

                var uploader = $('#form-file-upload'),
                    textarea = $('#add-comment-form').find('textarea');
                inputExt.enableUpload(uploader, textarea);

                $('#add-comment-form button[type="submit"]').tooltip();
            };
          loadCommentInputExt();

         });

        quick_emoji.enable('#new_comment_content');
    }
);
