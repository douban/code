require(['jquery', 'lib/odometer'], function() {
    $.getJSON('/hub/stat/source', function( data ) {
        $.each( data, function(className, val) {
            $('.odometer.' + className).html(val);
        });
    });
});
