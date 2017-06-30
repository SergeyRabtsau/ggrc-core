# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

""" Unit tests for the Assessment object """

from sqlalchemy.orm import attributes

from ggrc import db
from ggrc.models import Assessment
from ggrc.models import mixins
from ggrc.models import object_document
from ggrc.models import object_person
from ggrc.models import relationship
from ggrc.models import track_object_state
from ggrc.models.mixins import assignable

from unit.ggrc.models import test_mixins_base


class TestAssessmentMixins(test_mixins_base.TestMixinsBase):
  """ Tests inclusion of correct mixins and their attributes """

  def setUp(self):
    self.model = Assessment
    self.included_mixins = [
        assignable.Assignable,
        mixins.BusinessObject,
        mixins.CustomAttributable,
        db.Model,
        object_document.Documentable,
        track_object_state.HasObjectState,
        mixins.TestPlanned,
        mixins.Timeboxed,
        object_person.Personable,
        relationship.Relatable,
    ]

    self.attributes_introduced = [
        ('audit_id', attributes.InstrumentedAttribute),
        ('design', attributes.InstrumentedAttribute),
        ('operationally', attributes.InstrumentedAttribute),
        ('object', dict),
        ('status', attributes.InstrumentedAttribute),                    # Stateful       # noqa
        ('assignees', property),                                         # Assignable     # noqa
        ('custom_attribute_values', attributes.InstrumentedAttribute),   # CustomAttrib.  # noqa
        ('description', attributes.InstrumentedAttribute),               # Described      # noqa
        ('end_date', attributes.InstrumentedAttribute),                  # Timeboxed      # noqa
        ('notes', attributes.InstrumentedAttribute),                     # Noted          # noqa
        ('document_url', property),                                      # Documentable   # noqa
        ('document_evidence', property),                                 # Documentable   # noqa
        ('object_people', attributes.InstrumentedAttribute),             # Personable     # noqa
        ('os_state', attributes.InstrumentedAttribute),                  # HasObjectState # noqa
        ('reference_url', property),                                     # Documentable   # noqa
        ('related_sources', attributes.InstrumentedAttribute),           # Relatable      # noqa
        ('related_destinations', attributes.InstrumentedAttribute),      # Relatable      # noqa
        ('slug', attributes.InstrumentedAttribute),                      # Slugged        # noqa
        ('start_date', attributes.InstrumentedAttribute),                # Timeboxed      # noqa
        ('test_plan', attributes.InstrumentedAttribute),                 # TestPlanned    # noqa
        ('title', attributes.InstrumentedAttribute),                     # Titled         # noqa
    ]
