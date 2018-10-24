/*
 Copyright (C) 2018 Google Inc.
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import QueryParser from '../../generated/ggrc_filter_query_parser';
/**
 * Util methods for work with QueryAPI.
 */

/**
 * @typedef LimitArray
 * @type {array}
 * @property {number} 0  - Lower bound is inclusive.
 * @property {number} 1  - Upper bound is exclusive.
 */

/**
 * @typedef QueryAPIRequest
 * @type {Object}
 * @property {string} object_name - The name of object
 * @property {LimitArray} limit - The boundaries of the requested values.
 * @property {object} filters - Filter properties
 */

const BATCH_TIMEOUT = 100;
let batchQueue = [];
let batchTimeout = null;

/**
 * Collect requests to Query API.
 *
 * @param {Object} params - Params for request
 * @param {Object} params.headers - Custom headers for request.
 * @param {Object} params.data - Object with parameters on Query API needed.
 * @return {Promise} Promise on Query API request.
 */
function batchRequests(params) {
  let dfd = can.Deferred();
  batchQueue.push({dfd: dfd, params: params});

  if (_.isNumber(batchTimeout)) {
    clearTimeout(batchTimeout);
  }

  batchTimeout = setTimeout(function () {
    _resolveBatch(batchQueue.splice(0, batchQueue.length));
  }, BATCH_TIMEOUT);
  return dfd;
}

/**
 * Build params for ids type request on Query API.
 *
 * @param {String} objName - Name of requested object
 * @param {Object} page - Information about page state.
 * @param {Number} page.current - Current page
 * @param {Number} page.pageSize - Page size
 * @param {Array} page.sort - Array of sorting criteria
 * @param {String} page.filter - Filter string
 * @param {Object} relevant - Information about relevant object
 * @param {Object} relevant.type - Type of relevant object
 * @param {Object} relevant.id - Id of relevant object
 * @param {Object} relevant.operation - Type of operation.
 * @param {Object|Array} additionalFilter - Additional filters to be applied
 * @return {Object} Object of QueryAPIRequest
 */
function buildRelevantIdsQuery(objName, page, relevant, additionalFilter) {
  let param = buildParam(objName, page, relevant, null, additionalFilter);
  param.type = 'ids';
  return param;
}

/**
 * Build params for request on Query API.
 *
 * @param {String} objName - Name of requested object
 * @param {Object} page - Information about page state.
 * @param {Number} page.current - Current page
 * @param {Number} page.pageSize - Page size
 * @param {Array} page.sort - Array of sorting criteria
 * @param {Object|Object[]} relevant - Information about relevant object
 * @param {Object} relevant.type - Type of relevant object
 * @param {Object} relevant.id - Id of relevant object
 * @param {Object} relevant.operation - Type of operation.
 * @param {Array} fields - Array of requested fields.
 * @param {Object|Array} filters - Filters to be applied
 * @return {Object} Object of QueryAPIRequest
 */
function buildParam(objName, page, relevant, fields, filters) {
  let first;
  let last;
  let params = {};

  if (!objName) {
    return {};
  }

  params.object_name = objName;
  params.filters = _makeFilter(filters, relevant);

  if (page.current && page.pageSize) {
    first = (page.current - 1) * page.pageSize;
    last = page.current * page.pageSize;
    params.limit = [first, last];
  }

  if (page.sort) {
    params.order_by = _
      .chain(page.sort)
      .map((el) => {
        if (el.key) {
          return {
            name: el.key,
            desc: el.direction === 'desc',
          };
        }
      })
      .compact()
      .value();

    params.order_by = params.order_by.length ? params.order_by : undefined;
  }

  if (fields) {
    params.fields = fields;
  }
  return params;
}

/**
 * Build Count Params.
 *
 * @param {Array} types - Names of requested object
 * @param {Object} relevant - Information about relevant object
 * @param {Object} filter - A filter to be applied
 * @return {Array} Array of QueryAPIRequests
 */
function buildCountParams(types, relevant, filter) {
  let params;

  if (!types || !Array.isArray(types)) {
    return [];
  }

  params = types.map(function (objName) {
    let param = {};

    if (!objName) {
      return {};
    }

    param.object_name = objName;
    param.type = 'count';

    if (relevant) {
      param.filters = _makeFilter(filter, relevant);
    }

    return param;
  });

  return params;
}

/**
 * Params for request on Query API
 * @param {Object} params - Params for request
 * @param {Object} params.headers - Custom headers for request.
 * @param {Object} params.data - Object with parameters on Query API needed.
 * @return {Promise} Promise on Query API request.
 */
function makeRequest(params) {
  let reqParams = params.data || [];
  return can.ajax({
    type: 'POST',
    headers: $.extend({
      'Content-Type': 'application/json',
    }, params.headers || {}),
    url: '/query',
    data: JSON.stringify(reqParams),
  });
}

function _makeRelevantFilter(filter) {
  let relevantFilter = QueryParser.parse('#' + filter.type + ',' +
    filter.id + '#');

  if (filter && !filter.operation) {
    filter.operation = 'relevant';
  }

  if (filter.operation &&
    filter.operation !== relevantFilter.expression.op.name) {
    relevantFilter.expression.op.name = filter.operation;
  }

  return relevantFilter;
}

function _makeFilter(filter, relevant) {
  let relevantFilters;
  let filterList = [];

  if (relevant) {
    relevant = Array.isArray(relevant) ?
      relevant :
      can.makeArray(relevant);
    relevantFilters = relevant.map(function (filter) {
      return _makeRelevantFilter(filter);
    });
    filterList = filterList.concat(relevantFilters);
  }

  if (filter) {
    filter = Array.isArray(filter) ?
      filter :
      can.makeArray(filter);
    filterList = filterList.concat(filter);
  }
  if (filterList.length) {
    return filterList.reduce(function (left, right) {
      return QueryParser.joinQueries(left, right);
    });
  }
  return {expression: {}};
}

function _resolveBatch(queue) {
  makeRequest({
    data: queue.map(function (el) {
      return el.params;
    }),
  }).then(function (result) {
    result.forEach(function (info, i) {
      let req = queue[i];

      req.dfd.resolve(info);
    });
  });
}

export {
  buildParam,
  buildRelevantIdsQuery,
  batchRequests,
  buildCountParams,
};
