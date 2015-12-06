define('mod/editor', [
    'jquery',
    'codemirror',
    'mod/loadmode',
    'mod/overlay',
], function ($, CodeMirror) {

  $(function(){
    var editor = CodeMirror.fromTextArea($('.commit_form textarea[name="code"]')[0], {
      mode: {name: "python", version: 2, singleLineStringErrors: false},
      lineNumbers: true,
      indentUnit: 4,
      tabMode: "shift",
      matchBrackets: true
    });
    CodeMirror.autoLoadMode(editor, 'python');

    return editor
  });
});
