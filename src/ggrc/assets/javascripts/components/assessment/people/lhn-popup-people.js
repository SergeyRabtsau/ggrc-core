/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import template from './templates/lhn-popup-people.mustache';

export default GGRC.Components('lhnPopupPeople', {
  tag: 'lhn-popup-people',
  template: template,
  viewModel: {
    define: {
      instance: {
        set: function (value, setValue) {
          if (!value) {
            return;
          }

          value.refresh().then((refreshedInstance) => {
            this.attr('denyUnmap', false);
            setValue(refreshedInstance);
          });
        },
      },
    },
    denyUnmap: true,
    hasConflicts: false,
    conflictRoles: ['Assignees', 'Verifiers'],
    includeRoles: ['Creators', 'Assignees', 'Verifiers'],
    saveRoles: function () {
      this.attr('denyUnmap', true);
      this.attr('instance').save().then(() => {
        this.attr('denyUnmap', false);
      });
    },
  },
});
