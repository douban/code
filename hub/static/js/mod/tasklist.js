define('mod/tasklist', [
    'jquery',
    'jquery-lazyload'
], function($, _) {
  $(function() {
        $('body').delegate(
            '.tasklist-enabled input[type=checkbox]', 'click', function(){
                var editForm = $(this).parents('.tasklist-enabled').find('.tasklist-form');
                if (editForm && editForm.length) {
                    var el = editForm.find('#issue_body'), content = el.val(),
                    p = /- \[[x\s]\]/g, joints = content.match(p), parts = content.split(p),
                    idx = Number($(this).data('item-index'));
                    joints[idx] = joints[idx] == '- [x]' ? '- [ ]' : '- [x]', content = '';
                    for (var i=0, len=parts.length; i<len; i++) {
                        parts[i] && (content = content.concat(parts[i]));
                        joints[i] && (content = content.concat(joints[i]));
                    }
                    el.val(content);
                    editForm.submit();
                }
            });
  });
});
