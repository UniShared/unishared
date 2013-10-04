/*
 *  Project:
 *  Description:
 *  Author:
 *  License:
 */

// the semi-colon before function invocation is a safety net against concatenated
// scripts and/or other plugins which may not be closed properly.
define(["./mustache", "./jquery.shorten", "./jcarousellite_1.0.1", "./glob", "./jquery.simplePagination"], function (Mustache) {

    // undefined is used here as the undefined global variable in ECMAScript 3 is
    // mutable (ie. it can be changed by someone else). undefined isn't really being
    // passed in so we can ensure the value of it is truly undefined. In ES5, undefined
    // can no longer be modified.

    // window and document are passed through as local variable rather than global
    // as this (slightly) quickens the resolution process and can be more efficiently
    // minified (especially when both are regularly referenced in your plugin).

    // Create the defaults once
    var pluginName = "activityFeed",
        defaults = {
            hubs: {
                enabled: false,
                itemTemplate : '#hub_template',
                deleteHandler: null // Not used for the moment
            },
            documents: {
                enabled: false,
                itemTemplate: '#note_template',
                deleteHandler: null // Not used for the moment
            },
            baseUrl: !window.location.origin ? window.location.origin = window.location.protocol+"//"+window.location.host : window.location.origin,
            userId: null, // all, featured, live or a user id
            createfromUserId: null,
            viewFor: null, // Point of view (me or current user)
            maxItems: null,
            query: null, // Search query
            withPagination: false, /// Pagination or auto defilment
            seeAll: false,
            canCreate: false,
            canDelete: false
        };

    // The actual plugin constructor
    function ActivityFeed(element, options) {
        this.$element = $(element);

        // jQuery has an extend method which merges the contents of two or
        // more objects, storing the result in the first object. The first object
        // is generally empty as we don't want to alter the default this.options for
        // future instances of the plugin
        this.options = $.extend(true, {}, defaults, options);

        this._defaults = defaults;
        this._name = pluginName;

        this.init();
    }

    ActivityFeed.prototype = {

        /// Init the component and bind the events to the DOM elements
        init: function () {
            this.$container = this.$element.find('.container .items');
            this.$pagination = this.$element.find('.pagination');
            this.$loading = this.$element.find('.loading');
            this.$nothingSharedYet = this.$element.find('.nothing-shared-yet');
            this.$cache = this.$element.find('.cache');

            $(window).on('refresh.unishared', $.proxy(this.refresh, this));

            this.$element.mouseover($.proxy(this.pauseActivityFeed, this));
            this.$element.mouseleave($.proxy(this.runActivityFeed, this));

            this.reset();

            this.goToPage(this.last_page);
        },

        reset: function() {
            this.$container.empty();
            this.totalRecords = 0;
            this.items = null;
            this.first_time = true;
            this.last_page = 1;

            var $addFeedItem = this.$element.find('.add_feed_item'),
                url;

            if(this.options.canCreate) {
                if(this.options.documents.enabled) {
                    url = "/notes/create/"
                    if(this.options.createfromUserId) {
                        url += "?from={0}".format(this.options.createfromUserId);
                    }
                }
                else if(this.options.hubs.enabled) {
                    url = "/hubs/create/";
                }

                $addFeedItem.find('a').attr("href", url);
                $addFeedItem.show();
            }
            else {
                $addFeedItem.hide();
            }

            this.$pagination.pagination('destroy');
            if (this.options.withPagination) {
                this.$pagination.show();
            }
            else {
                this.$pagination.hide();
            }

            var $seeAllItem = this.$element.find('.see-all');
            if(this.options.seeAll) {
                var objectName, seeAllhref;
                if(this.options.documents.enabled) {
                    objectName = 'notes';
                    seeAllhref = '/profile?view=all_documents';
                }
                else if(this.options.hubs.enabled) {
                    objectName = 'hubs';
                    seeAllhref = '/profile?view=hubs';
                }
                $seeAllItem.find('span.object-name').text(objectName);
                $seeAllItem.find('a').attr('href', seeAllhref);
                $seeAllItem.show();
            }
            else {
                $seeAllItem.hide();
            }

            if(this.options.canDelete && this.options.documents.enabled) {
                this.$element.find('#modal-delete-document .btn-danger').click($.proxy(this.deleteHandler, this));
            }
            else {
                this.$element.off('click', '#modal-delete-document .btn-danger');
            }

            this.cleanInterval();
            this.clearCache();
        },

        /// Retrieve activity from the activity REST endpoint
        getActivity: function () {
            this.pauseActivityFeed();

            var max_items = this.options.maxItems;
            if (!this.options.withPagination) {
                max_items = max_items * 2;
            }

            var url = this.options.baseUrl + '/activity';
            if(this.options.userId) {
                url += '/'+this.options.userId;
            }
            else {
                url += '/all';
            }

            if(this.options.hubs.enabled) {
                url += '/hubs';
            }
            else if(this.options.documents.enabled) {
                url += '/documents';
            }

            url += '?max_items=' + max_items + '&page=' + this.last_page;

            if(this.options.query) {
                url += '&q=' + this.options.query;
            }

            ajaxSend(url, 'GET', null, $.proxy(this.successGetActivity, this));
        },

        /// Handler when the call to the activity REST endpoint succeed
        successGetActivity: function (data) {
            this.$loading.hide();

            if (data) {
                this.totalRecords = data.totalRecords;

                if(this.options.hubs.enabled) {
                    this.items = data.hubs;
                }
                else {
                    this.items = data.documents;
                }

                var length = 0;
                if (this.totalRecords == 0) {
                    this.$nothingSharedYet.removeClass('hide');
                } else {
                    if (this.items.length < this.options.maxItems) {
                        length = this.items.length;
                    } else {
                        length = this.options.maxItems;
                    }
                }

                for (var i = 0; i < length; i++) {
                    var item = this.items.shift();

                    if (i == 0) {
                        this.getActivityView(item, true, false);
                    } else {
                        this.getActivityView(item, false, false);
                    }

                    if (!this.options.withPagination) {
                        this.items.push(item);
                    }
                }

                if (this.options.withPagination) {
                    if (this.totalRecords > this.options.maxItems) {
                        if (this.first_time) {
                            this.$pagination.empty();

                            this.$pagination.pagination({
                                items: this.totalRecords,
                                itemsOnPage: this.options.maxItems,
                                cssStyle: 'light-theme',
                                onPageClick: $.proxy(this.goToPage, this)
                            });

                            this.first_time = false;
                        }

                        this.$pagination.show();
                    }
                }

                this.runActivityFeed();
            }
        },

        cleanInterval: function () {
            if (this.intervalId) {
                clearInterval(this.intervalId);
                this.intervalId = null;
            }
        },

        /// Pause the activity feed.
        /// Only used when not paginated.
        pauseActivityFeed: function () {
            this.cleanInterval();
            this.$container.find('.current').removeClass('current');
        },

        /// Run the activity feed
        /// Only used when not paginated
        runActivityFeed: function () {
            this.cleanInterval();

            if (!this.options.withPagination && this.items && this.totalRecords > this.options.maxItems) {
                this.$container.children().first().addClass('current');
                this.intervalId = setInterval($.proxy(this.showNextActivity, this), 4000);
            }
        },

        /// Get and display a specific page
        /// Only used when paginated
        goToPage: function (id_page) {
            if (this.options.withPagination) {
                this.last_page = id_page;

                this.$loading.show();
                this.$nothingSharedYet.addClass('hide');
                this.$container.empty();
                this.$pagination.hide();

                var $pageCache = this.$cache.find('#page-cache-' + this.last_page);
                if ($pageCache.length) {
                    this.$container.append($pageCache.children().clone());
                    this.$pagination.show();
                    this.$loading.hide();
                }
                else {
                    this.getActivity();
                }
            }
            else {
                this.$loading.show();
                this.$container.empty();
                this.getActivity();
            }
        },

        /// Create a HTML activity element from a JSON object
        getActivityView: function (item, current, new_element) {
            var $current_user_id = this.options.viewFor || this.options.userId,
            creator, cowriter, participant, i;

            item.authors = [];

            if(item.creator) {
                creator = item.creator.id == $current_user_id;
                item.authors.push(item.creator);
            }

            i = 0;
            while (i < item.cowriters.length) {
                item.authors.push(item.cowriters[i]);
                if (!cowriter && item.cowriters[i].id == $current_user_id) {
                    cowriter = true;
                }
                i++;
            }

            if(!creator && !cowriter) {
                i = 0;
                while (!participant && i < item.participants.length) {
                    if (item.participants[i].id == $current_user_id) {
                        participant = true;
                    }
                    i++;
                }
            }

            var template;
            var templateData;
            if(this.options.hubs.enabled) {
                template = this.$element.find(this.options.hubs.itemTemplate).html();
                templateData = {
                    hub: item,
                    item_is_current: current ? 'current' : '',
                    item_is_new: new_element ? 'new' : '',
                    hasAuthors: item.cowriters.length > 0,
                    hasMoreThan5Authors: item.cowriters.length > 0,
                    authors: item.cowriters,
                    user_role : (creator || cowriter) ? 'share' : participant ? 'participate' : 'no_interaction'
                };
            }
            else if(this.options.documents.enabled) {
                template = this.$element.find(this.options.documents.itemTemplate).html();
                templateData = {
                    title : item.resource.title,
                    resource_id : item.resource.id,
                    user_role : (creator || cowriter) ? 'share' : participant ? 'participate' : 'no_interaction',
                    authors : item.authors,
                    hasAuthors : item.authors.length > 0,
                    hasMoreThan5Authors : item.authors.length > 5,
                    updated : Globalize.format(new Date(item.resource.updated*1000), 'd'),
                    can_delete : typeof (is_my_profile) != 'undefined' && is_my_profile && (creator || cowriter || participant),
                    document_current : current ? 'current' : '',
                    document_new : new_element ? 'new' : '',
                    nb_views: item.resource.views
                };
            }

            var $render = $(Mustache.render(template, templateData));

            this.$container.append($render);

            if (this.options.withPagination) {
                var $pageCache = this.$cache.find('#page-cache-' + this.last_page);
                if (!$pageCache.length) {
                    $pageCache = $('<div></div>');
                    $pageCache.attr('id', 'page-cache-' + this.last_page);
                    this.$cache.append($pageCache);
                }
            }

            if (new_element) {
                this.$element.find('div.new').fadeIn('slow').removeClass('new');
            }

            $(function () {
                var $carousel_prev = $render.find(".carousel_prev");
                var $carousel_next = $render.find(".carousel_next");
                $render.find(".co_writers").each(function () {
                    $(this).jCarouselLite({
                        btnNext: $carousel_next,
                        btnPrev: $carousel_prev,
                        visible: 5,
                        circular: false
                    });

                    $(this).find('li').each(function () {
                        $(this).css('overflow', 'visible');
                    });

                    $(this).find('.info:not(.info[rel="tooltip"])').each(function () {
                        $(this).attr('rel', 'tooltip');
                        $(this).tooltip();
                    });

                    $(this).css('margin', '0 auto');
                });

                if (item.cowriters.length > 5) {
                    $carousel_prev.css('visibility', 'visible');
                    $carousel_next.css('visibility', 'visible');
                }
                else {
                    $carousel_prev.css('visibility', 'hidden');
                    $carousel_next.css('visibility', 'hidden');
                }
            });

            $render.find(".feed_item_title h2").each(function () {
                $(this).shorten({
                    width: 264,
                    tail: '...',
                    tooltip: true
                });
            });

            $render.find('.close').click(function () {
                var $current_document = $(this).closest(".feed_item");
                $current_document.addClass("deleted");
            });

            if (this.options.withPagination) {
                $pageCache.append($render.clone());
            }

            return $render;
        },

        /// Show the next activity in the model list
        /// Only used when no pagination
        showNextActivity: function () {
            var curActivity = this.$element.find('div.current'),
            nxtActivity = curActivity.next();

            curActivity.removeClass('current').addClass('old').fadeOut('slow', $.proxy(this.addNextActivity, this, nxtActivity));
        },

        /// Add the next activity from the model list
        /// Only used when no pagination
        addNextActivity: function (nxtActivity) {
            nxtActivity.addClass('current');

            var nxtActivityModel = this.items.shift();

            this.getActivityView(nxtActivityModel, false, true);

            this.$element.find('div.old').remove();

            this.items.push(nxtActivityModel);
        },

        /// Handler called when deleting an activity in the feed
        deleteHandler: function () {
            var $current_item = $('.deleted');
            $current_item.hide();

            if (!this.$container.children(':visible').length) {
                this.$nothingSharedYet.removeClass('hide');
            }

            if (this.options.withPagination) {
                var $current_document_cache = this.$cache.find('#' + $current_item.attr('id'));
                if ($current_document_cache.length) {
                    $current_document_cache.addClass("deleted");
                }
            }

            ajaxSend('/notes/delete/' + $current_item.attr('id') + '/', 'DELETE', null, $.proxy(function () {
                $(".deleted").remove();
                $(".alert-error").hide();

                var $alert = $('#document_categories').find(".alert");
                $alert.find('span').text('Document successfully deleted.');
                $alert.addClass("alert").addClass("alert-success");
                $alert.removeClass('hide');
                $alert.delay(5000).fadeOut(500);

                if (this.options.withPagination) {
                    this.$cache.find('#page-cache-' + this.last_page).remove();
                }
            }, this),
                function () {
                    if ($instance_template_nothing_shared_yet) {
                        $instance_template_nothing_shared_yet.remove();
                    }
                    var $deletedResources = $(".deleted");
                    $deletedResources.show();
                    $deletedResources.removeClass("deleted");

                    var $alert = $('#document_categories').find(".alert");
                    $alert.find('span').text('Something went wrong while deleting your document. Please try again');
                    $alert.addClass("alert").addClass("alert-error");
                    $alert.removeClass('hide');
                });
        },

        /// Clear the cache
        /// Always called when options are modified
        clearCache: function() {
            if(this.options.withPagination) {
                this.$cache.empty();
            }
        },

        /// Refresh the feed
        /// Erase the cache from the current page
        refresh: function () {
            if (this.options.withPagination) {
                this.$cache.find('#page-cache-' + this.last_page).remove();
            }

            this.goToPage(this.last_page);
        }
    };

    // A really lightweight plugin wrapper around the constructor,
    // preventing against multiple instantiations
    $.fn[pluginName] = function (options) {
        var args = arguments;

        // Is the first parameter an object (options), or was omitted,
        // instantiate a new instance of the plugin.
        if (options === undefined || typeof options === 'object') {
            return this.each(function () {

                // Only allow the plugin to be instantiated once,
                // so we check that the element has no plugin instantiation yet
                var data = $.data(this, 'plugin_' + pluginName)
                if (!data) {

                    // if it has no instance, create a new one,
                    // pass options to our plugin constructor,
                    // and store the plugin instance
                    // in the elements jQuery data object.
                    $.data(this, 'plugin_' + pluginName, new ActivityFeed( this, options ));
                }
                else {
                    data.options = $.extend(true, data.options, options);
                    data.reset();
                    data.goToPage(data.last_page);
                }
            });

            // If the first parameter is a string and it doesn't start
            // with an underscore or "contains" the `init`-function,
            // treat this as a call to a public method.
        } else if (typeof options === 'string' && options[0] !== '_' && options !== 'init') {

            // Cache the method call
            // to make it possible
            // to return a value
            var returns;

            this.each(function () {
                var instance = $.data(this, 'plugin_' + pluginName);

                // Tests that there's already a plugin-instance
                // and checks that the requested public method exists
                if (instance instanceof ActivityFeed && typeof instance[options] === 'function') {

                    // Call the method of our plugin instance,
                    // and pass it the supplied arguments.
                    returns = instance[options].apply( instance, Array.prototype.slice.call( args, 1 ) );
                }

                // Allow instances to be destroyed via the 'destroy' method
                if (options === 'destroy') {
                    $.data(this, 'plugin_' + pluginName, null);
                }
            });

            // If the earlier cached method
            // gives a value back return the value,
            // otherwise return this to preserve chainability.
            return returns !== undefined ? returns : this;
        }
    };

});