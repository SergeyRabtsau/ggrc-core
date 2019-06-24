/*
 Copyright (C) 2019 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import canStache from 'can-stache';
import CanComponent from 'can-component';
import '../person/person-data';
import viewModel from '../view-models/people-group-vm';
import template from './deletable-people-group.stache';

export default CanComponent.extend({
  tag: 'deletable-people-group',
  view: canStache(template),
  leakScope: true,
  viewModel,
});
