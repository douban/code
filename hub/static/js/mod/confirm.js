define('mod/confirm', [ 'jquery', 'bootbox' ], function($){

    $("a.confirm").click(function(e) {
        e.preventDefault();
        var location = $(this).attr('href');
        bootbox.confirm("Are you sure?", function(confirmed) {
             if(confirmed){
                 window.location.replace(location);
             }
        });
    });

});
