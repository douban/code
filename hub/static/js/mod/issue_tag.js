define('mod/issue_tag', [
    'jquery',
    'bootbox',
    'lib/coloreditor'
], function($) {
    $(function(){
        var issuesFilter = $('.nav-list-filter'),
            issuesEdit = $('.nav-list-edit'),
            remove_tag = function (name) {
                issuesFilter.find('li').each(function (){
                    var tName = $(this).attr('flag-tag');

                    if (name === tName){
                        $(this).remove();
                    }
                })
            },
            clear_href_tag = function () {
                var curHref = window.location.href,
                    url = curHref.split('?')[0],
                    tagCount = issuesEdit.attr('data-tag-count');
                if ($('.nav-list-edit div').length != tagCount){
                    window.location.href = url;
                }
            };

        $('.tag-admin').on('click', function() {
            var admin = $(this);
            if (admin.hasClass('tag-admin-unuse')){

                admin.html('取消');
                admin.removeClass('tag-admin-unuse');
                admin.addClass('tag-admin-using');

                issuesFilter.hide();
                issuesEdit.show();
            } else if (admin.hasClass('tag-admin-using')){

                admin.html('管理');
                admin.removeClass('tag-admin-using');
                admin.addClass('tag-admin-unuse');

                issuesFilter.show();
                issuesEdit.hide();

                clear_href_tag();
            }
        });
        $('.tag-remove').on('click', function () {
            var tagItem = $(this).closest('div'),
                tagType = tagItem.attr('data-tag-type'),
                tagName = tagItem.attr('data-tag-name'),
                tagTargetId = tagItem.attr('data-target-id'),
                msg = '你确定要删除tag: ' + tagName + ' ?';
            if (tagName){
                bootbox.confirm(msg, function(confirmed){
                    if (confirmed){
                        $.post('/j/issue/delete_tag', {'tag_name': tagName, 'tag_type': tagType, 'tag_target_id': tagTargetId}, function (ret) {
                            var status = ret.r;
                            if (status === 1){
                                tagItem.remove();
                                remove_tag(tagName);
                            }
                        }, 'json')
                    }
                })
            }
        });
        var t, e, n;
        e = function(e, n) {
            return e.closest(".js-label-editor").find(".js-color-editor-bg").css("background-color", n), e.css("color", t(n, -.5)), e.css("border-color", n)
        }, n = function(t) {
            var e, n;
            return e = "#eee", n = $(t).closest(".js-color-editor"), n.find(".js-color-editor-bg").css("background-color", e), t.css("color", "#c00"), t.css("border-color", e)
        }, t = function(t, e) {
            var n, s, a;
            for (t = String(t).toLowerCase().replace(/[^0-9a-f]/g, ""), t.length < 6 && (t = t[0] + t[0] + t[1] + t[1] + t[2] + t[2]), e = e || 0, a = "#", n = void 0, s = 0; 3 > s; )
            n = parseInt(t.substr(2 * s, 2), 16), n = Math.round(Math.min(Math.max(0, n + n * e), 255)).toString(16), a += ("00" + n).substr(n.length), s++;
            return a
        };
        $('.js-color-cooser-color').on('click', function () {
            var editor = $(this).closest(".js-label-editor");
            var editor_input = editor.find(".js-color-editor-input");
            editor.find(".js-label-editor-submit").removeClass("disabled");
            editor.removeClass("is-valid is-not-valid");
            var color_value = "#" + $(this).data("hex-color");
            editor_input.val(color_value);
            e(editor_input, color_value);
        });
        $('.js-color-editor-input').on('focusin', function () {
            var t, s;
            s = $(this), t = $(this).closest(".js-label-editor"), s.on("input.colorEditor", function() {
                console.log('co');
                var a;
                return "#" !== s.val().charAt(0) && s.val("#" + s.val()), t.removeClass("is-valid is-not-valid"), a = /(^#[0-9A-F]{6}$)|(^#[0-9A-F]{3}$)/i.test(s.val()),
                t.find(".js-label-editor-submit").toggleClass("disabled", !a), a ? (t.addClass("is-valid"), e(s, s.val())) : (t.addClass("is-not-valid"), n(s))
            }), s.on("blur.colorEditor", function() {
                return s.off(".colorEditor")
            });
            console.log('test');
        });

    });
})
