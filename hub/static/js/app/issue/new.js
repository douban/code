define('mousetrap', 'lib/mousetrap.js');
define('tag-it', 'lib/tag-it.js');

require(
    ['jquery'
     , 'mod/input-ext'
     , 'jquery-caret'
     , 'jquery-atwho'
     , 'jquery-timeago'
     , 'bootstrap'
     , 'mod/watch'
     , 'mousetrap'
     , 'tag-it'],
    function($, inputExt){
        $(function () {
            inputExt.enableZenMode('#pull_body');
            inputExt.enableAutoCompleteFollowingAndTeam('#pull_body');
            //previewable-comment-form
            $('.previewable-comment-form .js-preview-tabs a.preview-tab').on('show', function(e) {
                $('#preview_bucket p').html("Loading preview...");
            }).on('shown', function(e) {
                var url = $('#preview_bucket .content-body').data('api-url');
                var text = $('#write_bucket textarea').val();
                $('#preview_bucket .content-body').load(url, {text: text});
            });

            $('.new-issue form').submit(
                function () {
                    $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                    //Google Analytic Events
                    ga('send', 'event', 'issue', 'create');
                }
            );

              var uploader = $('#form-file-upload'),
              textarea = $('#write_bucket textarea');
              inputExt.enableUpload(uploader, textarea);

              $('#issue-tags').tagit({input_name: 'issue_tags', tag_list: $('.label')});

          });
    });
