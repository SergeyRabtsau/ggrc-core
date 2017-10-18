/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Component from '../related-people-access-control';

describe('GGRC.relatedPeopleAccessControl', function () {
  var viewModel;

  beforeAll(function () {
    viewModel = new (can.Map.extend(Component.prototype.viewModel));
  });

  describe('"getFilteredRoels" method', function () {
    var instance;

    beforeAll(function () {
      GGRC.access_control_roles = [
        {id: 1, name: 'Admin', object_type: 'Control'},
        {id: 2, name: 'Admin', object_type: 'Vendor'},
        {id: 3, name: 'Primary Contacts', object_type: 'Control'},
        {id: 4, name: 'Secondary Contacts', object_type: 'Control'},
        {id: 5, name: 'Principal Assignees', object_type: 'Control'},
        {id: 6, name: 'Secondary Assignees', object_type: 'Control'},
      ];

      instance = {
        'class': {
          model_singular: 'Control',
        },
      };
    });

    beforeEach(function () {
      viewModel.attr('instance', instance);
      viewModel.attr('includeRoles', []);
      viewModel.attr('excludeRoles', []);
    });

    afterAll(function () {
      delete GGRC.access_control_roles;
    });

    it('should return all roles related to instance type', function () {
      var roles = viewModel.getFilteredRoels();
      expect(roles.length).toBe(5);
    });

    it('should return roles from IncludeRoles list', function () {
      var roles;
      var include = ['Admin', 'Secondary Contacts', 'Principal Assignees'];

      viewModel.attr('includeRoles', include);
      roles = viewModel.getFilteredRoels();

      expect(roles.length).toBe(3);
      expect(roles[2].name).toEqual('Principal Assignees');
    });

    it('should return all roles except roles from ExcludeRoles list',
      function () {
        var roles;
        var exclude = ['Admin', 'Secondary Contacts', 'Principal Assignees'];

        viewModel.attr('excludeRoles', exclude);
        roles = viewModel.getFilteredRoels();

        expect(roles.length).toBe(2);
        expect(roles[1].name).toEqual('Secondary Assignees');
      }
    );

    it('should return roles from IncludeRoles withou roles from ExcludeRoles',
      function () {
        var roles;
        var include = ['Admin', 'Secondary Contacts', 'Principal Assignees'];
        var exclude = ['Admin', 'Principal Assignees', 'Primary Contacts'];

        viewModel.attr('includeRoles', include);
        viewModel.attr('excludeRoles', exclude);
        roles = viewModel.getFilteredRoels();

        expect(roles.length).toBe(1);
        expect(roles[0].name).toEqual('Secondary Contacts');
      }
    );
  });
});
