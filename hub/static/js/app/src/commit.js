define('mousetrap', 'lib/mousetrap.js');

require(['mod/quick_emoji'
, 'mousetrap'
, 'mod/commit'
, 'mod/diff'  // diff js
, 'mod/zclip' ], function(quick_emoji){
    quick_emoji.enable("#new_comment_content");
});
