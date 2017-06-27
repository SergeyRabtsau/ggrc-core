/*!
 Copyright (C) 2017 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

describe('GGRC.Components.relatedReferenceUrls', function () {
  'use strict';

  var viewModel;
  var instance;

  beforeEach(function () {
    viewModel = GGRC.Components.getViewModel('relatedReferenceUrls');
    instance = {};
    viewModel.attr('instance', instance);
  });

  describe('createReferenceUrl() method', function () {
    var method;
    var url;

    beforeEach(function () {
      method = viewModel.createReferenceUrl.bind(viewModel);
      url = 'test.url';
    });

    it('should dispatch createReferenceUrl event', function () {
      spyOn(viewModel, 'dispatch');
      method(url);
      expect(viewModel.dispatch)
        .toHaveBeenCalledWith({
          type: 'createReferenceUrl',
          payload: url
        });
    });
  });

  describe('removeReferenceUrl() method', function () {
    var method;
    var url;

    beforeEach(function () {
      method = viewModel.removeReferenceUrl.bind(viewModel);
      url = 'test.url';
      spyOn(viewModel, 'dispatch');
    });

    it('should dispatch removeReferenceUrl event', function () {
      method(url);
      expect(viewModel.dispatch)
        .toHaveBeenCalledWith({
          type: 'removeReferenceUrl',
          payload: url
        });
    });
  });

  describe('toggleFormVisibility() method', function () {
    var method;
    var isVisible;

    beforeEach(function () {
      method = viewModel.toggleFormVisibility.bind(viewModel);
      isVisible = true;
      spyOn(viewModel, 'attr');
      spyOn(viewModel, 'moveFocusToInput');
    });

    it('should set new value for form visibility', function () {
      method(isVisible);
      expect(viewModel.attr)
        .toHaveBeenCalledWith('isFormVisible', isVisible);
    });

    it('should clear create url form input', function () {
      method(isVisible);
      expect(viewModel.attr)
        .toHaveBeenCalledWith('value', '');
    });

    it('should set focus into create url form input', function () {
      method(isVisible);
      expect(viewModel.moveFocusToInput)
        .toHaveBeenCalled();
    });
  });

  describe('submitCreateReferenceUrlForm() method', function () {
    var method;

    beforeEach(function () {
      method = viewModel.submitCreateReferenceUrlForm.bind(viewModel);
      spyOn(viewModel, 'createReferenceUrl');
      spyOn(viewModel, 'toggleFormVisibility');
    });

    describe('in case of non-empty input', function () {
      var url;

      beforeEach(function () {
        spyOn(viewModel, 'validateUserInput').and.returnValue(true);
        url = 'test.url';
      });

      it('should validate user input', function () {
        method(url);
        expect(viewModel.validateUserInput)
          .toHaveBeenCalledWith(url);
      });

      it('should create reference url', function () {
        method(url);
        expect(viewModel.createReferenceUrl)
          .toHaveBeenCalledWith(url);
      });

      it('should hide create url form', function () {
        method(url);
        expect(viewModel.toggleFormVisibility)
          .toHaveBeenCalledWith(false);
      });
    });

    describe('in case of empty input', function () {
      var url;

      beforeEach(function () {
        spyOn(viewModel, 'validateUserInput').and.returnValue(false);
        url = '   ';
        spyOn($.fn, 'trigger').and.callThrough();
      });

      it('should validate user input', function () {
        method(url);
        expect(viewModel.validateUserInput)
          .toHaveBeenCalledWith('');
      });

      it('should show create url form', function () {
        method(url);
        expect(viewModel.toggleFormVisibility)
          .toHaveBeenCalledWith(true);
      });

      it('should show notification with error message', function () {
        method(url);
        expect($.fn.trigger).toHaveBeenCalledWith('ajax:flash',
          {error: ['Please enter a URL']});
      });
    });
  });
});
