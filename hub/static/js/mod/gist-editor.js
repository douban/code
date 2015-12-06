define('mod/gist-editor', [
    'jquery',
    'codemirror',
    'mod/loadmode',
    'mod/overlay'
], function ($, CodeMirror) {
    $(function(){
      editors = [];
      var initEditor = function(item){
        var editor = CodeMirror.fromTextArea(item, {
          lineNumbers: true,
          tabMode: "shift",
          matchBrackets: true
        });
        return editor;
      }
      $.each($('textarea[name="gist_content"]'), function(i, e){
        editor = initEditor(e);
        editors.push(editor);
      });

      $("#add-gist").delegate('a', 'click', function(){
        var editorTmpl = document.getElementById('bubble-gist-file').innerHTML;
        $("#files .js-gist-files").append(editorTmpl);
        var newEditor = $("#files .js-gist-files textarea:eq(-1)")[0];
        editor = initEditor(newEditor);
        editors.push(editor);
      });

      $('input[name="gist_name"]').live('blur change', function(){
        setMode(this);
      });

      $('input[name="gist_name"]').live('keydown', function(e){
        if (e.keyCode == 13) return false;
      });

      $(document).ready(function(){
        var _names = $('input[name="gist_name"]');
        setTimeout(function(){
            $.each(_names, function(i, e) { setMode(e) })
        }, 300 * _names.length)
      })

      function setMode(e){
        var editorIndex = $('input[name="gist_name"]').index(e),
            editor = editors[editorIndex],
            name = $(e).val(),
            ext = getExtension(name),
            mode = getMode(ext);
        CodeMirror.autoLoadMode(editor, mode.file || 'text');
          editor.setOption("mode", mode.mode)
      }

      function getExtension(name) {
        if (!name)
          return null;

        var lastDot = name.lastIndexOf(".");
        if (lastDot == -1 || lastDot + 1 == name.length)
          return null;
        else
          return name.substring(lastDot + 1).toLowerCase();
      }

      function getMode(extension) {
        var mode = {};
        if (!extension)
          return mode;

        switch (extension) {
        case "cc":
        case "h":
          mode.mode = "text/x-csrc";
          mode.file = "clike";
          break;
        case "clj":
          mode.mode = "text/x-clojure";
          mode.file = "clojure";
          break;
        case "coffee":
          mode.mode = "text/x-coffeescript";
          mode.file = "coffeescript";
          break;
        case "cpp":
          mode.mode = "text/x-c++src";
          mode.file = "clike";
          break;
        case "cs":
          mode.mode = "text/x-csharp";
          mode.file = "clike";
          break;
        case "sass":
        case "scss":
          mode.mode = "text/x-sass";
          mode.file = "sass";
          break;
        case "css":
          mode.mode = "text/css";
          mode.file = "css";
          break;
        case "erl":
          mode.mode = "text/x-erlang";
          mode.file = "erlang";
          break;
        case "hs":
        case "hsc":
          mode.mode = "text/x-haskell";
          mode.file = "haskell";
          break;
        case "html":
          mode.mode = "text/html";
          mode.file = "htmlmixed";
          break;
        case "ini":
        case "prefs":
          mode.mode = "text/x-properties";
          mode.file = "properties";
          break;
        case "java":
          mode.mode = "text/x-java";
          mode.file = "clike";
          break;
        case "gyp":
        case "js":
        case "json":
          mode.mode = "text/javascript";
          mode.file = "javascript";
          break;
        case "md":
        case "markdown":
          mode.mode = "text/x-markdown";
          mode.file = "markdown";
          break;
        case "pl":
          mode.mode = "text/x-perl";
          mode.file = "perl";
          break;
        case "py":
          mode.mode = "text/x-python";
          mode.file = "python";
          break;
        case "r":
          mode.mode = "text/x-rsrc";
          mode.file = extension;
          break;
        case "rb":
          mode.mode = "text/x-ruby";
          mode.file = "ruby";
          break;
        case "sh":
        case "zsh":
          mode.mode = "text/x-sh";
          mode.file = "shell";
          break;
        case "sql":
          mode.mode = "text/x-mysql";
          mode.file = "mysql";
          break;
        case "xq":
        case "xqy":
        case "xquery":
          mode.mode = "application/xquery";
          mode.file = "xquery";
          break;
        case "project":
        case "classpath":
        case "xib":
        case "xml":
          mode.mode = "application/xml";
          mode.file = "xml";
          break;
        case "yml":
        case "yaml":
          mode.mode = "text/x-yaml";
          mode.file = "yaml";
          break;
        default:
          mode.mode = "text/x-" + extension;
          mode.file = extension;
        }
        return mode;
      }

  });
});
