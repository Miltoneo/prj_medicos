/*! django-select2 adapter for Select2 */
(function($) {
    if (!$.fn.select2) return;
    $.fn.djangoSelect2 = function(options) {
        return this.each(function() {
            $(this).select2(options);
        });
    };
})(jQuery);
