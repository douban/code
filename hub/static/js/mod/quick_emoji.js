define([ 'jquery', 'lib/jquery.caret', 'bootstrap', ],
        function($) {
            var quick_emoji = {};
            quick_emoji.enable = function(textarea_query){
                $('body').delegate('.quick-emoji a', 'click', function(e){
                    var emoji = $(this).attr('data-emoji');
                    if(emoji){
                        textarea = $(textarea_query);
                        var caretpos = textarea.caretPos();
                        var content = textarea.val();
                        var result = "";
                        if(content) {
                            result = content.slice(0, caretpos) + ' ' +
                                emoji + ' ' + content.slice(caretpos);
                            textarea.val(result);
                            textarea.caretPos(caretpos + emoji.length + 2);
                        }
                        else {
                            result = emoji;
                            textarea.val(result);
                            textarea.caretPos(result.length);
                        }
                    }
                    return false;
                });

                $('body').delegate('.emojis a', 'hover', function(e){
                    var $zoomDiv = $('.zoom');
                    if (e.type == "mouseenter") {
                        var $emojiUrl = $(this).find('img').attr('src');
                        var $zoomImage = $('.zoom-image');
                        var $tabContent = $('.tab-content');
                        $zoomImage.attr('src', $emojiUrl);
                        $zoomDiv.css({'display': 'block'});
                    } else {
                        $zoomDiv.css({'display': 'none'});
                    }
                });
            }
                return quick_emoji;
            });
