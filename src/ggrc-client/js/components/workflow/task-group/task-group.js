/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import '../../info-pin-buttons/info-pin-buttons';
import '../taskgroup_clone';
import '../task-list/task-list';
import '../task-group-objects/task-group-objects';
import template from './templates/task-group.mustache';
import Permission from '../../../permission';

const viewModel = can.Map.extend({
  define: {
    canEdit: {
      get() {
        return (
          Permission.is_allowed_for('update', this.attr('instance')) &&
          this.attr('workflow.status') !== 'Inactive'
        );
      },
    },
  },
  instance: null,
  workflow: null,
  options: null,
  async loadWorkflow() {
    const instance = this.attr('instance');
    const workflow = await instance.refresh_all('workflow');
    this.attr('workflow', workflow);
  },
});


const init = function () {
  this.viewModel.loadWorkflow();
};

export default can.Component.extend({
  tag: 'task-group',
  template,
  viewModel,
  init,
});
