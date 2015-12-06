define('codemirror', ['lib/codemirror.js'], function(none){
    return CodeMirror;
});

require(['jquery'
, 'spin'
, 'mod/gist-editor'
, 'mod/gist-delete'
, 'mod/drop'
, 'jquery-timeago'
, 'bootstrap'
, 'codemirror'
], function($, Spinner){
      var files = $('.js-gist-file');
      var get_src = function (index, file, gist, path, ref) {
          var is_image = /^.+\.(jpg|png|gif|jpeg)$/i.test(path);
          if(is_image){
          }
          else{
              $.ajax({type: 'GET',
                  data: {'path': path, 'ref': ref},
                  url: '/api/gist/'.concat(gist, '/source'),
                  dataType: 'json',
                  success: function (ret) {
                    editors[index].setValue(ret.source);
              }});
          }
      };

      if (files.length > 0) {
        $.each(files, function(i, f){
            var file = $(f).children(".file textarea")[0],
              path = $(f).attr('data-path'),
              ref = $(f).attr('data-ref'), 
              gist = $(f).attr('data-gist');
            get_src(i, file, gist, path, ref);
        });
      }
});
