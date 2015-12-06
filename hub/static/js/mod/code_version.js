define('mod/code_version', [
    'jquery',
], function($) {

    function init(){
       $.getJSON("/api/get_code_version", function(data){
       var sha = data.code_version;
       var time = data.release_time;
       $('#rev_sha').html(sha);
       $('#rel_time').html(time.substr(5,11));
       });
     }

    return {
        init: init
    };

});
