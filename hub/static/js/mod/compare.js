define('mod/compare', [ 'jquery', 'jquery-tmpl' ], function($){

    var popup;
    var project_name = $('.history a').text();
    $('.compare-button').click(function (e) {
        var curRef = $(this).attr('data-ref'), allRef = [], curIdx = 0;
        $('.compare-button').each(function (i, el){
              var ref = $(el).attr('data-ref');
              allRef.push(ref);
              (ref == curRef) && (curIdx = i);
        });
        select_ref = allRef.slice(0, curIdx);
        e.preventDefault();
        var start_ref = $(this).attr('data-ref');
        if (!popup) {
            popup = $('<div id="compare-popup"></div>').appendTo('body');
            popup.delegate('.close', 'click', function () {popup.hide();});
            popup.delegate('#start-submit', 'click', function () {
                  var ref = popup.find('.ref-autocompleter').val();
                  var link = '';
                  location.href = link;
              })
              .delegate('#end-submit', 'click', function () {
                  var ref = popup.find('.ref-autocompleter').val();
                  if (ref == "" || ref == undefined || ref != null ||!ref.match('/^[0-9a-bA-B]+$/')){
                        var link = '/' + project_name + '/compare/'+start_ref+'...'+ref;
                        location.href = link;
                    } else {
                        popup.remove();
                        alert('wrong revision');
                    }
              });
        }
        var data = {};
        if ($(this).hasClass('from')) {
            data.mode = 'start';
        } else {
            data.mode = 'end';
        }
        data.rev = $($('.sha')[0]).text();
        data.revisions = JSON.stringify(select_ref);
        popup.empty().append($.tmpl($('#templ-compare-chooser'), data)).show();
        scrollTo(0, 0);
        // load commit_preview when sha given
        $('.ref-autocompleter').change(function (){
            var ref = $(this).val();
            $('.place_preview').empty();
            var url = '/' + project_name +'/pull/commit_preview/' + project_name+':'+ref;
            $.get(url, function(data){
                $('.place_preview').html(data);
            });
        });
    });

    popup = null;
    $('.commit-ref').click(function () {
        if (!popup) {
            popup = $('<div id="compare-popup"></div>').appendTo('body');
            popup.delegate('.close', 'click', function () {popup.hide();});
            popup.delegate('#start-submit', 'click', function () {
                var ref = popup.find('.ref-autocompleter').val();
                var link = '/' + project_name + '/compare/'+ref+'...' + '${sha2}';
                location.href = link;

            })
            .delegate('#end-submit', 'click', function () {
                var ref = popup.find('.ref-autocompleter').val();
                var link = '/' + project_name + '/compare/'+'${sha1}'+'...' + ref;
                location.href = link;
            });
        }
        var data = {};
        if ($(this).hasClass('from')) {
            data.mode = 'start';
        } else {
            data.mode = 'end';
        }
        popup.empty().append($.tmpl($('#templ-compare-chooser'), data)).show();
    });

});
