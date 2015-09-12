define('mousetrap', 'lib/mousetrap.js');

define('mod/chat', [
    'jquery',
    'jquery-atwho',
    'jquery-forms',
    'mod/connect',
    'mod/user_avatar',
    'mod/input-ext',
    'mousetrap',
    'bootbox'
], function ($, _, _, connectNode, loadAvatar, inputExt) {
    $(function () {
        var ajaxGet = function (url, nowMessageId) {
            $.ajax({type: "GET",
                    url: url,
                    dataType: "json",
                    success: function (data) {
                        if (data.r === 0) {
                             $(".alert-error").show();
                             location.hash = '#lobby';
                             return;
                        }

                        var messages = data.msg;
                        for (var i = 0; i < messages.length; i++) {
                            nowMessageId.append(messages[i]);
                        }
                        loadAvatar();
                        var $d = nowMessageId;
                        $d[0].scrollTop = $d[0].scrollHeight;
                        $('#message_input').focus();
                    }
            });
        };

        var roomName = "lobby";
        if (location.hash.slice(1)) {
            roomName = location.hash.slice(1);
        }
        var channelPrefix = "chat:room:";
        var roomChannel = channelPrefix + roomName;
        var io = connectNode(roomChannel);
        io.on('announce', function(data) {
            var channel = data.channel;
            var room = channel.split(':')[2];
            $('#'+room).append(data.send_message);
            loadAvatar();
            var $d= $('#'+room);
            $d[0].scrollTop = $d[0].scrollHeight;
        });
        var sliceUrl = '#' + roomName;
        var lastActive = $('[href=' + sliceUrl + ']').parents('li');
        lastActive.attr("class", "active");
        var lastMessageId = $("#"+roomName);
        var nowMessageId = $("#"+roomName);
        lastMessageId.hide();
        nowMessageId.show();
        nowMessageId.html('');

        var urlPrefix = "/j/chat/";
        var url = urlPrefix + roomName;
        $('#message-form').attr('action', url);
        ajaxGet(url, nowMessageId);

        $(window).on('hashchange',function(){
            roomName = location.hash.slice(1);
            sliceUrl = '#' + roomName;
            var needActive = $('[href='+sliceUrl+']').parents('li');
            lastActive.attr("class", "");
            needActive.attr("class", "active");
            lastActive = needActive;

            url = urlPrefix + roomName;
            $('#message-form').attr('action', url);
            lastMessageId.hide();
            nowMessageId = $('#'+roomName);
            nowMessageId.show();
            nowMessageId.html('');
            lastMessageId = nowMessageId;

            ajaxGet(url, nowMessageId);
                        
            roomChannel = channelPrefix + roomName;
            io.emit('ready', {channel:roomChannel});
        });

        $('#message_input').focus();
        var messageInput = $('textarea#message_input');
        inputExt.shortcut2submit(messageInput);
        inputExt.enableEmojiInput(messageInput);
        $('#message-form').ajaxForm({
            dataType: 'json',
            success: function(r) {
                if (r.r === 1) {
                    $('#message_input').val('');
                    $('#message_input').focus();
                    $('#message_input').closest('form').removeClass('submitting');
                }
            }
        });

        $('.del-room').on('click', function () {
            var roomName = $(this).attr("data-name"),
                roomItem = $(this),
                msg = '你确定要删除room: ' + roomName + '?';
            
            if (roomName) {
                bootbox.confirm(msg, function(confirmed) {
                    if (confirmed) {
                        $.post(urlPrefix + 'delete_room', {'room_name': roomName}, 
                               function (ret) { 
                                   if (ret.r === 1) {
                                        var li = roomItem.parents('li');
                                        li.remove();
                                   }
                               },
                               'json'
                               );
                    }
                });
            }
        });
    });
});
