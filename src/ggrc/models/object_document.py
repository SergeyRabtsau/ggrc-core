# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

""" Module for docuumentable mixins."""

from sqlalchemy import orm, case, and_, literal
from sqlalchemy.ext.declarative import declared_attr

from ggrc import db
from ggrc.models import reflection
from ggrc.models.relationship import Relationship
from ggrc.models.document import Document
from ggrc.fulltext.attributes import MultipleSubpropertyFullTextAttr


class Documentable(object):
  """Documentable mixin."""

  _include_links = []

  _fulltext_attrs = [
      MultipleSubpropertyFullTextAttr('document_evidence', 'document_evidence',
                                      ['title', 'link']),
      MultipleSubpropertyFullTextAttr('document_url', 'document_url',
                                      ['link']),
      MultipleSubpropertyFullTextAttr('reference_url', 'reference_url',
                                      ['link']),
  ]

  @declared_attr
  def documents(cls):
    """Return documents releated for that instance."""
    document_id = case(
        [
            (
                Relationship.destination_type == "Document",
                Relationship.destination_id,
            ),
            (
                Relationship.source_type == "Document",
                Relationship.source_id,
            ),
        ],
        else_=literal(False)
    )
    documentable_id = case(
        [
            (
                Relationship.destination_type == "Document",
                Relationship.source_id
            ),
            (
                Relationship.source_type == "Document",
                Relationship.destination_id,
            ),
        ],
        else_=literal(False)
    )
    documentable_type = case(
        [
            (
                Relationship.destination_type == "Document",
                Relationship.source_type
            ),
            (
                Relationship.source_type == "Document",
                Relationship.destination_type,
            ),
        ],
    )
    return db.relationship(
        Document,
        # at first we check is documentable_id not False (it return id in fact)
        # after that we can compare values.
        # this is required for saving logic consistancy
        # case return 2 types of values BOOL(false) and INT(id) not Null
        primaryjoin=lambda: and_(documentable_id, cls.id == documentable_id),
        secondary=Relationship.__table__,
        # at first we check is document_id not False (it return id in fact)
        # after that we can compare values.
        # this is required for saving logic consistancy
        # case return 2 types of values BOOL(false) and INT(id) not Null
        secondaryjoin=lambda: and_(document_id, Document.id == document_id,
                                   documentable_type == cls.__name__),
        viewonly=True,
    )

  @property
  def document_url(self):  # pylint: disable=no-self-argument
    # pylint: disable=not-an-iterable
    return [d for d in self.documents
            if Document.URL == d.document_type]

  @property
  def document_evidence(self):  # pylint: disable=no-self-argument
    # pylint: disable=not-an-iterable
    return [d for d in self.documents
            if Document.ATTACHMENT == d.document_type]

  @property
  def reference_url(self):  # pylint: disable=no-self-argument
    # pylint: disable=not-an-iterable
    return [d for d in self.documents
            if Document.REFERENCE_URL == d.document_type]

  @classmethod
  def eager_query(cls):
    """Eager query classmethod."""
    return cls.eager_inclusions(
        super(Documentable, cls).eager_query(),
        Documentable._include_links,
    ).options(
        orm.subqueryload(
            'documents',
        ).undefer_group(
            "Document_complete",
        ),
    )

  @staticmethod
  def _log_docs(documents):
    """Returns serialization of the given docs"""
    return [d.log_json() for d in documents if d]

  def log_json(self):
    """Serialize to JSON"""
    # This query is required to refresh related documents collection after
    # they were mapped to an object. Otherwise python uses cached value,
    # which might not contain newly created documents.
    out_json = super(Documentable, self).log_json()
    out_json["document_url"] = self._log_docs(self.document_url)
    out_json["document_evidence"] = self._log_docs(self.document_evidence)
    out_json["reference_url"] = self._log_docs(self.reference_url)
    return out_json

  @classmethod
  def indexed_query(cls):
    return super(Documentable, cls).indexed_query().options(
        orm.subqueryload("documents").undefer_group("Document_complete"),
    )


PublicDocumentable = type(
    "PublicDocumentable",
    (Documentable, ),
    {
        "_aliases": {
            "document_url": {
                "display_name": "Url",
                "type": reflection.AttributeInfo.Type.SPECIAL_MAPPING,
                "description": "New line separated list of URLs.",
            },
            "document_evidence": {
                "display_name": "Evidence",
                "type": reflection.AttributeInfo.Type.SPECIAL_MAPPING,
                "description": (
                    "New line separated list of evidence links and "
                    "titles.\nExample:\n\nhttp://my.gdrive.link/file "
                    "Title of the evidence link"
                ),
            },
            "reference_url": {
                "display_name": "Reference URL",
                "type": reflection.AttributeInfo.Type.SPECIAL_MAPPING,
                "description": "New line separated list of Reference URLs.",
            },
        }
    })
