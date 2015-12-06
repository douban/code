define('mod/contribut_info', [
    'jquery',
    'bootstrap'
], function($) {

    $(function(){
      $(".contributor").each(function(){
        var options = {
          title: $(this).attr('data-commits') + ' ' + 'commits',
          content: $(this).attr('data-added') + '++' + ' / ' + $(this).attr('data-removed') + '--'
        };
        $(this).popover(options);
      });
    });

});
