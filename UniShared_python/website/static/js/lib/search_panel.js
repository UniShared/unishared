define(
    [
        './components/component',
        'lib/jquery-ui-1.10.1.custom.min',
        './core'
    ],

    function(defineComponent)  {

        return defineComponent(searchPanel);

        function searchPanel() {
            this.defaultAttrs({
                searchField: '.search-field',
                searchButton: '.search-button',
                searchResults: '.search-results',
                resultsItems: '.search-results-items',
                searchObjects: 'documents',
                ulUiAutocomplete: 'ul.ui-autocomplete',
                autoComplete: false,
                titleOnly: false,
                placeHolder: undefined,
                cache : {}
            });

            this.after('initialize', function() {
                this.initSearchField();
                this.initSearchButton();

                this.on('setPlaceHolder.unishared', this.setPlaceHolder);
                this.on('setSearchObjects.unishared', this.setSearchObjects);
                this.on('reset.unishared', this.reset);
            });

            this.initSearchField = function () {
                this.on('keypress',
                    {
                        searchField: function (e) {
                            var code = (e.keyCode ? e.keyCode : e.which);
                            if(code == 13) { //Enter keycode
                                this.search();
                            }
                        }
                    });

                this.select('searchField').attr('placeHolder', this.attr.placeHolder);
            }

            this.reset = function () {
                this.select('searchField').val('');
            }

            this.setPlaceHolder = function (event, data) {
                this.attr.placeHolder = data;
                this.select('searchField').attr('placeHolder', this.attr.placeHolder);
            }

            this.setSearchObjects = function (event, data) {
                this.attr.searchObjects = data;
            }

            this.initSearchButton = function () {
                if(this.attr.autoComplete) {
                    var titleOnly = this.attr.titleOnly, cache = this.attr.cache,
                        $searchResults = this.select('searchResults').find('strong'),
                        searchedObjects = this.attr.searchObjects;

                    this.select('searchButton').hide();
                    this.select('searchField').autocomplete(
                        {
                            minLength: 1,
                            source: function( query, request ) {
                                var queryTerm = query.term;
                                if ( queryTerm in cache ) {
                                    request( cache[ queryTerm ] );
                                    return;
                                }

                                $.getJSON( "/activity/{0}/{1}".format('all', searchedObjects), {max_items: 5, q:queryTerm, titleOnly:titleOnly},
                                    function( data, status, xhr ) {
                                        cache[ queryTerm ] = data.documents;
                                        request( data.documents );
                                    } );
                            },
                            response: function(event, ui) {
                                var $ulUiAutocomplete = $("ul.ui-autocomplete");
                                // ui.content is the array that's about to be sent to the response callback.
                                if (ui.content.length === 0 && $ulUiAutocomplete.is(':visible')) {
                                    $("ul.ui-autocomplete").empty();
                                    $searchResults.hide();
                                } else {
                                    $searchResults.show();
                                    $ulUiAutocomplete;
                                }
                            },
                            open: function(event, ui) {
                                $searchResults.show();
                                $(".ui-autocomplete").css("position", "static");
                            },
                            close: function(event, ui) {
                                var $ulUiAutocomplete = $("ul.ui-autocomplete");
                                if ($ulUiAutocomplete.children().length && !$ulUiAutocomplete.is(':visible')) {
                                    $searchResults.show();
                                    $ulUiAutocomplete.show();
                                }
                                else {
                                    $searchResults.hide();
                                }
                            },
                            select: function(event, ui) {
                                $(event.target).trigger('clickSuggested.unishared', ui.item.resource.id);
                            },
                            appendTo: this.attr.resultsItems
                        }).data( "ui-autocomplete" )._renderItem = function( ul, item ) {
                            ul.css('position', 'static');
                            return $( "<li>" )
                                .append( "<a>{0} by {1}</a>".format(item.resource.title, item.creator.first_name) )
                                .appendTo( ul );
                        };
                }
                else {
                    this.select('searchButton').show().click($.proxy(this.search, this));
                }
            }

            this.search = function () {
                this.trigger('submit.unishared', this.select('searchField').val().split(" "));
            }
        }
    });