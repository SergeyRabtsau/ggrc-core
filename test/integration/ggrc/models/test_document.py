# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Integration tests for Document"""

from ggrc.models import all_models
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc import generator
from integration.ggrc.models import factories


class TestDocument(TestCase):
  """Document test cases"""
  # pylint: disable=invalid-name

  def setUp(self):
    super(TestDocument, self).setUp()
    self.api = Api()
    self.gen = generator.ObjectGenerator()

  def test_update_title(self):
    """Test update document title."""
    create_title = "test_title"
    update_title = "update_test_title"
    document = factories.DocumentFactory(title=create_title)
    response = self.api.put(document, {"title": update_title})
    self.assert200(response)
    self.assertEqual(all_models.Document.query.get(document.id).title,
                     update_title)

  def create_document_by_type(self, doc_type):
    """Create docuemtn with sent type."""
    data = {
        "title": "test_title",
        "link": "test_link",
    }
    if doc_type is not None:
        data["document_type"] = doc_type
    doc_type = doc_type or all_models.Document.URL
    resp, doc = self.gen.generate_object(
        all_models.Document,
        data
    )
    self.assertTrue(
        all_models.Document.query.filter(
            all_models.Document.id == resp.json["document"]['id'],
            all_models.Document.document_type == doc_type,
        ).all()
    )
    return (resp, doc)

  def test_create_url(self):
    """Test create url."""
    self.create_document_by_type(all_models.Document.URL)

  def test_create_url_default(self):
    """Test create url(default)."""
    self.create_document_by_type(None)

  def test_create_evidence(self):
    """Test create evidence."""
    self.create_document_by_type(all_models.Document.ATTACHMENT)

  def test_create_invalid_type(self):
    """Test validation document_type."""
    data = {
        "document_type": 3,
        "title": "test_title",
        "link": "test_link",
        "owners": [self.gen.create_stub(all_models.Person.query.first())],
    }
    obj_name = all_models.Document._inflector.table_singular
    obj = all_models.Document()
    obj_dict = self.gen.obj_to_dict(obj, obj_name)
    obj_dict[obj_name].update(data)
    resp = self.api.post(all_models.Document, obj_dict)
    self.assert400(resp)
    self.assertEqual('"Invalid value for attribute document_type. '
                     'Expected options are `URL`, `EVIDENCE`, `REFERENCE_URL`"',
                     resp.data)
