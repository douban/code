define(['jquery', ],
        function ($) {
            var mute_buttons = $('.mute-buttons');
            mute_buttons.find('a').click(function(){
                var href = $(this).attr("href");
                $.getJSON(href, 
                    function(data){
                        var status = data["status"];
                        if(status=='on'){
                            mute_buttons.find('.mute-on').addClass('btn-success');
                            mute_buttons.find('.mute-off').removeClass('btn-warning');
                        }else{
                            mute_buttons.find('.mute-on').removeClass('btn-success');
                            mute_buttons.find('.mute-off').addClass('btn-warning');
                        }
                    });
                return false;
            })
        });
