require(['jquery'], function(){
    var is_on = 1;
    var notifications_meta = ['participating_email',
        'participating_irc',
        'participating_web',
        'watching_email',
        'watching_irc',
        'watching_web'];

    for(var i = 0; i < notifications_meta.length; i++){
        $('#' + notifications_meta[i]).click(function() {
            var checkbox = $(this);
            if(checkbox.attr("checked") == "checked"){
                is_on = 1;
            }else{
                is_on = 0;
            }

            $.ajax({
                type: 'POST',
                data: {
                    'notifications_meta': checkbox.val(),
                    'is_on': is_on
                },
                url: '/settings/notification/setting',
                dataType: 'json',
                success: function (ret) {
                    if(ret.result == 'fail'){
                        checkbox.prop("checked", "checked");
                    }
                }
            });
        });
    }
});

