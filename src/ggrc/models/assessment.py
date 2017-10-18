# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Module for Assessment object"""
from sqlalchemy import and_
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import remote
from sqlalchemy.orm import validates
from sqlalchemy import orm

from ggrc import db
from ggrc.access_control.roleable import Roleable
from ggrc.builder import simple_property
from ggrc.models.comment import Commentable
from ggrc.models.custom_attribute_definition import CustomAttributeDefinition
from ggrc.models.mixins.audit_relationship import AuditRelationship
from ggrc.models.mixins import BusinessObject
from ggrc.models.mixins import CustomAttributable
from ggrc.models.mixins import FinishedDate
from ggrc.models.mixins import Notifiable
from ggrc.models.mixins import TestPlanned
from ggrc.models.mixins import Timeboxed
from ggrc.models.mixins import VerifiedDate
from ggrc.models.mixins import reminderable
from ggrc.models.mixins import statusable
from ggrc.models.mixins import labeled
from ggrc.models.mixins.assignable import Assignable
from ggrc.models.mixins.autostatuschangeable import AutoStatusChangeable
from ggrc.models.mixins.validate_on_complete import ValidateOnComplete
from ggrc.models.mixins.with_action import WithAction
from ggrc.models.mixins.with_similarity_score import WithSimilarityScore
from ggrc.models.deferred import deferred
from ggrc.models.object_document import PublicDocumentable
from ggrc.models.object_person import Personable
from ggrc.models import reflection
from ggrc.models.relationship import Relatable
from ggrc.models.track_object_state import HasObjectState
from ggrc.fulltext.mixin import Indexed, ReindexRule


class Assessment(Roleable, statusable.Statusable, AuditRelationship,
                 AutoStatusChangeable, Assignable, HasObjectState, TestPlanned,
                 CustomAttributable, PublicDocumentable, Commentable,
                 Personable, reminderable.Reminderable, Timeboxed, Relatable,
                 WithSimilarityScore, FinishedDate, VerifiedDate,
                 ValidateOnComplete, Notifiable, WithAction, BusinessObject,
                 labeled.Labeled, Indexed, db.Model):
  """Class representing Assessment.

  Assessment is an object representing an individual assessment performed on
  a specific object during an audit to ascertain whether or not
  certain conditions were met for that object.
  """

  __tablename__ = 'assessments'
  _title_uniqueness = False

  REWORK_NEEDED = u"Rework Needed"
  NOT_DONE_STATES = statusable.Statusable.NOT_DONE_STATES | {REWORK_NEEDED, }
  VALID_STATES = tuple(NOT_DONE_STATES | statusable.Statusable.DONE_STATES)

  ASSIGNEE_TYPES = (u"Creator", u"Assessor", u"Verifier")

  class Labels(object):  # pylint: disable=too-few-public-methods
    """Choices for label enum."""
    AUDITOR_PULLS_EVIDENCE = u'Auditor pulls evidence'
    FOLLOWUP = u'Followup'
    NEEDS_REWORK = u'Needs Rework'
    NEEDS_DISCUSSION = u'Needs Discussion'

  POSSIBLE_LABELS = [Labels.AUDITOR_PULLS_EVIDENCE,
                     Labels.FOLLOWUP,
                     Labels.NEEDS_REWORK,
                     Labels.NEEDS_DISCUSSION]

  REMINDERABLE_HANDLERS = {
      "statusToPerson": {
          "handler":
              reminderable.Reminderable.handle_state_to_person_reminder,
          "data": {
              statusable.Statusable.START_STATE: "Assessor",
              "In Progress": "Assessor"
          },
          "reminders": {"assessment_assessor_reminder", }
      }
  }

  design = deferred(db.Column(db.String, nullable=False, default=""),
                    "Assessment")
  operationally = deferred(db.Column(db.String, nullable=False, default=""),
                           "Assessment")
  audit_id = deferred(
      db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=False),
      'Assessment')
  assessment_type = deferred(
      db.Column(db.String, nullable=False, server_default="Control"),
      "Assessment")

  @declared_attr
  def object_level_definitions(cls):  # pylint: disable=no-self-argument
    """Set up a backref so that we can create an object level custom
       attribute definition without the need to do a flush to get the
       assessment id.

      This is used in the relate_ca method in hooks/assessment.py.
    """
    return db.relationship(
        'CustomAttributeDefinition',
        primaryjoin=lambda: and_(
            remote(CustomAttributeDefinition.definition_id) == cls.id,
            remote(CustomAttributeDefinition.definition_type) == "assessment"),
        foreign_keys=[
            CustomAttributeDefinition.definition_id,
            CustomAttributeDefinition.definition_type
        ],
        backref='assessment_definition',
        cascade='all, delete-orphan')

  object = {}  # we add this for the sake of client side error checking

  VALID_CONCLUSIONS = frozenset([
      "Effective",
      "Ineffective",
      "Needs improvement",
      "Not Applicable"
  ])

  # REST properties
  _api_attrs = reflection.ApiAttributes(
      'design',
      'operationally',
      'audit',
      'assessment_type',
      reflection.Attribute('archived', create=False, update=False),
      reflection.Attribute('object', create=False, update=False),
  )

  _fulltext_attrs = [
      'archived',
      'design',
      'operationally',
  ]

  @classmethod
  def indexed_query(cls):
    query = super(Assessment, cls).indexed_query()
    return query.options(
        orm.Load(cls).undefer_group(
            "Assessment_complete",
        ),
        orm.Load(cls).joinedload(
            "audit"
        ).undefer_group(
            "Audit_complete",
        ),
    )

  _tracked_attrs = {
      'description',
      'design',
      'notes',
      'operationally',
      'test_plan',
      'title',
      'start_date',
      'end_date'
  }

  _aliases = {
      "owners": None,
      "assessment_template": {
          "display_name": "Template",
          "ignore_on_update": True,
          "filter_by": "_ignore_filter",
          "type": reflection.AttributeInfo.Type.MAPPING,
      },
      "assessment_type": {
          "display_name": "Assessment Type",
          "mandatory": False,
      },
      "design": "Conclusion: Design",
      "operationally": "Conclusion: Operation",
      "archived": {
          "display_name": "Archived",
          "mandatory": False,
          "ignore_on_update": True,
          "view_only": True,
      },
      "test_plan": "Assessment Procedure",
      # Currently we decided to have 'Due Date' alias for start_date,
      # but it can be changed in future
      "start_date": "Due Date",
      "status": {
          "display_name": "State",
          "mandatory": False,
          "description": "Options are:\n{}".format('\n'.join(VALID_STATES))
      },
  }

  similarity_options = {
      "relevant_types": {
          "Objective": {"weight": 2},
          "Control": {"weight": 2},
      },
      "threshold": 1,
  }

  @simple_property
  def archived(self):
    return self.audit.archived if self.audit else False

  def validate_conclusion(self, value):
    return value if value in self.VALID_CONCLUSIONS else ""

  @validates("status")
  def validate_status(self, key, value):
    value = super(Assessment, self).validate_status(key, value)
    # pylint: disable=unused-argument
    if self.status == value:
      return value
    if self.status == self.REWORK_NEEDED:
      valid_states = [self.DONE_STATE, self.FINAL_STATE]
      if value not in valid_states:
        raise ValueError("Assessment in `Rework Needed` "
                         "state can be only moved to: [{}]".format(
                             ",".join(valid_states)))
    return value

  @validates("operationally")
  def validate_opperationally(self, key, value):
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @validates("design")
  def validate_design(self, key, value):
    # pylint: disable=unused-argument
    return self.validate_conclusion(value)

  @validates("assessment_type")
  def validate_assessment_type(self, key, value):
    """Validate assessment type to be the same as existing model name"""
    # pylint: disable=unused-argument
    # pylint: disable=no-self-use
    from ggrc.snapshotter.rules import Types
    if value and value not in Types.all:
      raise ValueError(
          "Assessment type '{}' is not snapshotable".format(value)
      )
    return value

  @classmethod
  def _ignore_filter(cls, _):
    return None
