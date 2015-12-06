define('mod/proj_del_btn', [
    'jquery',
    'bootbox'
], function($) {
    var delProj = function (proj, onSuccess) {
        bootbox.confirm("Are you sure?", function(confirmed) {
            if (confirmed) {
                $.post('/' + proj + '/remove', function (ret) {
                    if (ret.r === 1) {
                        onSuccess();
                    } else {
                        bootbox.alert(ret.err);
                    }
                }, 'json');
            }
        });
    };

    $('.my_projects li').hover(
        function () {$(this).addClass('hover');},
        function () {$(this).removeClass('hover');}
    );

    $('.my_projects li .delete-btn').click(function () {
        var delBtn = $(this), proj = delBtn.attr('data-proj');
        delProj(proj, function () { delBtn.closest('li').remove(); });
    });

    $('#settings-del-proj').click(function () {
        var delBtn = $(this), proj = delBtn.attr('data-proj');
        delProj(proj, function () { window.location = '/'; });
    });
});
