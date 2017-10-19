/*
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import Component from '../related-people-access-control';

describe('GGRC.relatedPeopleAccessControl', function () {
  var viewModel;

  beforeAll(function () {
    viewModel = new (can.Map.extend(Component.prototype.viewModel));

    GGRC.access_control_roles = [
      {id: 1, name: 'Admin', object_type: 'Control'},
      {id: 2, name: 'Admin', object_type: 'Vendor'},
      {id: 3, name: 'Primary Contacts', object_type: 'Control'},
      {id: 4, name: 'Secondary Contacts', object_type: 'Control'},
      {id: 5, name: 'Principal Assignees', object_type: 'Control'},
      {id: 6, name: 'Secondary Assignees', object_type: 'Control'},
    ];
  });

  afterAll(function () {
    delete GGRC.access_control_roles;
  });

  describe('"getFilteredRoels" method', function () {
    var instance;

    beforeAll(function () {
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

  describe('"checkConflicts" method', function () {
    var instance;

    beforeAll(function () {
      instance = new can.Map({
        'class': {
          model_singular: 'Control',
        },
      });
    });

    beforeEach(function () {
      viewModel.attr('instance', instance);
      viewModel.attr('includeRoles', []);
      viewModel.attr('excludeRoles', []);
    });

    function isGroupsHasConflict(conflictRoles, acl) {
      let groups;
      instance.attr('access_control_list', acl);
      viewModel.attr('instance', instance);
      viewModel.attr('groups', viewModel.getRoleList());
      groups = viewModel.attr('groups');

      return viewModel
        .isGroupsHasConflict(groups, conflictRoles);
    }

    function isCurrentGroupHasConflict(currentGroup, conflictRoles, acl) {
      let groups;
      instance.attr('access_control_list', acl);
      viewModel.attr('instance', instance);
      viewModel.attr('groups', viewModel.getRoleList());
      groups = viewModel.attr('groups');

      return viewModel
        .isCurrentGroupHasConflict(currentGroup, groups, conflictRoles);
    }

    it('"isGroupsHasConflict" should return TRUE. 2 groups conflict',
      function () {
        let conflictRoles = ['Admin', 'Primary Contacts'];
        let hasConflicts = false;
        let acl = [
          {ac_role_id: 1, person: {id: 1}},
          {ac_role_id: 1, person: {id: 2}},
          {ac_role_id: 1, person: {id: 3}},
          // conflict with ac_role_id: 1
          {ac_role_id: 3, person: {id: 3}},
          {ac_role_id: 3, person: {id: 4}},
          {ac_role_id: 4, person: {id: 1}},
        ];

        hasConflicts = isGroupsHasConflict(conflictRoles, acl);
        expect(hasConflicts).toBeTruthy();
      }
    );

    it('"isGroupsHasConflict" should return TRUE. 3 groups conflict',
      function () {
        let conflictRoles = [
          'Admin',
          'Primary Contacts',
          'Secondary Assignees',
        ];
        let hasConflicts = false;
        let acl = [
          {ac_role_id: 1, person: {id: 1}},
          {ac_role_id: 1, person: {id: 2}},
          {ac_role_id: 1, person: {id: 3}},

          // conflict with ac_role_id: 1
          {ac_role_id: 3, person: {id: 3}},
          {ac_role_id: 3, person: {id: 4}},
          {ac_role_id: 4, person: {id: 1}},

          // conflict with ac_role_id 3
          {ac_role_id: 6, person: {id: 4}},
        ];

        hasConflicts = isGroupsHasConflict(conflictRoles, acl);
        expect(hasConflicts).toBeTruthy();
      }
    );

    it('"isGroupsHasConflict" should return FALSE. 3 groups conflict',
      function () {
        let conflictRoles = [
          'Admin',
          'Primary Contacts',
          'Secondary Assignees',
        ];
        let hasConflicts = false;
        let acl = [
          {ac_role_id: 1, person: {id: 1}},
          {ac_role_id: 1, person: {id: 2}},
          {ac_role_id: 1, person: {id: 3}},
          {ac_role_id: 3, person: {id: 7}},
          {ac_role_id: 3, person: {id: 4}},
          {ac_role_id: 4, person: {id: 1}},
          {ac_role_id: 6, person: {id: 14}},
        ];

        hasConflicts = isGroupsHasConflict(conflictRoles, acl);

        expect(hasConflicts).toBeFalsy();
      }
    );

    it('"isCurrentGroupHasConflict" should return TRUE. 2 groups conflict',
      function () {
        let conflictRoles = ['Admin', 'Primary Contacts'];
        let hasConflicts = false;
        let acl = [
          {ac_role_id: 1, person: {id: 1}},
          {ac_role_id: 1, person: {id: 2}},
          {ac_role_id: 1, person: {id: 3}},
          // conflict with ac_role_id: 1
          {ac_role_id: 3, person: {id: 3}},
          {ac_role_id: 3, person: {id: 4}},
          {ac_role_id: 4, person: {id: 1}},
        ];

        hasConflicts = isCurrentGroupHasConflict('Admin', conflictRoles, acl);
        expect(hasConflicts).toBeTruthy();
      }
    );

    it('"isCurrentGroupHasConflict" should return TRUE. 3 groups conflict',
      function () {
        let conflictRoles = [
          'Admin',
          'Primary Contacts',
          'Secondary Assignees',
        ];
        let hasConflicts = false;
        let acl = [
          {ac_role_id: 1, person: {id: 1}},
          {ac_role_id: 1, person: {id: 2}},
          {ac_role_id: 1, person: {id: 3}},

          // conflict with ac_role_id: 1
          {ac_role_id: 3, person: {id: 3}},
          {ac_role_id: 3, person: {id: 4}},
          {ac_role_id: 4, person: {id: 1}},

          // conflict with ac_role_id 3
          {ac_role_id: 6, person: {id: 4}},
        ];

        hasConflicts = isCurrentGroupHasConflict('Admin', conflictRoles, acl);
        expect(hasConflicts).toBeTruthy();
      }
    );

    it('"isCurrentGroupHasConflict" should return FALSE. 3 groups conflict',
      function () {
        let conflictRoles = [
          'Admin',
          'Primary Contacts',
          'Secondary Assignees',
        ];
        let hasConflicts = false;
        let acl = [
          {ac_role_id: 1, person: {id: 1}},
          {ac_role_id: 1, person: {id: 2}},
          {ac_role_id: 1, person: {id: 3}},
          {ac_role_id: 3, person: {id: 7}},
          {ac_role_id: 3, person: {id: 4}},
          {ac_role_id: 4, person: {id: 1}},
          {ac_role_id: 6, person: {id: 14}},
        ];

        hasConflicts = isCurrentGroupHasConflict('Admin', conflictRoles, acl);
        expect(hasConflicts).toBeFalsy();
      }
    );
  });
});
