require.config({
    baseUrl: '/js/'
});

define('jquery-src', 'lib/jquery-1.8.3.js');
define('jquery', ['jquery-src'], function(){
    return window.jQuery;
});

define('jquery-tmpl', ['jquery'], 'lib/jquery.tmpl.js');
define('jquery-lazyload', ['jquery'], 'lib/jquery.lazyload.js');
define('jquery-caret', ['jquery'], 'lib/jquery.caret.js');
define('jquery-atwho', ['jquery'], 'lib/jquery.atwho.js');
define('jquery-timeago', ['jquery'], 'lib/jquery.timeago.js');
define('jquery-forms', ['jquery'], 'lib/jquery.forms.js');
define('jquery-unobstrusive', ['jquery'], 'lib/unobtrusive.js');
define('jquery-zclip', ['jquery'], 'lib/jquery.zclip.js');
define('jquery-tooltipster', ['jquery'], 'lib/jquery.tooltipster.js');
define('socket.io', 'lib/socket.io.js');
define('bootstrap', ['jquery'], 'lib/bootstrap-amd.js');
define('mustache', 'lib/mustache.js');
define('store', 'lib/store.js');
define('spin', 'lib/spin.js');
define('key', ['lib/keymaster.js'], function(none){
      return key;
});
define('mousetrap', 'lib/mousetrap.js');
define('codemirror', ['lib/codemirror.js'], function(none){
    return CodeMirror;
});
define('bootbox-origin', ['jquery'], 'lib/bootbox.js');

define('bootbox', ['bootbox-origin'], function(none){
    return bootbox;
});

define('d3', ['lib/d3-3.3.3.js'], function(none){
    return d3;
});
define('string-score', 'lib/string_score.js');


require([
    'jquery',
    'mod/user_avatar',
    'mod/relative_date',
    'mod/code_version',
    'mod/user_following',
    'mod/search_autocomplete',
    'mod/emoji-hint',
    'jquery-tmpl',
    'jquery-timeago',
    'jquery-lazyload',
    'jquery-caret',
    'jquery-atwho',
    'jquery-forms',
    'jquery-unobstrusive',
    'jquery-zclip',
    'jquery-tooltipster',
    'socket.io',
    'bootstrap',
    'mustache',
    'spin',
    'bootbox'
], function($, loadAvatar, updateRelativeDate, codeVersion, userFollowing) {
    $(function () {
          setTimeout(loadAvatar, 800);
          updateRelativeDate();
          codeVersion.init();
          userFollowing.update();

          if (("standalone" in window.navigator) && window.navigator.standalone) {
              // For iOS Apps
              $('a').on('click', function(e){
                  e.preventDefault();
                  var new_location = $(this).attr('href');
                  if (new_location != undefined && new_location.substr(0, 1) != '#' && $(this).attr('data-method') == undefined){
                      window.location = new_location;
                  }
              });
          }

      });
});
