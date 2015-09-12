define('mod/shortcut', [
         'jquery',
         'key'
], function($, key){
      // add shortcut key
      var forkBtn = $('#fork-btn'), pullreqBtn = $('#pullrequest-btn');
      /*
      if (forkBtn) {
          forkBtn.click(function () {
            window.location.href = forkBtn.attr("href");
            });
          key('f', function () {forkBtn.click();});
      }
      */
      if (pullreqBtn) {
          pullreqBtn.click(function () {
              window.location.href = pullreqBtn.attr("href");
          });
          key('p', function () {pullreqBtn.click();});
      }
});
