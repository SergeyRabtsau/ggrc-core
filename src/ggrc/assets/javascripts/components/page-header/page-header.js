/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (GGRC, can) {
  'use strict';

  var template = can.view(GGRC.mustache_path +
    '/components/page-header/page-header.mustache'
  );
  var viewModel = can.Map.extend({
    define: {
      isMyAssessments: {
        type: Boolean,
        get: function () {
          return GGRC.Utils.CurrentPage.isMyAssessments();
        }
      },
      showTitles: {
        type: Boolean,
        value: true
      }
    },
    showHideTitles: function (element) {
      var elWidth = element.width();
      var $menu = element.find('.menu');
      var $title = element.find('h1');

      this.attr('showTitles', true);

      if (elWidth < ($menu.width() + $title.width())) {
        this.attr('showTitles', false);
      } else {
        this.attr('showTitles', true);
      }
    }
  });

  GGRC.Components('pageHeader', {
    tag: 'page-header',
    template: template,
    viewModel: viewModel,
    events: {
      '{window} resize': _.debounce(function () {
        this.viewModel.showHideTitles(this.element);
      }, 100),
      inserted: function () {
        this.viewModel.showHideTitles(this.element);
      }
    }
  });
})(window.GGRC, window.can);
