define('mod/emoji-hint', [
    'jquery',
    'key'
], function($, key) {
    var emojiHint;
    $('#show-emoji-hint').click(
        function () {
            if (!emojiHint) {
                emojiHint = $('<div class="emoji-hint"><iframe src="/hub/emoji" width="650" height="600" frameborder="0"></iframe><a href="javascript:void(0)" id="close">X</a></div>').appendTo('body');
                emojiHint.find('#close').click(function () {emojiHint.hide();});
                $('body').click(function () {emojiHint.hide();});
            }
            emojiHint.show().css('top', $(window).scrollTop());
            return false;
        });

    key('esc', function(){
      emojiHint.hide();
    });
});
