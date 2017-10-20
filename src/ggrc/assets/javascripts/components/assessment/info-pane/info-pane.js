/*
 Copyright (C) 2017 Google Inc., authors, and contributors
 Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
 */

import '../controls-toolbar/controls-toolbar';
import '../assessment-local-ca';
import '../../custom-attributes/custom-attributes';
import '../../custom-attributes/custom-attributes-field';
import '../../custom-attributes/custom-attributes-status';
import '../mapped-objects/mapped-related-information';
import '../mapped-objects/mapped-comments';
import '../mapped-objects/mapped-controls';
import '../../inline/inline-form-control';
import './inline-item';
import './create-url';
import '../../object-change-state/object-change-state';
import {
  getCustomAttributes,
  CUSTOM_ATTRIBUTE_TYPE,
  convertToFormViewField,
  convertValuesToFormFields,
  applyChangesToCustomAttributeValue,
} from '../../../plugins/utils/ca-utils';

(function (can, GGRC, CMS) {
  'use strict';
  var tpl = can.view(GGRC.mustache_path +
    '/components/assessment/info-pane/info-pane.mustache');

  /**
   * Assessment Specific Info Pane View Component
   */
  GGRC.Components('assessmentInfoPane', {
    tag: 'assessment-info-pane',
    template: tpl,
    viewModel: {
      documentTypes: {
        evidences: CMS.Models.Document.EVIDENCE,
        urls: CMS.Models.Document.URL,
        referenceUrls: CMS.Models.Document.REFERENCE_URL,
      },
      define: {
        verifiers: {
          get: function () {
            let acl = this.attr('instance.access_control_list');
            let verifierRoleId = this.attr('_verifierRoleId');
            let verifiers;

            if (!verifierRoleId) {
              return [];
            }

            verifiers = acl
              .filter((item) => item.ac_role_id == verifierRoleId)
              .map((item) => item.person);

            return verifiers;
          },
        },
        isSaving: {
          type: 'boolean',
          value: false,
        },
        isLoading: {
          type: 'boolean',
          value: false,
        },
        mappedSnapshots: {
          Value: can.List,
        },
        assessmentTypeNameSingular: {
          get: function () {
            var type = this.attr('instance.assessment_type');
            return CMS.Models[type].title_singular;
          },
        },
        assessmentTypeNamePlural: {
          get: function () {
            var type = this.attr('instance.assessment_type');
            return CMS.Models[type].title_plural;
          },
        },
        assessmentTypeObjects: {
          get: function () {
            var self = this;
            return this.attr('mappedSnapshots')
              .filter(function (item) {
                return item.child_type === self
                  .attr('instance.assessment_type');
              });
          },
        },
        relatedInformation: {
          get: function () {
            var self = this;
            return this.attr('mappedSnapshots')
              .filter(function (item) {
                return item.child_type !== self
                  .attr('instance.assessment_type');
              });
          },
        },
        comments: {
          Value: can.List,
        },
        urls: {
          Value: can.List,
        },
        referenceUrls: {
          Value: can.List,
        },
        evidences: {
          Value: can.List,
        },
        editMode: {
          type: 'boolean',
          get: function () {
            return this.attr('instance.status') !== 'Completed' &&
              this.attr('instance.status') !== 'In Review' &&
              !this.attr('instance.archived');
          },
          set: function () {
            this.onStateChange({state: 'In Progress', undo: false});
          },
        },
        isEditDenied: {
          get: function () {
            return !Permission
              .is_allowed_for('update', this.attr('instance')) ||
              this.attr('instance.archived');
          },
        },
        instance: {},
        isInfoPaneSaving: {
          get: function () {
            if (this.attr('isUpdatingRelatedItems')) {
              return false;
            }

            return this.attr('isUpdatingEvidences') ||
              this.attr('isUpdatingUrls') ||
              this.attr('isUpdatingComments') ||
              this.attr('isUpdatingReferenceUrls') ||
              this.attr('isAssessmentSaving');
          },
        },
      },
      modal: {
        open: false,
      },
      _verifierRoleId: undefined,
      isUpdatingRelatedItems: false,
      isAssessmentSaving: false,
      onStateChangeDfd: {},
      formState: {},
      noItemsText: '',
      initialState: 'Not Started',
      assessmentMainRoles: ['Creator', 'Assessor', 'Verifier'],
      setUrlEditMode: function (value, type) {
        this.attr(type + 'EditMode', value);
      },
      setInProgressState: function () {
        this.onStateChange({state: 'In Progress', undo: false});
      },
      getQuery: function (type, sortObj, additionalFilter) {
        var relevantFilters = [{
          type: this.attr('instance.type'),
          id: this.attr('instance.id'),
          operation: 'relevant',
        }];
        return GGRC.Utils.QueryAPI
          .buildParam(type,
            sortObj || {},
            relevantFilters,
            [],
            additionalFilter || []);
      },
      getCommentQuery: function () {
        return this.getQuery('Comment',
          {sortBy: 'created_at', sortDirection: 'desc'});
      },
      getSnapshotQuery: function () {
        return this.getQuery('Snapshot');
      },
      getDocumentQuery: function (documentType) {
        var query = this.getQuery(
          'Document',
          {sortBy: 'created_at', sortDirection: 'desc'},
          this.getDocumentAdditionFilter(documentType));
        return query;
      },
      requestQuery: function (query, type) {
        var dfd = can.Deferred();
        type = type || '';
        this.attr('isUpdating' + can.capitalize(type), true);
        GGRC.Utils.QueryAPI
          .batchRequests(query)
          .done(function (response) {
            var type = Object.keys(response)[0];
            var values = response[type].values;
            dfd.resolve(values);
          })
          .fail(function () {
            dfd.resolve([]);
          })
          .always(function () {
            this.attr('isUpdating' + can.capitalize(type), false);

            if (this.attr('isUpdatingRelatedItems')) {
              this.attr('isUpdatingRelatedItems', false);
            }
          }.bind(this));
        return dfd;
      },
      loadSnapshots: function () {
        var query = this.getSnapshotQuery();
        return this.requestQuery(query);
      },
      loadComments: function () {
        var query = this.getCommentQuery();
        return this.requestQuery(query, 'comments');
      },
      loadEvidences: function () {
        var query = this.getDocumentQuery(
          this.attr('documentTypes.evidences'));
        return this.requestQuery(query, 'evidences');
      },
      loadUrls: function () {
        var query = this.getDocumentQuery(
          this.attr('documentTypes.urls'));
        return this.requestQuery(query, 'urls');
      },
      loadReferenceUrls: function () {
        var query = this.getDocumentQuery(
          this.attr('documentTypes.referenceUrls'));
        return this.requestQuery(query, 'referenceUrls');
      },
      updateItems: function () {
        can.makeArray(arguments).forEach(function (type) {
          this.attr(type).replace(this['load' + can.capitalize(type)]());
        }.bind(this));
      },
      afterCreate: function (event, type) {
        var createdItems = event.items;
        var success = event.success;
        var items = this.attr(type);
        var resultList = items
          .map(function (item) {
            createdItems.forEach(function (newItem) {
              if (item._stamp && item._stamp === newItem._stamp) {
                if (!success) {
                  newItem.attr('isNotSaved', true);
                }
                newItem.removeAttr('_stamp');
                newItem.removeAttr('isDraft');
                item = newItem;
              }
            });
            return item;
          })
          .filter(function (item) {
            return !item.attr('isNotSaved');
          });
        this.attr('isUpdating' + can.capitalize(type), false);

        items.replace(resultList);
      },
      addItems: function (event, type) {
        var items = event.items;
        this.attr('isUpdating' + can.capitalize(type), true);
        return this.attr(type).unshift.apply(this.attr(type),
          can.makeArray(items));
      },
      getDocumentAdditionFilter: function (documentType) {
        return documentType ?
          {
            expression: {
              left: 'document_type',
              op: {name: '='},
              right: documentType,
            },
          } :
          [];
      },
      addAction: function (actionType, related) {
        var assessment = this.attr('instance');
        var path = 'actions.' + actionType;

        if (!assessment.attr('actions')) {
          assessment.attr('actions', {});
        }
        if (assessment.attr(path)) {
          assessment.attr(path).push(related);
        } else {
          assessment.attr(path, [related]);
        }
      },
      addRelatedItem: function (event, type) {
        var self = this;
        var related = {
          id: event.item.attr('id'),
          type: event.item.attr('type'),
        };

        // dispatching event on instance to pass to the auto-save-form
        this.attr('instance').dispatch({
          type: 'afterCommentCreated',
        });

        this.attr('deferredSave').push(function () {
          self.addAction('add_related', related);
        })
        .done(function () {
          self.afterCreate({
            items: [event.item],
            success: true,
          }, type);
        })
        .fail(function () {
          self.afterCreate({
            items: [event.item],
            success: false,
          }, type);
        })
        .always(function (assessment) {
          assessment.removeAttr('actions');
        });
      },
      removeRelatedItem: function (item, type) {
        var self = this;
        var related = {
          id: item.attr('id'),
          type: item.attr('type'),
        };
        var items = self.attr(type);
        var index = items.indexOf(item);
        this.attr('isUpdating' + can.capitalize(type), true);
        items.splice(index, 1);

        this.attr('deferredSave').push(function () {
          self.addAction('remove_related', related);
        })
        .fail(function () {
          GGRC.Errors.notifier('error', 'Unable to remove URL.');
          items.splice(index, 0, item);
        })
        .always(function (assessment) {
          assessment.removeAttr('actions');
          self.attr('isUpdating' + can.capitalize(type), false);
        });
      },
      updateRelatedItems: function () {
        this.attr('isUpdatingRelatedItems', true);

        this.attr('mappedSnapshots')
          .replace(this.loadSnapshots());
        this.attr('comments')
          .replace(this.loadComments());
        this.attr('evidences')
          .replace(this.loadEvidences());
        this.attr('urls')
          .replace(this.loadUrls());
        this.attr('referenceUrls')
          .replace(this.loadReferenceUrls());
      },
      initializeFormFields: function () {
        var cavs =
          getCustomAttributes(
            this.attr('instance'),
            CUSTOM_ATTRIBUTE_TYPE.LOCAL
          );
        this.attr('formFields',
          convertValuesToFormFields(cavs)
        );
      },
      initGlobalAttributes: function () {
        var cavs =
          getCustomAttributes(
            this.attr('instance'),
            CUSTOM_ATTRIBUTE_TYPE.GLOBAL
          );
        this.attr('globalAttributes',
          cavs.map(function (cav) {
            return convertToFormViewField(cav);
          })
        );
      },
      initializeDeferredSave: function () {
        this.attr('deferredSave', new GGRC.Utils.DeferredTransaction(
          function (resolve, reject) {
            this.attr('instance').save().done(resolve).fail(reject);
          }.bind(this), 1000, true));
      },
      onStateChange: function (event) {
        var isUndo = event.undo;
        var newStatus = event.state;
        var instance = this.attr('instance');
        var self = this;
        var previousStatus = instance.attr('previousStatus') || 'In Progress';
        this.attr('onStateChangeDfd', can.Deferred());

        if (isUndo) {
          instance.attr('previousStatus', undefined);
        } else {
          instance.attr('previousStatus', instance.attr('status'));
        }
        instance.attr('isPending', true);

        this.attr('formState.formSavedDeferred')
          .then(function () {
            instance.refresh().then(function () {
              instance.attr('status', isUndo ? previousStatus : newStatus);

              if (instance.attr('status') === 'In Review' && !isUndo) {
                $(document.body).trigger('ajax:flash',
                  {hint: 'The assessment is complete. ' +
                  'The verifier may revert it if further input is needed.'});
              }

              return instance.save()
              .then(function () {
                instance.attr('isPending', false);
                self.initializeFormFields();
                self.attr('onStateChangeDfd').resolve();
              });
            });
          });
      },
      saveGlobalAttributes: function (event) {
        var globalAttributes = event.globalAttributes;
        var caValues = this.attr('instance.custom_attribute_values');
        applyChangesToCustomAttributeValue(caValues, globalAttributes);

        return this.attr('instance').save();
      },
      showRequiredInfoModal: function (e, field) {
        var scope = field || e.field;
        var errors = scope.attr('errorsMap');
        var errorsList = can.Map.keys(errors)
          .map(function (error) {
            return errors[error] ? error : null;
          })
          .filter(function (errorCode) {
            return !!errorCode;
          });
        var data = {
          options: scope.attr('options'),
          contextScope: scope,
          fields: errorsList,
          value: scope.attr('value'),
          title: scope.attr('title'),
          type: scope.attr('type'),
        };
        var title = 'Required ' +
          data.fields.map(function (field) {
            return can.capitalize(field);
          }).join(' and ');

        can.batch.start();
        this.attr('modal', {
          content: data,
          modalTitle: title,
          state: {},
        });
        can.batch.stop();
        this.attr('modal.state.open', true);
      },
      setVerifierRoleId: function () {
        let verifierRoleIds = GGRC.access_control_roles
          .filter((item) => item.object_type === 'Assessment' &&
            item.name === 'Verifier')
          .map((item) => item.id);

        let verifierRoleId = _.head(verifierRoleIds);
        this.attr('_verifierRoleId', verifierRoleId);
      },
    },
    init: function () {
      this.viewModel.initializeFormFields();
      this.viewModel.initGlobalAttributes();
      this.viewModel.updateRelatedItems();
      this.viewModel.initializeDeferredSave();

      this.viewModel.setVerifierRoleId();
    },
    events: {
      '{viewModel.instance} refreshMapping': function () {
        this.viewModel.attr('mappedSnapshots')
          .replace(this.viewModel.loadSnapshots());
      },
      '{viewModel.instance} modelBeforeSave': function () {
        this.viewModel.attr('isAssessmentSaving', true);
      },
      '{viewModel.instance} modelAfterSave': function () {
        this.viewModel.attr('isAssessmentSaving', false);
      },
      '{viewModel} instance': function () {
        this.viewModel.initializeFormFields();
        this.viewModel.initGlobalAttributes();
        this.viewModel.updateRelatedItems();
      },
      '{viewModel.instance} resolvePendingBindings': function () {
        this.viewModel.updateItems('referenceUrls');
      },
    },
    helpers: {
      extraClass: function (type) {
        switch (type()) {
          case 'checkbox':
            return 'inline-reverse';
          default:
            return '';
        }
      },
    },
  });
})(window.can, window.GGRC, window.CMS);
