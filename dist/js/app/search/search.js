
require.config({ enable_ozma: true });


/* @source  */;

require(['jquery', 'jquery-timeago'], function($, Spinner) {
    var fetch = function(data) {
        $.post('count', data, function(ret) {
            ret = $.parseJSON(ret);
            $('.mini-icon-public-repo + .counter').text(ret.repos);
            $('.mini-icon-code + .counter').text(ret.codes);
            $('.mini-icon-person + .counter').text(ret.users);
            $('.mini-icon-doc + .counter').text(ret.docs);
            $('.mini-icon-pull + .counter').text(ret.pulls);
            $('.mini-icon-issue + .counter').text(ret.issues);
        });
    }
    $(function() {
        var q = $("#command-bar").val();
        var language = $("input[name='language']").val();
        var state = $("input[name='state']").val();
        var doctype = $("input[name='doctype']").val();
        var data = {q:q, language:language, state:state, doctype:doctype};
        fetch(data);
    });

    $('select[name="s"]').change(function() {
        $(this).parent().submit();
    });

    $('#tip').click(function() {
        $('#tip-content').toggle();
    });

    $('a.path-url').each(function (){
        var url = $(this).attr('href');
        $(this).parents('.public').find('.linenodiv a').each(function (){
            var href = $(this).attr('href');
            $(this).attr('href', url + href);
        });
    });
});

