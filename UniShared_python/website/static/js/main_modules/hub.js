"use strict";

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(
    [
        'lib/people_form',
        'lib/live_feed',
        'lib/search_panel',
        'lib/mustache',
        'lib/core',
        'lib/jfmfs',
        'lib/validate',
        'lib/activity_feed',
        'lib/popup',
        'lib/hub/hub_name_form'
    ],
    function (PeopleForm, liveFeed, SearchPanel, Mustache) {
        var $overlay = $('#overlay'),
            $containerPeople = $('#container_people'),
            $id_unistar = $('#id_unistar').val(),
            $activityFeed = $('.feed'),
            $docInviteCowriters = $('#doc-invite-co-writers'), $docInviteParticipants = $('#doc-invite-participants'),
            $hubHelp = $('#hub-help'), $searchPanel = $('.search-panel');

        liveFeed.init();

        $(document).click($.proxy(function (e) {
            var click = $(e.target), outsideDiv = $("#overlay div:first").parents();

            if (click.is(outsideDiv)) {
                $overlay.hide();
                $containerHelpFirstCreation.hide();
                $containerPeople.trigger('hide');
            }
        }, this));

        var successHandler = function (event, data) {
            if (data && data.message) {
                var $alert = $('#doc-actions-alert');

                $containerPeople.trigger('hide');
                $overlay.hide();

                $alert.removeClass('alert-error');
                $alert.removeClass('alert-success');

                if (data.success) {
                    $alert.addClass('alert-success');
                } else {
                    $alert.addClass('alert-error');
                }
                $alert.find('span').text(data.message);
                $alert.show().delay(5000).fadeOut(500);
            }
        };

        var errorHandler = function (data) {
            $containerPeople.trigger('hide');
            $overlay.hide();
            if (data && data.status == 500) {
                var $alert = $('#doc-actions-alert');
                $alert.removeClass('alert-success');
                $alert.addClass('alert-error');
                $alert.find('span').text('Something went wrong, please try again.');
                $alert.show().delay(10000).fadeOut(500);
            }
        };

        PeopleForm.attachTo('#container_people', {role: '', type: 'hub', resourceId: $id_unistar, submitLabel: 'Invite them!'});
        $containerPeople.on('success', successHandler);
        $containerPeople.on('error', errorHandler);

        function getPlaceHolder() {
            return 'Search in {0}...'.format($('.searchLocation ').text().trim().toLowerCase());
        }

        SearchPanel.attachTo($searchPanel, {placeHolder: getPlaceHolder()});
        $searchPanel.on('submit.unishared', function (event, query) {
            _gaq.push(['_trackEvent', 'Hub', getPlaceHolder(), query]);
            $activityFeed.activityFeed(
                {
                    query: query
                });
        });

        var canCreate = $('#canCreate').val();
        $activityFeed.activityFeed(
            {
                documents: {
                    enabled: true
                },
                userId: $('#id_unistar').val(),
                createfromUserId: $('#id_unistar').val(),
                viewFor: $('#id_unistar').val(),
                withPagination: true,
                canCreate: canCreate,
                maxItems: max_activities
            });

        $('.add_feed_item').click(function () {
            need_refresh = true;
        });

        var $containerHelpFirstCreation = $('#container_help_first_creation');
        if ($containerHelpFirstCreation.length) {
            $containerHelpFirstCreation.unishared_popup();

            if (typeof first_creation != "undefined") {
                $containerHelpFirstCreation.unishared_popup('show');
            }
        }

        $hubHelp.click(function () {
            $containerHelpFirstCreation.unishared_popup('show');
        });

        var showPeopleForm = function () {
            $overlay.show();

            $containerPeople.trigger('setRole', {role:$(this).data('role')});
            $containerPeople.trigger('show');

            $containerPeople.on('hide', function () {
                $overlay.hide();
            });
        };

        $docInviteCowriters.click(showPeopleForm);
        $docInviteParticipants.click(showPeopleForm);

        function getOrganizationMembers() {
            var $id_unistar = $('#id_unistar').val(),
                templateAuthor = '{{#author}}<li><a href="{{profile_link}}" class="info" title="{{first_name}}" target="_blank"> <img src="{{picture}}" class="info userphoto" height="90px" width="90px"></a></li>{{/author}}',
                $organizationMembers = $('#organization_members'),

                $organizationMembersContainer = $('#organization_members').find('.co_writers'),
                $organizationMembersLoading = $('#organization_members').find('.loading');

            $organizationMembersContainer.hide();
            ajaxSend('/hub/cowriters/' + $id_unistar, 'GET', null, function (model) {
                $organizationMembersLoading.show();

                if (model.cowriters && model.cowriters.length) {
                    $organizationMembersContainer.find('ul').empty();

                    for (var indCowriter in model.cowriters) {
                        var cowriter = model.cowriters[indCowriter];

                        if (cowriter.id != $id_unistar) {
                            $organizationMembersContainer.find('ul').append(Mustache.render(templateAuthor, {
                                author: cowriter
                            }));
                        }
                    }

                    if (model.role == 'partners') {
                        $organizationMembers.insertAfter($('#organization_newsfeed'));
                    }

                    $organizationMembersContainer.show();
                    $organizationMembers.show();

                    $(function () {
                        var $carousel_next = $organizationMembers.find('.carousel_next');
                        var $carousel_prev = $organizationMembers.find('.carousel_prev');
                        $organizationMembersContainer.jCarouselLite({
                            btnNext: $carousel_next,
                            btnPrev: $carousel_prev,
                            visible: 8,
                            circular: false
                        });

                        $organizationMembersContainer.css('margin', '0 auto');

                        $organizationMembersContainer.find('ul li').css('height', '90px');

                        if (model.cowriters.length > 8) {
                            $carousel_prev.css('visibility', 'visible');
                            $carousel_next.css('visibility', 'visible');
                        }
                        else {
                            $carousel_prev.css('visibility', 'hidden');
                            $carousel_next.css('visibility', 'hidden');
                        }
                    });

                }

                $organizationMembersLoading.hide();
                $('#organization_members').find('.info:not(.info[rel="tooltip"])').each(function () {
                    $(this).attr('rel', 'tooltip');
                    $(this).tooltip();
                });
            });
        }

        getOrganizationMembers();

        $(window).on('refresh.unishared', function () {
            getOrganizationMembers();
        });
    });