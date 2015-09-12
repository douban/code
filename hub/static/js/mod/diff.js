define('mod/diff', [
    'jquery',
    'mod/input-ext',
    'mod/liveupdate',
    'mod/colorcube',
], function ($, inputExt, live, colorcube) {

        ////////////////////  linecomment

        // comment form
        var hideCommentForm = function () {
            $('.inline-comment-form').hide().closest('tr').removeClass('show-inline-comment-form');
            $('.inline-comment-form').each(
                function (idx, el) {
                    if (!$(el).siblings('.comment-holder').children('.comment').length) {
                        $(el).parents('tr').hide();
                    }
                }
            );
        };
        var openCommentForm = function (curRow) {
            hideCommentForm();
            var nextRow = curRow.next('tr');
            // if no comments on curRow yet
            if (!nextRow.length || !nextRow.hasClass('inline-comments')) {
                nextRow = $.tmpl($('#templ-inline-comments-row'), {}).insertAfter(curRow);
            }
            // if side by side... plz refactor this
            var file = curRow.parents('.file');
            if ((file.children('.side')).length != 0 && file.children('.side').css('display') != 'none') {
                $(nextRow.children()[0]).attr('colspan', 1);
            }
            nextRow.show().addClass('show-inline-comment-form');
            var commentsBlock = nextRow.children('.line-comments'),
            commentForm = commentsBlock.find('.inline-comment-form');
            // if no commentForm on nextRow yet
            if (!commentForm.length) {
                // get form-data
                var patch_data = file.children('.meta').find('.patch-data');
                var line_data = curRow.find('.line-data');
                var data = {
                    from_sha: patch_data.attr('data-from-sha'),
                    old_path: patch_data.attr('data-old-path'),
                    new_path: patch_data.attr('data-new-path'),
                    from_oid: patch_data.attr('data-from-oid'),
                    to_oid:   patch_data.attr('data-to-oid'),
                    old_no: line_data.attr('data-old'),
                    new_no: line_data.attr('data-new'),
                };
                commentForm = $.tmpl($('#templ-inline-comment-form'), data).appendTo(commentsBlock);
                commentForm.find('.js-hide-inline-comment-form').click(
                    function () {
                        hideCommentForm();
                    }
                ).end().find('form').submit(
                    function () {
                        $(this).find('button[type="submit"]').attr('disabled', true).addClass('disabled');
                        return true;
                    }
                );
                var commentTexarea = commentForm.find('textarea');
                inputExt.enableEmojiInput(commentTexarea);
                inputExt.shortcut2submit(commentTexarea);
            }
            commentForm.show().find('textarea').focus();
            // codelive channel
            var linecomment_channel_id;
            if ($('.discussion-tab-link').length > 0) {
                linecomment_channel_id = "code_pr_"+$('.discussion-tab-link').attr('data-url') + 'linecomment';
            }
            // `comment on this line`
            commentForm.find('form.js-inline-comment-form').ajaxForm({
                dataType: 'json',
                beforeSend: function () {
                    commentForm.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                    .end().find('.loader').show();
                },
                success: function(r) {
                    if (r.r == 0 && r.html) {
                        commentForm.siblings('.js-comments-holder').append(r.html);
                        commentForm.find('textarea').val('').blur();
                        hideCommentForm();
                        live && linecomment_channel_id &&
                            live.emit('ready', {channel: linecomment_channel_id, msg:r.html_with_diff});
                    } else if (r.error){
                        alert(r.error);
                    }
                    commentForm.find('button[type="submit"]').attr('disabled', false).removeClass('disabled');
                    commentForm.find('form.js-inline-comment-form').removeClass('submitting')
                    .end().find('.loader').hide();
                    return true;
                },
                error: function () {}
            });
        };

        // add-bubble...
        $('body').delegate('.add-bubble', 'click', function () {
            var curRow = $(this).parents('tr');
            var nextRow = curRow.next('tr');
            if (nextRow.hasClass('inline-comments') && nextRow.css('display') != 'none') {
                nextRow.hide();
            } else {
                openCommentForm(curRow);
            }
        });

        // `add a line note`
        $('body').delegate(
            '.js-show-inline-comment-form', 'click', function () {
            var curRow = $(this).parents('tr').prev('tr');
            openCommentForm(curRow);
        });

        // linecomment delete
        $('body').delegate('.inline-comments .delete-button', 'click', function (e) {
            if (!confirm('Are you sure you want to delete this?')) {
                return false;
            }
            var comment = $(this).parents('.comment');
            $.getJSON(
                $(this).attr('href'),
                function(r) {
                    // FIXME: global row?
                    if (r.r == '1')
                        var row = comment.parents('tr');
                    if (comment.siblings('.comment').length ||
                        row.find('.inline-comment-form').length) {
                        comment.remove();
                    } else {
                        row.remove();
                    }
                }
            );
            return false;
        });

        // comment & linecomment edit
        $('body').delegate('.js-comment-edit-button', 'click', function (e) {
            var form_content = $(this).parents('.comment-header')
            .next('.comment-content')
            .children('.form-content');
            if (form_content != undefined) {
                form_content.show().find('textarea').focus();
                form_content.find('form.js-comment-update').ajaxForm({
                    dataType: 'json',
                    beforeSend: function() {
                        form_content.find('button[type="submit"]').attr('disabled', true).addClass('disabled')
                        .end().find('.loader').show();
                    },
                    success: function(r) {
                        if (r.r == 0 && r.html) {
                            if (form_content.find('textarea').attr('name') === 'pull_request_review_comment'){
                                form_content.parents('.js-comments-holder').append(r.html);
                                form_content.parents('.comment').remove();
                            } else {
                                var comment = form_content.parents('.change');
                                var avatar = comment.prev('.side-avatar');
                                form_content.parents('#changelog').append(r.html);
                                comment.remove();
                                avatar.remove();
                            }
                        }
                        return true;
                    }
                });
            } else {
                return false;
            }
        });

        // show linecomments toggle
        $('body').delegate('.file .js-show-inline-comments-toggle', 'change', function () {
            var comments = $(this).parents('.file').find('.inline-comments');
            if ($(this).is(':checked')) {
                comments.show();
            } else {
                comments.hide();
            }
        });

        // generated file toggle
        $('body').delegate('.file a.generated', 'click', function() {
            var file = $(this).parents('.file');
            var inline = file.children('.inline').show();
            $(this).hide();
        });

        // patch side diff toggle
        $('body').delegate('.file .js-side-diff', 'click', function () {
            var file = $(this).parents('.file');
            file.find('a.generated').hide();
            if (file.children('.side').css('display') === 'none' &&
                file.children('.inline').css('display') === 'none'){
                file.children('.inline').show();
            }else {
                var inline = file.children('.inline').toggle();
                var side = file.children('.side').toggle();
                var checkbox = file.find('.js-show-inline-comments-toggle');
                if (file.children('.side').css('display') != 'none') {
                    checkbox.attr('checked', false);
                    side.find('.inline-comments').hide();
                }
                else {
                    checkbox.attr('checked', true);
                }
            }
        });

        // diff patch fullscreen toggle
        $('body').delegate('.file .js-fullscreen', 'click', function () {
            var fullscreenStage = $('#fullscreen-stage');
            if (fullscreenStage.length == 0) {
                var files = $(this).parents('#files');
                fullscreenStage = $('<div id="fullscreen-stage"></div>').appendTo(files);
            }
            if (fullscreenStage.is(":visible")) {
                fullscreenStage.hide();
                $('body').removeClass('fullscreen-mode');
            } else {
                var file = $(this).parents('.file');
                fullscreenStage.html(file.clone()).show();
                $('body').addClass('fullscreen-mode');
                fullscreenStage.find('.file .js-fullscreen').text('Exit Full Screen');
            }
        });

        // dblclick open linecomment form
        var clearSelection = function () {
            if (window.getSelection) {
              if (window.getSelection().empty) {  // Chrome
                window.getSelection().empty();
              } else if (window.getSelection().removeAllRanges) {  // Firefox
                window.getSelection().removeAllRanges();
              }
            } else if (document.selection) {  // IE?
              document.selection.empty();
            }
        }
        $('body').delegate('.js-open-comment-form.dblclick-comment', 'dblclick', function () {
            clearSelection();
            var curRow = $(this).parents('tr');
            openCommentForm(curRow);
        });

        ////////////////////  moreline get_contexts

        // moreline
        $('body').delegate('pre.skipped a', 'click', function() {
            var curRow = $(this).parents('tr');
            var patch_data = curRow.parents('.file').children('.meta').find('.patch-data');
            var data = curRow.find('.expand-data');
            var url = patch_data.attr('data-context-url');
            $.get(
                url,
                {
                    old_sha   : patch_data.attr('data-old-sha'),
                    old_path  : patch_data.attr('data-old-path'),
                    old_start : data.attr('data-old-start'),
                    new_start : data.attr('data-new-start'),
                    old_end   : data.attr('data-old-end'),
                    new_end   : data.attr('data-new-end'),
                    type      : $(this).attr('data-type'),
                },
                function (r) {
                    curRow.after(r.html);
                    if (r.html.trim()) {
                        curRow.remove();
                    }
                }
            );
        });

        // full diff
        $('body').delegate('.ellipsis', 'click', function() {
            var $this = $(this);
            var fpath = $this.attr('data-path');
            var new_fpath = $this.attr('data-new-path');

            // for pull/new
            var from_proj = $('.new-pull-request form input[name="from_proj"]').attr('value');
            var from_ref = $('.new-pull-request form input[name="from_ref"]').attr('value');
            var to_ref = $('.new-pull-request form input[name="to_ref"]').attr('value');
            var to_proj = $('.new-pull-request form input[name="to_proj"]').attr('value');

            var url = $this.attr('data-url');
            var table = $this.parents('.data').find('.diff-table');
            $.get(url,
                  {
                      filepath: fpath,
                      new_filepath: new_fpath,
                      from_proj: from_proj,
                      from_ref: from_ref,
                      to_ref: to_ref,
                      to_proj: to_proj
                  },
                  function(r){
                      table.find('tbody').html(r.html);
                  });
        });

        // TODO: modify this, after refactor diff api
        // toggle whitespace diff
        $('body').delegate('.toggle_whitespace', 'click', function() {
            var $this = $(this);
            var fpath = $this.attr('data-path');
            var new_fpath = $this.attr('data-new-path');

             // for pull/new
            var from_proj = $('.new-pull-request form input[name="from_proj"]').attr('value');
            var from_ref = $('.new-pull-request form input[name="from_ref"]').attr('value');
            var to_ref = $('.new-pull-request form input[name="to_ref"]').attr('value');
            var to_proj = $('.new-pull-request form input[name="to_proj"]').attr('value');

            var url = $this.attr('data-url');
            var table = $this.parents('.data').find('.diff-table');
            var whitespace = $this.attr('data-w');

            $.get(url,
                  {
                      filepath: fpath,
                      new_filepath: new_fpath,
                      from_proj: from_proj,
                      from_ref: from_ref,
                      to_ref: to_ref,
                      to_proj: to_proj,
                      w: whitespace
                  },
                  function(r){
                      table.find('tbody').html(r.html);
                      $this.attr('data-w', (1 - parseInt(whitespace)).toString());
                  });
        });

        //////////////////// no use ??
        function convertDiff(name, table, pre) {
          var inline = $(table).hasClass('inline');
          var ths = table.tHead.rows[0].cells;
          var afile, bfile;
          if ( inline ) {
              afile = ths[0].title;
              bfile = ths[1].title;
          } else {
              afile = $(ths[0]).find('a').text();
              bfile = $(ths[1]).find('a').text();
          }
          if ( afile.match(/^Revision /) ) {
              afile = 'a/' + name;
              bfile = 'b/' + name;
          }
          var lines = [
            "Index: " + name,
            "===================================================================",
            "--- " + afile.replace(/File /, ''),
            "+++ " + bfile.replace(/File /, ''),
          ];
          var sepIndex = 0;
          var oldOffset = 0, oldLength = 0, newOffset = 0, newLength = 0;
          var title = "";
          if (inline)
            title = $(ths[2]).text();
          for (var i = 0; i < table.tBodies.length; i++) {
            var tBody = table.tBodies[i];
            if (i == 0 || tBody.className == "skipped") {
              if (i > 0) {
                if (!oldOffset && oldLength) oldOffset = 1
                if (!newOffset && newLength) newOffset = 1
                lines[sepIndex] = lines[sepIndex]
                  .replace("{1}", oldOffset).replace("{2}", oldLength)
                  .replace("{3}", newOffset).replace("{4}", newLength)
                  .replace("{5}", title);
              }
              sepIndex = lines.length;
              lines.push("@@ -{1},{2} +{3},{4} @@{5}");
              oldOffset = 0, oldLength = 0, newOffset = 0, newLength = 0;
              if (tBody.className == "skipped") {
                if (inline)
                  title = $(tBody.rows[0].cells[2]).text();
                continue;
              }
            }
            var tmpLines = [];
            for (var j = 0; j < tBody.rows.length; j++) {
              var cells = tBody.rows[j].cells;
              var oldLineNo = parseInt($(cells[0]).text());
              var newLineNo = parseInt($(cells[inline ? 1 : 2]).text());
              if (tBody.className == 'unmod') {
                lines.push(" " + $(cells[inline ? 2 : 1]).text());
                oldLength += 1;
                newLength += 1;
                if (!oldOffset) oldOffset = oldLineNo;
                if (!newOffset) newOffset = newLineNo;
              } else {
                var oldLine;
                var newLine;
                var oldTag = "-";
                var newTag = "+";
                if (inline) {
                  oldLine = newLine = $(cells[2]).text();
                  if ($('em', cells[2]).length) oldTag = newTag = "\\";
                } else {
                  oldLine = $(cells[1]).text();
                  if ($('em', cells[1]).length) oldTag = "\\";
                  newLine = $(cells[3]).text();
                  if ($('em', cells[3]).length) newTag = "\\";
                }
                if (!isNaN(oldLineNo)) {
                  lines.push(oldTag + oldLine);
                  oldLength += 1;
                }
                if (!isNaN(newLineNo)) {
                  tmpLines.push(newTag + newLine);
                  newLength += 1;
                }
              }
            }
            if (tmpLines.length > 0) {
              lines = lines.concat(tmpLines);
            }
          }
          if (!oldOffset && oldLength) oldOffset = 1;
          if (!newOffset && newLength) newOffset = 1;
          lines[sepIndex] = lines[sepIndex]
            .replace("{1}", oldOffset).replace("{2}", oldLength)
            .replace("{3}", newOffset).replace("{4}", newLength)
            .replace("{5}", title);
          /* remove trailing &nbsp; and join lines (with CR for IExplorer) */
          var sep = $.browser.msie ? "\r" : "\n";
          for ( var i = 0; i < lines.length; i++ )
              if ( lines[i] )
              {
                  var line = lines[i].replace(/\xa0$/, '') + sep;
                  if ( lines[i][0] == '+' )
                    pre.append($('<span class="add">').text(line));
                  else if ( lines[i][0] == '-' )
                    pre.append($('<span class="rem">').text(line));
                  else
                    pre.append($('<span>').text(line));
              }
        }
        // no use ??
        $("div.diff h2").each(function() {
          console.log('call div.diff h2 !!!');
          var switcher = $("<span class='switch'></span>").prependTo(this);
          var name = $.trim($(this).text());
          var table = $(this).siblings("table").get(0);
          if (! table) return;
          var pre = $('<pre class="diff">').hide().insertAfter(table);
          $("<span>" + _("Tabular") + "</span>").click(function() {
            $(pre).hide();
            $(table).show();
            $(this).addClass("active").siblings("span").removeClass("active");
            return false;
          }).addClass("active").appendTo(switcher);
          $("<span>" + _("Unified") + "</span>").click(function() {
            $(table).hide();
            if (!pre.get(0).firstChild) convertDiff(name, table, pre);
            $(pre).fadeIn("fast")
            $(this).addClass("active").siblings("span").removeClass("active");
            return false;
          }).appendTo(switcher);
        });


        colorcube.init({target:'body'});
});
