/*!
* jquery.plugin.pullToRefresh.js
* version 1.0
* author: Damien Antipa
* https://github.com/dantipa/pull-to-refresh-js
*/
(function( $ ){

	$.fn.pullToRefresh = function( options ) {

		var isTouch = !!('ontouchstart' in window),
			cfg = $.extend(true, {
			  message: {
				pull: 'Pull to refresh',
				release: 'Release to refresh',
				loading: 'Loading'
				}
			}, options),
			html = '<div class="pull-to-refresh">' +
				'<div class="icon"></div>' +
				'<div class="message">' +
					'<i class="arrow"></i>' +
					'<i class="spinner large"></i>' +
					'<span class="pull">' + cfg.message.pull + '</span>' +
					'<span class="release">' + cfg.message.release + '</span>' +
					'<span class="loading">' + cfg.message.loading + '</span>' +
				  '</div>' +
				'</div>';



		return this.each(function() {
			if (!isTouch) {
				return;
			}

			var e = $(this).prepend(html),
				content = e.find('.wrap'),
				ptr = e.find('.pull-to-refresh'),
				arrow = e.find('.arrow'),
				spinner = e.find('.spinner'),
				pull = e.find('.pull'),
				release = e.find('.release'),
				loading = e.find('.loading'),
				ptrHeight = ptr.height(),
				arrowDelay = ptrHeight / 3 * 2,
				isActivated = false,
				isLoading = false;

			content.on('touchstart', function (ev) {
				if (e.scrollTop() === 0) { // fix scrolling
					e.scrollTop(1);
				}
			}).on('touchmove', function (ev) {
				var top = e.scrollTop(),
					deg = 180 - (top < -ptrHeight ? 180 : // degrees to move for the arrow (starts at 180° and decreases)
						  (top < -arrowDelay ? Math.round(180 / (ptrHeight - arrowDelay) * (-top - arrowDelay)) 
						  : 0));

				if (isLoading) { // if is already loading -> do nothing
					return true;
				}

				arrow.show();
				arrow.css('transform', 'rotate('+ deg + 'deg)'); // move arrow

				spinner.hide();

				if (-top > ptrHeight) { // release state
					release.css('opacity', 1);
					pull.css('opacity', 0);
					loading.css('opacity', 0);
					

					isActivated = true;
				} else if (top > -ptrHeight) { // pull state
					release.css('opacity', 0);
					loading.css('opacity', 0);
					pull.css('opacity', 1);

					isActivated = false;
				}
			}).on('touchend', function(ev) {
				var top = e.scrollTop();
				
				if (isActivated) { // loading state
					isLoading = true;
					isActivated = false;

					release.css('opacity', 0);;
					pull.css('opacity', 0);
					loading.css('opacity', 1);
					arrow.hide();
					spinner.show();

					ptr.css('position', 'static');

					cfg.callback().done(function() {
						ptr.animate({
							height: 10
						}, 'fast', 'linear', function () {
							ptr.css({
								position: 'absolute',
								height: ptrHeight
							});
							isLoading = false;
						});
					});
				}
			});
		});

	};
})( jQuery );
