/*
    Copyright (C) 2019 Google Inc.
    Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import canStache from 'can-stache';
import CanMap from 'can-map';
import CanComponent from 'can-component';
import '../redirects/proposable-control/proposable-control';
import template from './base-inline-control-title.stache';

export default CanComponent.extend({
  tag: 'base-inline-control-title',
  view: canStache(template),
  leakScope: false,
  viewModel: CanMap.extend({
    define: {
      isEditIconAllowed: {
        get: function () {
          return !this.attr('editMode') &&
            !this.attr('isLoading') &&
            !this.attr('isEditIconDenied');
        },
      },
      redirectionAttrName: {
        get() {
          return this.attr('title').trim().toLowerCase().replace(/[\s]+/g, '_');
        },
      },
    },
    instance: null,
    title: '',
    isLoading: false,
    editMode: false,
    isEditIconDenied: false,
    redirectionEnabled: false,
  }),
  events: {
    '.inline-edit-icon click': function () {
      this.viewModel.dispatch('setEditModeInline');
    },
  },
});
