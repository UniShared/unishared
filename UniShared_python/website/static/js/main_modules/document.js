'use strict';

require.config({
    baseUrl: window.staticUrl + 'js'
});

require(
    [
        'lib/people_form',
        'lib/mustache',
        'lib/live_feed',
        'lib/core',
        'lib/jcarousellite_1.0.1',
        'lib/jquery.sharrre-1.3.4.min'
    ],
    function (PeopleForm, Mustache, liveFeed) {
        var $overlay = $('#overlay'), $loading = $overlay.find('.loading'), $socialPanel,
            $containerPeople = $('#container_people'), $container_login_session = $('#container_login_session'),
            $container_help_first_creation = $('#container_help_first_creation'), $container_help_first_participation = $('#container_help_first_participation'),
            $doc_people = $('#doc-co-writers'), $carousel_next = $doc_people.find('.carousel_next'), $carousel_prev = $doc_people.find('.carousel_prev'), templateCowriter = '<li style="overflow: visible; float: left;"><a href="/{{username}}" class="info userphoto" target="_blank" title="{{first_name}}"> <img src="{{picture}}" class="thumbnail_32x32" height="32px" width="32px"> </a></li>',
            successHandler, errorHandler;

        liveFeed.init();

        function openPopup(element, callBack) {
            var height = element.height(),
                winHeight = $(document).height(),
                top = 0;

            $overlay.fadeIn(500);
            element.fadeIn(500, callBack);

            if (winHeight > height) {
                top = Math.round((winHeight / 2) - (height / 2));
            }

            element.css('position', 'relative');
            element.css('top', top);
        }

        function openPeopleForm(role) {
            $overlay.show();

            $containerPeople.trigger('setRole', {role: role});
            $containerPeople.trigger('show');

            $containerPeople.on('hide', function () {
                $overlay.hide();
                $containerPeople.off('hide');
            });
        }

        function closePopup() {
            $overlay.fadeOut(500);
            $overlay.find('.form').hide();
            $('.btn-primary.active').removeClass('active');
        }

        function loaded() {
            $loading.hide();

            if ($container_help_first_creation.length && !$container_help_first_creation.is(':visible')) {
                setTimeout(function() { openPopup($container_help_first_creation); }, 6 * 1000);
            }
            else if($container_help_first_participation.length && !$container_help_first_participation.is(':visible')) {
                setTimeout(function() { openPopup($container_help_first_participation); }, 6 * 1000);
            }

            if (!$overlay.find('.form:visible').length) {
                closePopup();
            }

            if (!$container_login_session.length) {
                $(document).click(function (e) {
                    var click = $(e.target), outsideDiv = $("#overlay div:first").parents();

                    if (click.is(outsideDiv)) {
                        closePopup();
                    }
                });
            }
        }

        $('.doc-iframe').load(loaded);
        $(window).on('load.unishared', loaded);
        setTimeout("$(window).trigger('load.unishared');", 10 * 1000);

        $overlay.find('.close, .prev_button').click(function () {
            closePopup();
            return false;
        });

        $('body,html').css('height', $(window).height() - 71);

        $(window).resize(function () {
            $('body,html').css('height', $(window).height() - 71);
        });

        $('#doc-actions-alert').find('.close').click(function () {
            $(this).parent().hide();
        });

        if ($container_login_session.length) {
            $container_login_session.show();
        }
        else {
            $loading.show();
        }

        $overlay.show();
        window._gaq.push(['_trackEvent', 'Documents', 'Open', resource_type + ':' + resource_id]);

        $socialPanel = $('#social_panel');
        $socialPanel.sharrre({
            share: {
                facebook: true,
                twitter: true,
                googlePlus: true
            },
            buttons: {
                googlePlus: {
                    size: 'tall'
                },
                facebook: {
                    layout: 'box_count'
                },
                twitter: {
                    count: 'vertical',
                    via: 'UniShared'
                }
            },
            enableHover: false,
            enableCounter: false,
            enableTracking: true
        });

        $socialPanel.find('.close').click(function () {
            $(this).parent().fadeOut(500);
        });

        $('.profile_img,#hello a,#brand').attr('target', '_blank');

        errorHandler =  function (event, data) {
            $containerPeople.trigger('hide');
            $overlay.hide();
            if (data && data.status === 500) {
                var $alert = $('#doc-actions-alert');
                $alert.removeClass('alert-success');
                $alert.addClass('alert-error');
                $alert.find('span').text('Something went wrong, please try again.');
                $alert.show().delay(10000).fadeOut(500);
            }
        };

        successHandler = function (event, data) {
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

        PeopleForm.attachTo('#container_people', {role: '', type: 'notes', resourceId: $('#resource_id').val(), submitLabel: 'Invite them!'});
        $containerPeople.on('success', successHandler);
        $containerPeople.on('error', errorHandler);

        $('#doc-invite-co-writers, #doc-invite-participants').click(function () {
            openPeopleForm($(this).data('role'));
        });

        $container_help_first_creation.find('.next_button').click(function () {
            $(this).closest('.form').fadeOut(500, function () {
                openPeopleForm('cowriters');
            });
            return false;
        });

        ajaxSend('/notes/cowriters/' + $('#resource_id').val(), 'GET', null, function (data) {
            var cowriters = data.cowriters,
            $docCowritersUl = $doc_people.find('.co_writers ul'),
                i, cowriter;

            $docCowritersUl.empty();
            for (i in cowriters) {
                cowriter = cowriters[i];

                $docCowritersUl.append($(Mustache.render(templateCowriter, {
                    'username': cowriter.username,
                    'first_name': cowriter.first_name,
                    'picture': cowriter.picture
                })));
            }
            $doc_people.find('.co_writers_carousel').show();
            if ($docCowritersUl.children().length) {
                $doc_people.find('.co_writers').each(function () {
                    $(this).jCarouselLite({
                        btnNext: $carousel_next,
                        btnPrev: $carousel_prev,
                        visible: 5,
                        circular: false
                    });

                    $(this).find('li').each(function () {
                        $(this).css('overflow', 'visible');
                    });

                    $(this).find('.info').each(function () {
                        $(this).tooltip({
                            'placement': 'bottom'
                        });
                    });

                    $(this).css('margin', '0 auto');
                });

                if ($doc_people.find('.co_writers ul').children().length > 5) {
                    $carousel_next.css('visibility', 'visible');
                    $carousel_prev.css('visibility', 'visible');
                } else {
                    $carousel_next.css('visibility', 'hidden');
                    $carousel_prev.css('visibility', 'hidden');
                }
            }
        }, errorHandler);
    });