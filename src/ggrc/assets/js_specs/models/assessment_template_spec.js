/*!
  Copyright (C) 2017 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

describe('can.Model.AssessmentTemplate', function () {
  'use strict';

  var AssessmentTemplate;
  var instance;  // an AssessmentTemplate instance

  beforeAll(function () {
    AssessmentTemplate = CMS.Models.AssessmentTemplate;
  });

  beforeEach(function () {
    instance = new AssessmentTemplate();
  });

  describe('_packPeopleData() method', function () {
    it('packs default people data into a JSON string', function () {
      var result;

      instance.attr('default_people', {
        assignees: 'Rabbits',
        verifiers: 'Turtles'
      });

      result = instance._packPeopleData();

      expect(result).toEqual({
        assignees: 'Rabbits',
        verifiers: 'Turtles'
      });
    });

    it('uses the list of chosen assignee IDs if default assignees are set ' +
      'to "other"',
      function () {
        var assessorIds;
        var result;

        instance.attr('default_people', {
          assignees: 'other',
          verifiers: 'Whatever'
        });

        assessorIds = new can.Map({'17': true, '2': true, '9': true});
        instance.attr('assigneesList', assessorIds);

        result = instance._packPeopleData();

        expect(result).toEqual({
          assignees: [2, 9, 17],
          verifiers: 'Whatever'
        });
      }
    );

    it('uses the list of chosen verifier IDs if default verifiers are set ' +
      'to "other"',
      function () {
        var verifierIds;
        var result;

        instance.attr('default_people', {
          assignees: 'Whatever',
          verifiers: 'other'
        });

        verifierIds = new can.Map({'12': true, '6': true, '11': true});
        instance.attr('verifiersList', verifierIds);

        result = instance._packPeopleData();

        expect(result).toEqual({
          assignees: 'Whatever',
          verifiers: [6, 11, 12]
        });
      }
    );
  });

  describe('_unpackPeopleData() method', function () {
    it('builds an IDs dict from the default assignees list', function () {
      instance.attr('default_people', {
        assignees: new can.List([5, 7, 12])
      });
      instance.attr('assigneesList', {});

      instance._unpackPeopleData();

      expect(
        instance.assigneesList.attr()
      ).toEqual({'5': true, '7': true, '12': true});
    });

    it('sets the default assignees option to "other" if needed', function () {
      // this is needed when the default assignees setting is actually
      // a list of User IDs...
      instance.attr('default_people', {
        assignees: new can.List([5, 7, 12])
      });

      instance._unpackPeopleData();

      expect(instance.default_people.assignees).toEqual('other');
    });

    it('clears the assignees IDs dict if needed', function () {
      instance.attr('assigneesList', {'42': true});
      instance.attr('default_people', {
        assignees: 'Some User Group'  // not a list of IDs
      });

      instance._unpackPeopleData();

      expect(instance.assigneesList.attr()).toEqual({});
    });

    it('builds an IDs dict from the default verifiers list', function () {
      instance.attr('default_people', {
        verifiers: new can.List([5, 7, 12])
      });
      instance.attr('verifiersList', {});

      instance._unpackPeopleData();

      expect(
        instance.verifiersList.attr()
      ).toEqual({'5': true, '7': true, '12': true});
    });

    it('sets the default verifiers option to "other" if needed', function () {
      // this is needed when the default verifiers setting is actually
      // a list of User IDs...
      instance.attr('default_people', {
        verifiers: new can.List([5, 7, 12])
      });

      instance._unpackPeopleData();

      expect(instance.default_people.verifiers).toEqual('other');
    });

    it('clears the verifiers IDs dict if needed', function () {
      instance.attr('verifiersList', {'42': true});
      instance.attr('default_people', {
        verifiers: 'Some User Group'  // not a list of IDs
      });

      instance._unpackPeopleData();

      expect(instance.verifiersList.attr()).toEqual({});
    });
  });

  describe('assigneeAdded() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('adds the new assignee\'s ID to the assignees list', function () {
      instance.attr('assigneesList', {'7': true});
      eventObj.selectedItem = {id: 42};

      instance.assigneeAdded(context, $element, eventObj);

      expect(
        instance.attr('assigneesList').attr()
      ).toEqual({'7': true, '42': true});
    });

    it('silently ignores duplicate entries', function () {
      instance.attr('assigneesList', {'7': true});
      eventObj.selectedItem = {id: 7};

      instance.assigneeAdded(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('assigneesList').attr()).toEqual({'7': true});
    });
  });

  describe('assigneeRemoved() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('removes the new assignee\'s ID from the assignees list', function () {
      instance.attr('assigneesList', {'7': true, '42': true, '3': true});
      eventObj.person = {id: 42};

      instance.assigneeRemoved(context, $element, eventObj);

      expect(
        instance.attr('assigneesList').attr()
      ).toEqual({'7': true, '3': true});
    });

    it('silently ignores removing non-existing entries', function () {
      instance.attr('assigneesList', {'7': true});
      eventObj.person = {id: 50};

      instance.assigneeRemoved(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('assigneesList').attr()).toEqual({'7': true});
    });
  });

  describe('verifierAdded() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('adds the new verifier\'s ID to the assignees list', function () {
      instance.attr('verifiersList', {'7': true});
      eventObj.selectedItem = {id: 42};

      instance.verifierAdded(context, $element, eventObj);

      expect(
        instance.attr('verifiersList').attr()
      ).toEqual({'7': true, '42': true});
    });

    it('silently ignores duplicate entries', function () {
      instance.attr('verifiersList', {'7': true});
      eventObj.selectedItem = {id: 7};

      instance.verifierAdded(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('verifiersList').attr()).toEqual({'7': true});
    });
  });

  describe('verifierRemoved() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('removes the new verifier\'s ID from the verifiers list', function () {
      instance.attr('verifiersList', {'7': true, '42': true, '3': true});
      eventObj.person = {id: 42};

      instance.verifierRemoved(context, $element, eventObj);

      expect(
        instance.attr('verifiersList').attr()
      ).toEqual({'7': true, '3': true});
    });

    it('silently ignores removing non-existing entries', function () {
      instance.attr('verifiersList', {'7': true});
      eventObj.person = {id: 50};

      instance.verifierRemoved(context, $element, eventObj);
      // there should have been no error

      expect(instance.attr('verifiersList').attr()).toEqual({'7': true});
    });
  });

  describe('defaultAssigneesChanged() method', function () {
    var context;
    var $element;
    var eventObj;
    var greenList;
    var redList;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
      instance.attr('showCaptainAlert', false);
      greenList = [
        'Auditors', 'Principal Assignees', 'Secondary Assignees',
        'Primary Contacts', 'Secondary Contacts',
      ];
      redList = [
        'Admin', 'Audit Lead', 'other',
      ];
    });

    it('sets the assigneesListDisable flag if the corresponding ' +
      'selected option is different from "other"',
      function () {
        instance.attr('assigneesListDisable', false);
        instance.attr('default_people.assignees', 'Object Admins');

        instance.defaultAssigneesChanged(context, $element, eventObj);

        expect(instance.attr('assigneesListDisable')).toBe(true);
      }
    );

    it('clears the assigneesListDisable flag if the corresponding ' +
      'selected option is "other"',
      function () {
        instance.attr('assigneesListDisable', true);
        instance.attr('default_people.assignees', 'other');

        instance.defaultAssigneesChanged(context, $element, eventObj);

        expect(instance.attr('assigneesListDisable')).toBe(false);
      }
    );

    it('showCaptainAlert value is "true" if default assignee ' +
      'is one of changedList',
      function () {
        greenList.map(function (item) {
          instance.attr('default_people.assignees', item);
          instance.defaultAssigneesChanged(context, $element, eventObj);

          expect(instance.attr('showCaptainAlert')).toBe(true);
        });
      }
    );

    it('showCaptainAlert value is "false" if default assignee ' +
      'is NOT one of changedList',
      function () {
        redList.map(function (item) {
          instance.attr('default_people.assignees', item);
          instance.defaultAssigneesChanged(context, $element, eventObj);

          expect(instance.attr('showCaptainAlert')).toBe(false);
        });
      }
    );
  });

  describe('defaultVerifiersChanged() method', function () {
    var context;
    var $element;
    var eventObj;

    beforeEach(function () {
      context = {};
      $element = $('<div></div>');
      eventObj = $.Event();
    });

    it('sets the verifiersListDisable flag if the corresponding ' +
      'selected option is different from "other"',
      function () {
        instance.attr('verifiersListDisable', false);
        instance.attr('default_people.verifiers', 'Object Admins');

        instance.defaultVerifiersChanged(context, $element, eventObj);

        expect(instance.attr('verifiersListDisable')).toBe(true);
      }
    );

    it('clears the verifiersListDisable flag if the corresponding ' +
      'selected option is "other"',
      function () {
        instance.attr('verifiersListDisable', true);
        instance.attr('default_people.verifiers', 'other');

        instance.defaultVerifiersChanged(context, $element, eventObj);

        expect(instance.attr('verifiersListDisable')).toBe(false);
      }
    );
  });
});
