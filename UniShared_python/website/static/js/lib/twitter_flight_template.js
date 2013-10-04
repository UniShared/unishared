define(
    [
        './components/component',
        './core',
    ],

    function(defineComponent)  {

        return defineComponent(searchField);

        function searchField() {
            this.defaultAttrs({
            });

            this.after('initialize', function() {

            });
        }
    });