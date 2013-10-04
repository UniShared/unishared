$(document).ready(function() {
	if (!$.cookie('kkbb')) {
		$.cookie('kkbb', '1', {
			path : '/'
		});
	}

	if ($.cookie('kkbb') && $.cookie('kkbb') == '1') {
		var $overlay = $('#overlay');
		$overlay.show();

		var $container_kkbb = $('#container_kkbb');
		$container_kkbb.show();

		function days_between(date1, date2) {
			// The number of milliseconds in one day
			var ONE_DAY = 1000 * 60 * 60 * 24

			// Convert both dates to milliseconds
			var date1_ms = date1.getTime()
			var date2_ms = date2.getTime()

			// Calculate the difference in milliseconds
			var difference_ms = Math.abs(date1_ms - date2_ms)

			// Convert back to days and return
			return Math.round(difference_ms / ONE_DAY)
		}

		var open25end = new Date(2012, 10, 26, 14, 42, 45);
		$('#daysBeforeOpen25end').text(days_between(open25end, new Date()));

		$container_kkbb.find('.close').show().click(function() {
			$.cookie('kkbb', '0', {
				path : '/'
			});
			_gaq.push(['_trackEvent', 'KKBB #Open25', 'Close']);
			closePopup();
			return false;
		});
		$container_kkbb.find('.prev_button').show().click(function() {
			$.cookie('kkbb', '0', {
				path : '/'
			});
			_gaq.push(['_trackEvent', 'KKBB #Open25', 'Not now']);
			closePopup();
			return false;
		});
		$container_kkbb.find('.next_button').click(function() {
			$.cookie('kkbb', '0', {
				path : '/'
			});
			_gaq.push(['_trackEvent', 'KKBB #Open25', 'Contribute']);
			window.open("http://www.kisskissbankbank.com/open-the-25-best-classes-of-the-world");
			closePopup();
			return false;
		});

		$(document).click(function(e) {
			var click = $(e.target);
			var outsideDiv = $("#overlay div:first").parents();
			if (click.is(outsideDiv)) {
				closePopup();
			}
		});
	}
});

function closePopup() {
	var $overlay = $('#overlay');
	$overlay.fadeOut(500);
	$overlay.find('#container_kkbb').hide();
}