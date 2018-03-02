/*
  Copyright (C) 2018 Google Inc.
  Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
*/

import template from './issue-tracker-enable.mustache';
import logger from './issue-tracker-log';

/* eslint-disable no-console */

const audit = GGRC.page_instance();

let isButtonActivated = false;

let vm;

const relevantToAuditFilter = {
  expression: {
    object_name: audit.type,
    op: {name: 'relevant'},
    ids: [audit.id],
  },
};
const request = async (url, body) => {
  let params = {
    method: 'POST',
    body: JSON.stringify(body),
    headers: {
      'Content-type': 'application/json',
    },
    credentials: 'include',
  };

  let response = await fetch(url, params);
  return response.json();
};
const getRelatedAssessmentsIds = async (filters = relevantToAuditFilter) => {
  let query = {
    object_name: 'Assessment',
    filters,
    type: 'ids',
  };
  let response = await request('/query', [query]);
  return response[0].Assessment.ids;
};
const updateAssessments = (assessments) => {
  let result = can.Deferred().resolve([]);

  return Array.from(assessments).reduce((dfd, assessment) => {
    return dfd.then((updated) => {
      let deferred = new can.Deferred();

      assessment.save().then((assessment) => {
        logger.add({
          id: assessment.id,
          status: 'loaded',
        });

        delete CMS.Models.Assessment.cache[assessment.id];
        delete CMS.Models.Assessment.store[assessment.id];

        deferred.resolve([...updated, assessment]);
      }, () => {
        logger.add({
          id: assessment.id,
          status: 'error',
        });

        deferred.resolve([...updated, {
          error: 'Assessment not updated',
          id: assessment.id,
        }]);
      });

      return deferred;
    });
  }, result);
};

const IssueTrackerEnabler = can.Map.extend({
  state: {
    open: false,
  },
  isStopped: false,
  slugsString: '',
  done: false,
  audit: audit,
  statesMap: {},
  statesList: [],
  slugs: [],
  checked: 0,
  ids: [],
  logs: [],
  open() {
    this.attr('state.open', true);
  },
  stop() {
    this.attr('isStopped', true);
  },
  showLog() {
    let log = logger.readLog();
    console.log('Show log, items in the log:', log.length);

    this.attr('logs').replace(log);
  },
  initIds(ids) {
    this.attr('statesList').replace([]);
    this.attr('checked', 0);
    ids.forEach((id) => {
      let state = new can.Map({
        id,
        state: 'unchecked',
      });
      this.attr('statesList').push(state);
      this.attr(`statesMap.${id}`, state);
    });

    this.attr('ids', ids);
  },
  async enableITForAll() {
    let ids = await getRelatedAssessmentsIds();

    this.initIds(ids);

    logger.reset();

    this.enableByIds(ids);
  },
  async enableForSlugs() {
    let slugString = this.attr('slugsString');
    let slugs = slugString.split(',').map((slug) => slug.trim());

    this.attr('slugs', slugs);

    let query = {
      expression: {
        left: 'slug',
        op: {name: 'IN'},
        right: slugs,
      },
    };
    let filter = GGRC.query_parser.join_queries(relevantToAuditFilter, query);

    let ids = await getRelatedAssessmentsIds(filter);

    this.initIds(ids);

    logger.reset();

    this.enableByIds(ids);
  },
  enableByIds(ids) {
    let assessmentsForUpdate = ids.splice(0, 5)
      .map((id) => CMS.Models.Assessment.findOne({id}));

    return $.when(...assessmentsForUpdate)
      .then((...assessments) => {
        let assessmentWithoutIT = assessments.filter((asmt) => {
          let isTrackerDisabled = !asmt.attr('issue_tracker')
            || !asmt.attr('issue_tracker.enabled');

          let checked = this.attr('checked');

          this.attr('checked', checked + 1);
          if (!isTrackerDisabled) {
            logger.add({
              id: asmt.id,
              status: 'skipped',
            });

            this.attr(`statesMap.${asmt.id}.state`, 'skipped');
          }

          return isTrackerDisabled;
        });

        if (!assessmentWithoutIT.length) {
          return [];
        }

        let updatingAsmts = assessmentWithoutIT.map((asmt) => {
          let it = asmt.attr('issue_tracker');
          let parentIT = audit.attr('issue_tracker');

          it.attr('issue_priority', it.attr('issue_priority')
            || parentIT.attr('issue_priority'));
          it.attr('issue_severity', it.attr('issue_severity')
            || parentIT.attr('issue_severity'));
          it.attr('component_id', it.attr('component_id')
            || parentIT.attr('component_id'));
          it.attr('hotlist_id', it.attr('hotlist_id')
            || parentIT.attr('hotlist_id'));
          it.attr('issue_type', it.attr('issue_type')
            || parentIT.attr('issue_type'));
          it.attr('title', it.attr('title') || asmt.attr('title'));
          it.attr('enabled', true);
          return asmt;
        });

        return updateAssessments(updatingAsmts);
      }, () => {
        // got an error on
        ids.forEach((id) => {
          this.attr(`statesMap.${id}.state`, 'error');
        });
      })
      .then((updateReady) => {
        updateReady.forEach((a) => {
          if (!a.error) {
            this.attr(`statesMap.${a.id}.state`, 'loaded');
          } else {
            this.attr(`statesMap.${a.id}.state`, 'error');
          }
        });
      })
      .always(() => {
        let isStopped = this.attr('isStopped');

        if (ids.length && !isStopped) {
          return this.enableByIds(ids);
        } else {
          this.attr('done', true);
        }
      });
  },
});

GGRC.enableIssueTracker = () => {
  if (audit.type !== 'Audit') {
    console.warn(`This function is applicable only in Audit scope. 
      Please open the Audit page and try again!`);
    return;
  }

  if (!audit.issue_tracker
    || audit.issue_tracker && !audit.issue_tracker.enabled) {
    console.warn('Issue tracker must be enabled for this Audit!');
    return;
  }

  if (isButtonActivated) {
    console.warn('Issue tracker script has already activated!');
    vm.open();
  } else {
    isButtonActivated = true;

    vm = new IssueTrackerEnabler();

    let renderer = can.view.mustache(template);
    let fragment = renderer(vm);

    $('section.footer').append(fragment);
  }
};
