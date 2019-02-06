/*
 Copyright (C) 2019 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import * as QueryAPI from '../utils/query-api-utils';

describe('QueryAPI utils', function () {
  describe('batchRequests() method', function () {
    let batchRequests = QueryAPI.batchRequests;

    beforeEach(function () {
      spyOn(can, 'ajax')
        .and.returnValues(
          $.Deferred().resolve([1, 2, 3, 4]), $.Deferred().resolve([1]));
    });

    afterEach(function () {
      can.ajax.calls.reset();
    });

    it('does only one ajax call for a group of consecutive calls',
      function (done) {
        $.when(batchRequests(1),
          batchRequests(2),
          batchRequests(3),
          batchRequests(4)).then(function () {
          expect(can.ajax.calls.count()).toEqual(1);
          done();
        });
      });

    it('does several ajax calls for delays calls', function (done) {
      batchRequests(1);
      batchRequests(2);
      batchRequests(3);
      batchRequests(4);

      // Make a request with a delay
      setTimeout(function () {
        batchRequests(4).then(function () {
          expect(can.ajax.calls.count()).toEqual(2);
          done();
        });
      }, 150);
    });
  });

  describe('buildParam(objName, page, relevant, fields, filters) method',
    () => {
      let page;

      describe('when page.current and page.pageSize are defined', () => {
        beforeEach(() => {
          page = {
            current: 7,
            pageSize: 10,
          };
        });

        it('returns correct limit when buffer is not defined', () => {
          let result = QueryAPI.buildParam('SomeName', page);

          expect(result).toEqual(jasmine.objectContaining({
            limit: [60, 70],
          }));
        });

        it('adds buffer to right limit if buffer defined', () => {
          page.buffer = 1;

          let result = QueryAPI.buildParam('SomeName', page);

          expect(result).toEqual(jasmine.objectContaining({
            limit: [60, 71],
          }));
        });
      });
    });

  describe('buildCountParams() method', function () {
    let relevant = {
      type: 'Audit',
      id: '555',
      operation: 'relevant',
    };

    it('empty arguments. buildCountParams should return empty array',
      function () {
        let queries = QueryAPI.buildCountParams();
        expect(Array.isArray(queries)).toBe(true);
        expect(queries.length).toEqual(0);
      }
    );

    it('No relevant. buildCountParams should return array of queries',
      function () {
        let types = ['Assessment', 'Control'];

        let queries = QueryAPI.buildCountParams(types);
        let query = queries[0];

        expect(queries.length).toEqual(types.length);
        expect(query.object_name).toEqual(types[0]);
        expect(query.type).toEqual('count');
        expect(query.filters).toBe(undefined);
      }
    );

    it('Pass relevant. buildCountParams should return array of queries',
      function () {
        let types = ['Assessment', 'Control'];

        let queries = QueryAPI.buildCountParams(types, relevant);
        let query = queries[0];
        let expression = query.filters.expression;

        expect(queries.length).toEqual(types.length);
        expect(query.object_name).toEqual(types[0]);
        expect(query.type).toEqual('count');
        expect(expression.object_name).toEqual(relevant.type);
        expect(expression.ids[0]).toEqual(relevant.id);
        expect(expression.op.name).toEqual('relevant');
      }
    );
  });
});
