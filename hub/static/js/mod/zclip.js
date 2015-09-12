define('mod/zclip', [
  'jquery',
  'jquery-zclip'
], function($, _) {
  $(function () {
    $('input.git-url').focus(function(e) {
      var elem = this;
      setTimeout(function() {
        elem.select();
      }, 0);
    });
    $('.copy-git-url').zclip({
      path: '/static/js/lib/ZeroClipboard.swf',
      copy: function() {
        return $('.copy-git-url').attr('data-clipboard-text');
      },
      afterCopy: function() {}
    });
  });
});
