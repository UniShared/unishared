'use strict';

define(['./mustache', './core', './jquery.shorten', './jcarousellite_1.0.1'],
    function (Mustache) {
        var $live_documents = $('#live_documents');
        var $arrow_to_left = $live_documents.find('.arrow_to_left');
        var $arrow_to_right = $live_documents.find('.arrow_to_right');

        var templateAuthor = '<li>{{#author}}<a href="/{{username}}" class="info" title="{{first_name}}" target="_blank"> <img src="{{picture}}" class="userphoto thumbnail_32x32" height="32px" width="32px"></a>{{/author}}</li>';

        var lastClassId = 0;
        var liveDocuments = null;
        var MAX_TITLE_LENGTH = 30;
        var isClose = false;

        function init() {
            $live_documents.find('.close').click(function (event) {
                event.preventDefault();
                $('#live_documents').slideToggle();
                isClose = true;
            });

            $arrow_to_left.click(function (event) {
                if (lastClassId > 0) {
                    lastClassId--;
                    loadModelToView();
                }
            });

            $arrow_to_right.click(function (event) {
                if (lastClassId < liveDocuments.length) {
                    lastClassId++;
                    loadModelToView();
                }
            });

            isClose = false;
            runLiveFeed();
            setInterval("liveFeed.runLiveFeed()", 600000);
        }

        function runLiveFeed() {
            if (!isClose) {
                window.ajaxSend('/activity/live/documents', 'GET', null, function (data) {
                    if (data.totalRecords) {
                        liveDocuments = data.documents;
                        lastClassId = 0;

                        var resource_id = $('#resource_id').val();
                        if (!(data.totalRecords == 1 && resource_id && resource_id == liveDocuments[lastClassId].resource.id)) {
                            $('#live_documents').animate({'bottom': '0px'}, 500, function () {
                                loadModelToView();
                            });
                        }
                    }
                });
            }
        }


        function loadModelToView() {
            var resource_id = $('#resource_id').val();

            if (resource_id) {
                for (var documentId in liveDocuments) {
                    if (resource_id == liveDocuments[documentId].resource.id) {
                        liveDocuments.splice(documentId, 1);
                    }
                }
            }

            var model = liveDocuments[lastClassId];

            if (!model) {
                return;
            }

            if (lastClassId == 0) {
                $arrow_to_left.css('visibility', 'hidden');
            }
            else {
                $arrow_to_left.css('visibility', 'visible');
            }

            if (lastClassId + 1 == liveDocuments.length) {
                $arrow_to_right.css('visibility', 'hidden');
            }
            else {
                $arrow_to_right.css('visibility', 'visible');
            }

            var title = $('<h3></h3>');
            title.text(model.resource.title);

            var $live_documents_link = $live_documents.find('#live_document_link');

            $live_documents_link.find('h3').remove();
            $live_documents_link.append(title);

            title.shorten({
                width: 216,
                tail: '...',
                tooltip: true
            });
            title.tooltip();

            $live_documents_link.attr('href', '/notes/' + model.resource.id);

            $('img#live_document_profile_image').attr('src', model.creator.picture);

            var profile_link = $('a#live_document_profile_link');
            profile_link.attr('href', '/profile/' + model.creator.id);
            profile_link.attr('title', model.creator.first_name);

            var resource_link = $live_documents.find('a#live_document_resource_link')
            resource_link.attr('href', '/notes/' + model.resource.id);
            resource_link.click(function (ev) {
                need_refresh = true;
            });
            $live_documents.find('span.number').text(liveDocuments.length);
            $live_documents.find('span#live_document_current_id').text(lastClassId + 1);

            var $cowriters_ul = $live_documents.find('div.co_writers ul');
            $cowriters_ul.empty();

            $cowriters_ul.append(Mustache.render(templateAuthor, {
                author: model.creator
            }));

            for (var indCowriter in model.cowriters) {
                var cowriter = model.cowriters[indCowriter];

                $cowriters_ul.append(Mustache.render(templateAuthor, {
                    author: cowriter
                }));
            }

            if ($cowriters_ul.children().length) {
                $live_documents.find('.info:not(.info[rel="tooltip"])').each(function () {
                    $(this).attr('rel', 'tooltip');
                    $(this).tooltip();
                });

                $(function () {
                    var $carousel_prev = $live_documents.find(".carousel_prev");
                    var $carousel_next = $live_documents.find(".carousel_next");

                    $live_documents.find(".co_writers").each(function () {
                        $(this).jCarouselLite({
                            btnNext: $carousel_next,
                            btnPrev: $carousel_prev,
                            visible: 5,
                            circular: false
                        });

                        $(this).css('margin', '0 auto');

                    });

                    if (model.cowriters.length > 5) {
                        $carousel_prev.css('visibility', 'visible');
                        $carousel_next.css('visibility', 'visible');
                    } else {
                        $cowriters_ul.attr('style', '');
                        $carousel_prev.css('visibility', 'hidden');
                        $carousel_next.css('visibility', 'hidden');
                    }
                });
            }
        }

        return {
            "init": init,
            "runLiveFeed": runLiveFeed
        }
    });