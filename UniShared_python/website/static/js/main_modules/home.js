require.config({
    baseUrl: window.staticUrl + 'js'
});

require([
        "lib/live_feed",
        "lib/search_panel",
        "lib/core",
        "lib/w",
        "lib/activity_feed"
        ], function(LiveFeed, SearchPanel) {
    LiveFeed.init();

    var $activityDocumentsFeed = $('#section-documents .feed');
    $activityDocumentsFeed.activityFeed(
        {
            documents: {
                enabled: true
            },
            maxItems: 11,
            userId: 'featured',
            seeAll: true,
            withPagination: false
        });

    var $documentsSearchPanel = $('#section-documents .search-panel');
    SearchPanel.attachTo($documentsSearchPanel, { placeHolder: 'Search notes' });
    $documentsSearchPanel.on('submit.unishared', function (event, query) {
        if(query) {
            _gaq.push(['_trackEvent', 'Home', 'Search documents', query]);
            $activityDocumentsFeed.activityFeed(
            {
                query: query,
                userId: 'all',
                withPagination: true
            });
        }
        else {
            $activityDocumentsFeed.activityFeed(
            {
                query: null,
                userId: 'featured',
                withPagination: false
            });
        }
    });

    var $activityHubsFeed = $('#section-hubs .feed');
    $activityHubsFeed.activityFeed(
        {
            hubs: {
                enabled: true
            },
            maxItems: 5,
            userId: 'featured',
            seeAll: true,
            withPagination: false
        });

    var $hubsSearchPanel = $('#section-hubs .search-panel');
    SearchPanel.attachTo($hubsSearchPanel, { placeHolder: 'Search hubs' });
    $hubsSearchPanel.on('submit.unishared', function (event, query) {
        if(query) {
            _gaq.push(['_trackEvent', 'Home', 'Search hubs', query]);
            $activityHubsFeed.activityFeed(
            {
                query: query,
                userId: 'all',
                withPagination: true
            });
        }
        else {
            $activityHubsFeed.activityFeed(
            {
                query: null,
                userId: 'featured',
                withPagination: false
            });
        }
    });
	$('#header-in a').bind('click', function(event) {
		var $anchor = $(this);

		$('html, body').stop().animate({
			scrollTop : $($anchor.attr('href')).offset().top - 71
		}, 'easeInOutExpo');
		
		_gaq.push(['_trackEvent', 'Home', $anchor.attr('href')]);

		event.preventDefault();
	});

	var sections = $('section'),
	navigation_links = $('nav li');

	sections.waypoint({
		handler : function(event, direction) {

			var active_section, active_link;
			
			active_section = $(this);
			if (direction === "up") {
			    active_section = active_section.prev();
			}
				
			active_link = $('nav a[href="#' + active_section.attr("id") + '"]').parent();
			
			navigation_links.removeClass("selected");
			active_link.addClass("selected");
		},
		offset : 71
	});

    $('#more_about_hubs').click(function () {
        _gaq.push(['_trackEvent', 'Home', 'More about hubs']);
    })
});
