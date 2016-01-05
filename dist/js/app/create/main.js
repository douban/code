
require.config({ enable_ozma: true });


/* @source  */;

//define('jquery', 'lib/jquery.min.js')
require(['jquery'], function($){
  $(function(){
    $("#org_proj").click(function(){
      $("#owner").hide("slow");
      $(".splash").hide("slow");
      $("#mirror").hide("slow");
      $(".mirror-url").hide();
      $(".mirror-with-proxy").hide();
    });
    $("#people_proj").click(function(){
      $("#owner").show("slow");
      $(".splash").show("slow");
      $("#mirror").hide();
      $(".mirror-url").hide();
      $(".mirror-with-proxy").hide();
    });
    $("#mirror_proj").click(function(){
      $("#owner").hide();
      $("#mirror").show("slow");
      $(".splash").show("slow");
      $(".mirror-url").show();
      $(".mirror-with-proxy").show();
    });
  });
});
