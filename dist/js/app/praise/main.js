
require.config({ enable_ozma: true });


/* @source mod/praise.js */;

define('mod/praise', [
  "jquery",
  "bootstrap"
], function($) {
           $(function () {
                 // handle rec btn on people page
                 var recWnd;
                 $('.rec .add-rec').not('.mine').click(
                     function (e) {
                         e.preventDefault();
                         if (!recWnd) {
                             $.get($(this).attr('href'), {}, function (r) {
                                       recWnd = $('<div class="rec-wnd"></div>').html(r).appendTo('body');
                                       recWnd.find('textarea').focus().end()
                                           .find('.close-form').click(
                                               function () {
                                                   recWnd.hide();
                                               });
                                   }, 'html');
                         } else recWnd.show();
                     });

                 // rec vote
                 $('.rec-vote').click(
                     function (e) {
                         e.preventDefault();
                         var btns = $(this).parent('.vote-buttons');
                         if (!btns.hasClass('likes') && !btns.hasClass('voted')) {
                             btns.addClass('likes');
                             $.getJSON($(this).attr('href'),
                                       {rec_id:$(this).attr('data-rec-id')},
                                       function (r) {
                                           if (r.r == '0') {
                                               btns.removeClass('likes');
                                           }
                                       });
                         }
                     });
             });
       });

/* @source  */;

require(['mod/praise'], function ($) {});
