/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

(function (can, GGRC) {
  'use strict';

  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/assessment-people.mustache');
  var tag = 'assessment-people';

  can.Component.extend({
    tag: tag,
    template: tpl,
    viewModel: {
      define: {
        emptyMessage: {
          type: 'string',
          value: '',
        },
      },
      roleConflicts: false,
      infoPaneMode: true,
      withDetails: false,
      instance: {},
      conflictRoles: ['Assessor', 'Verifier'],
      orderOfRoles: ['Creator', 'Assessor', 'Verifier'],
    },
    events: {
      '{instance} roleConflicts': function (ev, args) {
        this.viewModel.attr('roleConflicts', args.roleConflicts);
      },
    },
  });
})(window.can, window.GGRC);
