/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tag = 'custom-roles';
  var tpl = can.view(GGRC.mustache_path +
    '/components/custom-roles/custom-roles.mustache');

  GGRC.Components('customRoles', {
    tag: tag,
    template: tpl,
    viewModel: {
      instance: {},
      updatableGroupId: null,
      includeRoles: [],
      excludeRoles: [],
      save: function (args) {
        var self = this;
        this.attr('updatableGroupId', args.groupId);
        this.attr('instance').save()
          .then(function () {
            self.attr('instance').dispatch('refreshInstance');
            self.attr('updatableGroupId', null);
          });
      },
    },
  });
})(window.can, window.GGRC);
