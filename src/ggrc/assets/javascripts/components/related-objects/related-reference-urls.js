/*!
    Copyright (C) 2017 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

(function (can, $) {
  'use strict';

  GGRC.Components('relatedReferenceUrls', {
    tag: 'related-reference-urls',
    viewModel: {
      element: null,
      define: {
        urls: {
          value: function () {
            return [];
          }
        },
        value: {
          type: 'string',
          value: ''
        },
        isFormVisible: {
          type: 'boolean',
          value: false
        },
        isDisabled: {
          type: 'boolean',
          value: false
        }
      },
      /**
       * @description Moves focus to the create url input element
       */
      moveFocusToInput: function () {
        var inputElements = this.element.find('input');
        if (inputElements.length) {
          inputElements[0].focus();
        }
      },
      /**
       * @description Validates user input
       *
       * @param  {String} data Data for validation
       * @return {Boolean} - If incoming string is empty it returns false,
       * otherwise true
       */
      validateUserInput: function (data) {
        return data.length > 0;
      },
      /**
       * @description Handles changes during toggling form visibility
       *
       * @param  {Boolean} value New value for form visibility
       */

      toggleFormVisibility: function (isVisible) {
        this.attr('isFormVisible', isVisible);
        this.attr('value', '');
        if (isVisible) {
          this.moveFocusToInput();
        }
      },
      /**
       * @description Handles create url form submitting
       *
       * @param  {String} url - url to create
       * @return {Boolean} - it returns false to prevent page refresh
       */

      submitCreateReferenceUrlForm: function (url) {
        var trimmedUrl = url.trim();
        var isValid = this.validateUserInput(trimmedUrl);

        // non-valid user input case - empty string
        if (!isValid) {
          $(document.body).trigger('ajax:flash', {
            error: 'Please enter a URL'
          });
          this.toggleFormVisibility(true);
          return false;
        }

        this.createReferenceUrl(trimmedUrl);

        this.toggleFormVisibility(false);
        return false;
      },
      /**
       * @description Dispatches 'createReferenceUrl' event with appropriate
       * data payload
       *
       * @param  {String} url - url to create
       */
      createReferenceUrl: function (url) {
        this.dispatch({
          type: 'createReferenceUrl',
          payload: url
        });
      },
      /**
       * @description Dispatches 'removeReferenceUrl' event with appropriate
       * data payload
       *
       * @param  {string} url - url to delete
       */
      removeReferenceUrl: function (url) {
        this.dispatch({
          type: 'removeReferenceUrl',
          payload: url
        });
      }
    },
    events: {
      /**
       * @description Handler for 'inserted' event to save reference
       * to component element
       */
      inserted: function () {
        this.viewModel.attr('element', this.element);
      }
    }
  });
})(window.can, window.can.$);
