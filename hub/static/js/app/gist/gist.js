require(['jquery'
, 'spin'
, 'jquery-timeago'
, 'bootstrap'
, 'mod/gist-delete'
//, 'mod/diff'  // no use yet
], function($, Spinner){
  $(function(){
      blob = $('.blob');
      var get_src = function (file, gist, path, ref) {
          var is_image = /^.+\.(jpg|png|gif|jpeg)$/i.test(path);
          if(is_image){
          }
          else{
              $.ajax({type: 'GET',
                  data: {'path': path, 'ref': ref},
                  url: '/api/gist/'.concat(gist, '/src'),
                  dataType: 'json',
                  success: function (ret) {
                      if (ret.type == 'blob') {
                          $(file).html(ret.src);
                          var anchor = window.location.hash;
                          anchor && $('a[href='.concat(anchor, ']')).get(0).scrollIntoView();
                      }
              }});
          }
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
      if (blob.length > 0) {
          $.each(blob, function(i, bb){
              var file = $(bb).children(".file")[0];
              drawSpinner(file);
              var path = $(bb).attr('data-path'),
              ref = $(bb).attr('data-ref');
              gist = $(bb).attr('data-gist');
              get_src(file, gist, path, ref);
      });
      }
       $.each($('.file-box'), function(i, l){
          var aspan = $(l).find('.link-overlay')[0];
          $(l).mouseenter(function(){
          $(l).css("outline","solid 1px #D8EAF2");
          $(aspan).css('visibility', 'visible');
          }).mouseleave(function(){
          $(l).css("outline","none");
          $(aspan).css('visibility', 'hidden');
              });
         });
          $(".js-preview-tabs a").click(function() {
        var curTab = $(this),
            act = curTab.attr("action"),
            writeContent = $("form .write-content"),
            previewContent = $("form .preview-content");
        $(".js-preview-tabs a").removeClass("selected");
        curTab.addClass("selected");
        if (act == "write") {
            writeContent.css("display", "block");
            previewContent.css("display", "none");
        } else if (act == "preview") {
            writeContent.css("display", "none");
            previewContent.css("display", "block");
            preview();
        }
    });

    var commentTextarea = $("textarea[name='content']");
    commentTextarea.keyup(function() {
        var submitBtn = $(".js-comment-submit");
        if ($(this).val() == "") {
            submitBtn.attr("disabled", "disabled");
        } else {
            submitBtn.removeAttr("disabled");
        }
    });

    var commentDeleteButton = $(".js-comment-delete");
    commentDeleteButton.click(function() {
        var url = $(this).attr("url"),
            act = $(this).attr("act"),
            commentId = $(this).attr("target-id");
        $.post(url, {"act": act}, function(ret) {
            ret = $.parseJSON(ret);
            if (ret.hasOwnProperty('r') && ret.r == "1") {
                var containerId = "comment-"+commentId+"-container";
                $("#"+containerId).hide("fast");
            } else {
                alert("Failed to delete comment");
            }
        });
    });

    var preview = function() {
        var text = $("textarea[name='content']").val();
        $.ajax({
            url: "/preview",
            data: {"text": text},
            success: function(ret) {
                $(".comment-content .preview-content-body").html(ret);
            }
        });
    }

  });
});
