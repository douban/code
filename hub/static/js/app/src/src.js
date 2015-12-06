define('key', ['lib/keymaster.js'], function(none){
      return key;
});
define('string-score', 'lib/string_score.js');
define('jquery-media', 'lib/jquery.media.js');
define('jquery-commits-graph', 'lib/jquery.commits-graph.js');
define('pjax', 'lib/jquery.pjax.js');

require(['jquery'
, 'spin'
, 'jquery-timeago'
, 'bootstrap'
, 'mod/type_search'
, 'mod/watch'
, 'mod/fetch'
, 'mod/shortcut'
, 'mod/zclip'
, 'key'
, 'string-score'
, 'pjax'
, 'jquery-media'
, 'jquery-commits-graph'
], function($, Spinner){

    var init_source_info = function () {
        var get_src = function (path, ref) {
            var is_image = /^.+\.(jpg|png|gif|jpeg)$/i.test(path);
            if(is_image){
                apiurl = '/'.concat(projectName, '/raw/', ref, '/', path);
                file.html('<img src="'+apiurl+'">');
            }
            else{
                $.ajax({type: 'GET',
                       data: {'path': path, 'ref': ref},
                       url: '/api/'.concat(projectName, '/src'),
                       dataType: 'json',
                       success: function (ret) {
                           if (ret.type == 'blob') {
                               //if (ret.parser == 'markdown' || ret.parser == 'docutils') {
                               //    // reuse markdown's css
                               //    file.addClass('markdown-body');
                               //}
                               file.html(ret.src);
                               $('.media').media({width:938, height:600});
                               var anchor = window.location.hash;
                               var highlight_re = /#L(\d+)-(\d+)$/;
                               var scroll_re = /#L-?(\d+)$/;
                               if (anchor && anchor.match(scroll_re) != undefined){
                                   var paras = anchor.match(scroll_re);
                                   var line_num = parseInt(paras[1]);
                                   $('a[name="'+'L-'+line_num.toString()+'"]').
                                       parent('div').css('background-color', 'rgb(255, 255, 204)');
                                   $('a[href='.concat('#L-'+line_num.toString(), "]")).get(0).scrollIntoView();
                               }
                               else if (anchor && anchor.match(highlight_re) != undefined){
                                   var paras = anchor.match(highlight_re);
                                   var start = parseInt(paras[1]);
                                   var end = parseInt(paras[2]);
                                   var h = end - start;
                                   $('a[name="'+'L-'+start.toString()+'"]').
                                       parent('div').css('background-color', 'rgb(255, 255, 204)')
                                   .nextAll('div').slice(0, h).css('background-color', 'rgb(255, 255, 204)');
                                   $('a[href='.concat('#L-'+paras[1], "]")).get(0).scrollIntoView();
                               }
                           }
                       }});
            }
        };
        var get_commits = function (path, ref) {
            $.ajax({type: 'GET',
                   data: {'path': path, 'ref': ref},
                   url: '/api/'.concat(projectName, '/commits_by_path'),
                   dataType: 'json',
                   success: function (ret) {
                       if (ret.r) {
                           var commits = ret.commits;
                           treeBrowser.find('.tree-item').each(
                               function (idx) {
                               var id = $(this).attr('id')
                               var c = commits[id];
                               $(this).children('.age').text(c.age);
                               if (!c.contributor_url) {
                                   $(this).children('.message').html(
                                       '<a class="message" href="/'.concat(projectName, '/commit/', c.sha, '">', c.message_with_emoji, '</a>',
                                                                           ' [', '<span>', c.contributor, '</span>]'));
                               } else {
                                   $(this).children('.message').html(
                                       '<a class="message" href="/'.concat(projectName, '/commit/', c.sha, '">', c.message_with_emoji, '</a>',
                                                                           ' [', '<a href="', c.contributor_url, '">', c.contributor, '</a>]'));
                               }
                           });
                       }
                   }});
        };

        var drawSpinner = function (elem, isSmall) {
            var opts = { lines: 9, length: 6, width: 4, radius: 9, rotate: 12,
                color: '#000', speed: 1, trail: 60, shadow: false,
                hwaccel: false, className: 'spinner', zIndex: 2e9,
                top: 'auto', left: 'auto' };
                if (isSmall) {
                    opts.length = 4;
                    opts.width = 2;
                    opts.radius = 4;
                }
                return new Spinner(opts).spin(elem);
        };

        // main

        var projectName = $('#project_name').val(),
        blob = $('#blob'), file = $('.file'),
        tree = $('#tree'), treeBrowser = $('.tree-browser');
        if (tree.length > 0) {
            drawSpinner($('.tree-browser td.message:first')[0], true);
            // get commits details
            var path = tree.attr('data-path'),
            ref = tree.attr('data-ref');
            get_commits(path, ref);
        }
        if (blob.length > 0) {
            drawSpinner($('.file')[0]);
            var path = blob.attr('data-path'),
            ref = blob.attr('data-ref');
            get_src(path, ref);
        }

    };

    $(document).pjax('#pjax_container #tree .content a', '#pjax_container', {timeout:1500});
    $(document).pjax('#pjax_container #blob .content a', '#pjax_container', {timeout:1500});
    $(document).on('pjax:end', function() {
        init_source_info();
    });

    init_source_info();

    $('body').delegate('#http', 'click', function (e) {
        var git_url = $(this).parents('.git-url');
        git_url.removeClass('ssh');
        git_url.addClass('http');
        git_url.find('#git-label').text('HTTP');
        return true;
    });
    $('body').delegate('#ssh', 'click', function (e) {
        var git_url = $(this).parents('.git-url');
        git_url.removeClass('http');
        git_url.addClass('ssh');
        git_url.find('#git-label').text('SSH');
        return true;
    });

    $('#commits-graph').commits({
        width: 200,
        height: 1200,
        y_step: 59
    });
});
