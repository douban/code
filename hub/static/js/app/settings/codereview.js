require(['jquery'], function(){
    var is_enable = 1;
    var field = [
        'dblclick_comment',
    ];

    for(var i = 0; i < field.length; i++){
        $('#' + field[i]).click(function() {
            var checkbox = $(this);
            if(checkbox.attr("checked") == "checked"){
                is_enable = 1;
            }else{
                is_enable = 0;
            }

            $.ajax({
                type: 'POST',
                data: {
                    'field': checkbox.val(),
                    'is_enable': is_enable
                },
                url: '/settings/codereview/setting',
                dataType: 'json',
                success: function (ret) {
                    if(ret.result == 'fail'){
                        checkbox.prop("checked", "checked");
                    }
                }
            });
        });
    }

    $('#text_font').on('change', function() {
        var select = $(this);
        $.ajax({
            type: 'POST',
            data: {
                'field': 'text_font',
                'is_enable': select.val()
            },
            url: '/settings/codereview/setting',
            dataType: 'json',
            success: function (ret) {
                if(ret.result == 'fail'){
                    select.find('option:selected').removeAttr('selected');
                    select.find('option[value="' + ret.origin + '"]').attr("selected",true);
                }
            }
        });
    });
});

