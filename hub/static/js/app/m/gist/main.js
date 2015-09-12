define('codemirror', ['lib/codemirror.js'], function(none){
    return CodeMirror;
});
require(['codemirror', 'mod/gist-editor', 'mod/drop'], function(){});
