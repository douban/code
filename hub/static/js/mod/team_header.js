define('mod/team_header', ['jquery'], function($){
  $(function(){
     var JoinOrLeaveTeam = function (url, onSuccess) {
         $.post(url, function (ret) {
             if (ret.r === 0) {
                 onSuccess();
             }
         }, 'json');
     };
     $('.join-or-leave-btn').click(function () {
         var Btn = $(this), team = Btn.attr('data-team'), _type = Btn.attr('data-type'),
             url = '/hub/team/' + team + '/' + _type;
         if (_type === "leave") {
             JoinOrLeaveTeam(url, function () {
                 Btn.removeClass('btn-danger');
                 Btn.addClass('btn-success');
                 Btn.html('Join');
                 Btn.attr('data-type', 'join');
             }); 
         }else{
             JoinOrLeaveTeam(url, function () {
                 Btn.removeClass('btn-success');
                 Btn.addClass('btn-danger');
                 Btn.html('Leave');
                 Btn.attr('data-type', 'leave');
             }); 
         }
     });
  });
});
