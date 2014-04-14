/**
 * API dynamic content
 */
(function($) {

    "use strict";

    $(function() {
        $('[data-api]').each(function() {
            var $this = $(this);

            $.get($this.data('api'), function(data) {
                $this.text(JSON.stringify(data, undefined, 2));
            });
        });
    });


}(window.jQuery));
