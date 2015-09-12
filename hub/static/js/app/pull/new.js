define('mousetrap', 'lib/mousetrap.js');

require(
    ['jquery'
     , 'mod/input-ext'
     , 'jquery-caret'
     , 'jquery-atwho'
     , 'jquery-timeago'
     , 'bootstrap'
     , 'mod/watch'
     //, 'mod/commit'
     , 'mod/diff'   // diff js
     , 'mousetrap'],
    function($, inputExt){
        $(function () {
            inputExt.enableZenMode('#pull_body');
            inputExt.enableAutoCompleteFollowingAndTeam('#pull_body');

            //pull.js
            $('.editor-expander').click(
                function() {
                    var $editor = $('.range-editor');
                    $('.pull-tabs').css('opacity', $editor.css('display') == 'none' ? 0.45 : 1);
                    $editor.slideToggle('fast');
                    return false;
                });

            var update_preview = function($box) {
                var proj_name = $box.find('select').val();
                var url = '/api/' + proj_name + '/git/branches';

                $.getJSON(url, function(branches){
                    $box.find('.typeahead').data('source', branches);
                });

                url = $box.data('preview-url-base') + proj_name + ':' + $box.find('input.js-ref').val();
                $box.find('.commit-preview').load(url);
            };

            $('.range-editor select[name=base_repo]').change(
                function() {
                    var $box = $(this).parents('.chooser-box');
                    update_preview($box);
                });

            $('.range-editor input[type=text]').change(
                function() {
                    var $box = $(this).parents('.chooser-box');
                    update_preview($box);
                });

            $('#update_commit_range').click(
                function() {
                    var $form = $(this).parents('form');
                    $form.attr('action', $(this).data('url')).submit();
                });
            //previewable-comment-form
            $('.previewable-comment-form .js-preview-tabs a.preview-tab').on(
                'show', function(e) {
                    $('#preview_bucket p').html("Loading preview...");
                }).on('shown', function(e) {
                    var url = $('#preview_bucket .content-body').data('api-url');
                    var text = $('#write_bucket textarea').val();
                    $('#preview_bucket .content-body').load(url, {text: text});
                });

            $('.new-pull-request form').submit(
                function () {
                    $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                    //Google Analytic Events
                    ga('send', 'event', 'pullrequest', 'create');
                });

            var uploader = $('#form-file-upload'),
                textarea = $('#write_bucket textarea');
            inputExt.enableUpload(uploader, textarea);

            $('a[data-toggle="tab"]').on(
                'shown', function (e) {
                    if ($(e.target).hasClass('preview-discussion-tab')) {
                        $('#form-file-upload').show();
                    } else {
                        $('#form-file-upload').hide();
                    }
                });
        });
    });
