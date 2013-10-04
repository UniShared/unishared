'use strict';

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(
    [
        'lib/live_feed',
        'lib/search_panel',
        'lib/core',
        'lib/exp',
        'lib/activity_feed'],
    function (LiveFeed, SearchField) {
        var documents = true, first_time = true,
            $link_my_documents = $('#link_my_documents'), $link_all_documents = $('#link_all_documents'), $link_hubs = $('#link_hubs'),
            $add_document_link = $('#add_document_link'), $add_hub_link = $('#add_hub_link'),
            $activity_feed = $('.feed'),
            $about_me = $("#about_me"), $edit_about_me = $("#edit_about_me"), $link_edit_about_me = $("#link_edit_about_me"), $save_or_cancel_edit_about_me = $("#save_or_cancel_edit_about_me"),
            $searchPanel = $('.search-panel');

        LiveFeed.init();

        $("#expander_about_me #about_me").expander({
            slicePoint: 600
        });

        var urlVars = getUrlVars();
        if (urlVars && urlVars.view) {
            if (urlVars.view === 'my_documents') {
                documents = true;
                my_documents = true;
            }
            else if (urlVars.view === 'all_documents') {
                documents = true;
                my_documents = false;
            }
            else if (urlVars.view === 'hubs') {
                documents = false;
            }
        }

        goTo();

        function myClasses() {
            _gaq.push(['_trackEvent', 'Profile', 'My documents']);
            documents = true;
            my_documents = true;
            goTo();
        }

        function allClasses() {
            _gaq.push(['_trackEvent', 'Profile', 'All documents']);
            documents = true;
            my_documents = false;
            goTo();
        }

        $link_my_documents.click(myClasses);
        $link_all_documents.click(allClasses);

        $link_hubs.click(function () {
            _gaq.push(['_trackEvent', 'Profile', 'Hubs']);
            documents = false;
            goTo();
        });

        $('.add_feed_item').click(function () {
            need_refresh = true;
        });

        function getPlaceHolder() {
            return 'Search in {0}...'.format($('.active').text().trim().toLowerCase());
        }

        SearchField.attachTo($searchPanel, {placeHolder: getPlaceHolder()});
        $searchPanel.on('submit.unishared', function (event, query) {
            _gaq.push(['_trackEvent', 'Profile', getPlaceHolder(), query]);
            $activity_feed.activityFeed(
                {
                    query: query
               });
        });

        // Start editing about me
        function editAboutMe() {
            $save_or_cancel_edit_about_me.css("display", "inline");
            $link_edit_about_me.css("display", "none");
            $edit_about_me.css("display", "block");
            $about_me.css("display", "none");

            return false;
        }

        // End editing about me
        function endEditAboutMe() {
            $save_or_cancel_edit_about_me.css("display", "none");
            $link_edit_about_me.css("display", "inline");
            $edit_about_me.css("display", "none");
            $about_me.css("display", "block");

            return false;
        }

        // End editing about me and save
        function saveAboutMe(id) {
            endEditAboutMe();

            if ($edit_about_me.val() != "") {
                var values = {};
                values.about_me = $edit_about_me.val();

                ajaxSend('/profile/', 'POST', values, function () {
                    $about_me.text($edit_about_me.val()).expander();
                });
            }
        }

        $link_edit_about_me.click(editAboutMe);
        $save_or_cancel_edit_about_me.find('#link_save_about_me').click(function () {
            saveAboutMe($('#id_unistar').val());
        });
        $save_or_cancel_edit_about_me.find('#link_cancel_edit_about_me').click(endEditAboutMe);

        function goTo() {
            $link_my_documents.removeClass('active');
            $link_my_documents.removeClass('inactive');

            $link_all_documents.removeClass('active');
            $link_all_documents.removeClass('inactive');

            $link_hubs.removeClass('active');
            $link_hubs.removeClass('inactive');

            var $idUnistar = $('#id_unistar').val(),
                canCreate = $('#canCreate').val() === "true";

            $activity_feed.activityFeed(
                {
                    hubs: {
                        enabled: !documents
                    },
                    documents: {
                        enabled: documents
                    },
                    query: null,
                    userId: documents && my_documents ? $idUnistar : 'all',
                    viewFor: $('#id_unistar').val(),
                    withPagination: true,
                    canCreate : canCreate,
                    canDelete : is_my_profile,
                    maxItems: canCreate ? 11 : 12
                });

            if (documents) {
                $add_document_link.show();
                $add_hub_link.hide();

                if (my_documents) {
                    $link_my_documents.addClass('active');
                    $link_all_documents.addClass('inactive');
                    $link_hubs.addClass('inactive');
                } else {
                    $link_all_documents.addClass('active');
                    $link_my_documents.addClass('inactive');
                    $link_hubs.addClass('inactive');
                }
            }
            else {
                $link_all_documents.addClass('inactive');
                $link_my_documents.addClass('inactive');
                $link_hubs.addClass('active');

                $add_document_link.hide();
                $add_hub_link.show();
            }

            $searchPanel.trigger('setPlaceHolder.unishared', getPlaceHolder());
            $searchPanel.trigger('reset.unishared');
            $searchPanel.trigger('setSearchObjects.unishared', documents ? 'documents' : 'hubs');
        }
    });