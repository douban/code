define('mousetrap', 'lib/mousetrap.js');

define(
    ['jquery', 'mod/user_following','jquery-caret', 'jquery-atwho', 'mousetrap', 'lib/zen-form'],
    function ($, userFollowing) {
        var inputExt = {};
        var emojis = [
            'airplane', 'alien', 'art', 'bear', 'beer', 'bike', 'bomb', 'book',
            'bulb', 'bus', 'cake', 'calling', 'clap', 'cocktail', 'code', 'computer',
            'cool', 'cop', 'email', 'feet', 'fire', 'fish', 'fist', 'gift', 'hammer',
            'heart', 'iphone', 'key', 'leaves', 'lgtm', 'lipstick', 'lock', 'mag', 'mega',
            'memo', 'moneybag', 'new', 'octocat', 'ok', 'palm_tree', 'pencil', 'punch',
            'runner', 'scissors', 'ship', 'shipit', 'ski', 'smile', 'smoking', 'sparkles',
            'star', 'sunny', 'taxi', 'thumbsdown', 'thumbsup', 'tm', 'tophat', 'train',
            'trollface', 'v', 'vs', 'warning', 'wheelchair', 'zap', 'zzz', 'see_no_evil',
            'hear_no_evil', 'speak_no_evil', 'monkey', 'monkey_face', 'manybeers', 'beers',
            'hhkb', 'ruby'
        ], emoji_list = $.map(emojis, function(value, i) {return {key: value + ':', name:value};});
        inputExt.enableEmojiInput = function (el) {
            el.atwho('(?:^|\\s):',
                     {data:emoji_list, limit:7,
                         tpl:'<li data-value="${key}">${name} <img src="/static/emoji/${name}.png" height="20" width="20" /></li>'});
                         return el;
        };

        inputExt.enableAutoCompleteFollowingAndTeam = function (el) {
            var teams = JSON.parse($('#all-teams').val() || '[]');
            var users = teams.concat(userFollowing.val());

            $(el).atwho("@", {
                data: users,
                limit: 7
            });
        };

        // 输入#自动提示pr信息
        inputExt.enablePullsInput = function (el) {
            var projectName = el.attr('data-project-name');
            if (!projectName) return el;
            $.getJSON('/' + projectName + '/pulls/all_data', function (r) {
                var pulls = $.map(
                    r, function(value, i) {
                    return {key: value.id, name:value.id + ' ' + value.title, title:value.title};
                });
                el.atwho('(?:^|\\s)#',
                         {data:pulls, limit:7,
                             tpl:'<li data-value="${key}"><small>#${key}</small> ${title}</li>'});
            });
            return el;
        };

        inputExt.shortcut2submit = function (el) {
            Mousetrap.bind(
                ['command+enter', 'ctrl+enter'],
                function (e) {
                    if (el && (e.srcElement || e.target) == $(el)[0] && !$(el).closest('form').hasClass('submitting')) {
                        e.preventDefault ? e.preventDefault() : (e.returnValue = false);
                        $(el).closest('form').addClass('submitting').submit();
                    }
                },
                'keydown'
            );
        };

        // 进入全屏模式
        inputExt.enableZenMode = function (el) {
            var trigger = '.go-zen';
            el = $(el);
            el.zenForm({trigger:trigger, theme:'light'}).dblclick(function(e) {
                if (!e.altKey) return;
                $(this).zenForm({ trigger: null, theme: 'light' });
                fix();
            });

            $(trigger).click(fix);

            function fix() {
                var textarea = $('.zen-forms-input-wrap textarea');
                if (textarea) {
                    inputExt.enableEmojiInput(textarea);
                    textarea.attr({
                        'data-project-name': el.attr('data-project-name'),
                        'placeholder': el.attr('placeholder')
                    });

                    inputExt.enablePullsInput(textarea);

                    var participants = $('#participants').val();
                    if (participants) {
                        participants = JSON.parse(participants);
                        textarea.atwho("@", {data:participants, limit:7});
                    }

                    // 因为zen-form设置的z-index非常高(99999)所以将at-view调更高
                    $('#at-view').css('z-index', 100000);
                }
            }
        };

        var focusToEnd = function(els) {
            return $(els).each(function() {
                var v = $(this).val();
                $(this).focus().val("").val(v);
            });
        };

        inputExt.enableQuickQuotes = function (el) {
            Mousetrap.bind(
                ['r'],
                function (e) {
                    var oldVal = $(el).val(), newVal, selVal = window.getSelection().toString();
                    selVal = '> ' + selVal.split('\n').join('\n> ');
                    newVal = oldVal.concat((oldVal != '') ? '\n\n':'', selVal, '\n\n');
                    $("html, body").animate({scrollTop: $(document).height()}, "slow");
                    $(el).val(newVal);
                    focusToEnd(el);
                },
                'keyup'
            );
        };

        inputExt.enableFileUpload = function (uploader, textarea, is_image) {
            uploader.submit(
                function() {
                $(this).ajaxSubmit({
                    dataType: 'json',
                    type: 'POST',
                    delegation: true,
                    success: function(r) {
                        var oldText = textarea.val(),
                        newText = oldText +
                            (oldText.length == 0 ? '' : '\n') +
                            (is_image? '!' : '') +
                            '[' + r.origin_filename + '](' + r.url + ')';
                        textarea.val(newText);
                    },
                    error: function(r) {
                        alert("上传错误，请确认您上传的文件类型合法");
                    }
                });
                return false;
            });

            uploader.find('input').change(function () {
                uploader.submit();
            });
        };

        inputExt.enableImageUpload = function (uploader, textarea) {
            inputExt.enableFileUpload(uploader,textarea, true);
        };

        inputExt.enableUpload = function(upload_widget,textarea){
            inputExt.enableImageUpload(upload_widget.find(".upload-image-form"),textarea);
            inputExt.enableFileUpload(upload_widget.find(".upload-file-form"),textarea);
        };

        return inputExt;
    }
);
