define('mod/gist-delete', [
    'jquery'
], function ($) {
    $(function(){
      $('button.danger.js-delete-gist').click(function(){ 
        if(confirm('Are you positive you want to delete this Gist?')){
          window.location.href = './delete';
        }
      });
    })
});

