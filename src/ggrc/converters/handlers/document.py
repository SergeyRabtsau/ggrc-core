# Copyright (C) 2017 Google Inc.
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

"""Handlers document entries."""

from logging import getLogger

from ggrc import models
from ggrc.converters.handlers import handlers
from ggrc.login import get_current_user_id


# pylint: disable=invalid-name
logger = getLogger(__name__)


class DocumentLinkHandler(handlers.ColumnHandler):
  """Base class for document documents handlers."""

  DOCUMENT_TYPE = None

  @staticmethod
  def _parse_line(line):
    raise NotImplemented()

  def _get_old_map(self):
    raise NotImplemented()

  def get_value(self):
    raise NotImplemented()

  def parse_item(self, has_title=False):
    """Parse document link lines.

    Returns:
      list of documents for all URLs and evidences.
    """
    documents = []
    user_id = get_current_user_id()
    for line in self.raw_value.splitlines():
      link, title = self._parse_line(line)
      if not (link and title):
        continue
      documents.append(models.Document(
          link=link,
          title=title,
          modified_by_id=user_id,
          context=self.row_converter.obj.context,
          document_type=self.DOCUMENT_TYPE,
      ))

    return documents

  def set_obj_attr(self):
    self.value = self.parse_item()

  def set_value(self):
    """This should be ignored with second class attributes."""

  def insert_object(self):
    """Update document URL values

    This function adds missing URLs and remove existing ones from Documents.
    The existing URLs with new titles just change the title.
    """
    if self.row_converter.ignore:
      return
    new_link_map = {d.link: d for d in self.value}
    old_link_map = self._get_old_map()

    for new_link, new_doc in new_link_map.iteritems():
      if new_link in old_link_map:
        old_link_map[new_link].title = new_doc.title
      else:
        models.Relationship(source=self.row_converter.obj, destination=new_doc)

    for old_link, old_doc in old_link_map.iteritems():
      if old_link in new_link_map:
        continue
      if old_doc.related_destinations:
        old_doc.related_destinations.pop()
      elif old_doc.related_sources:
        old_doc.related_sources.pop()
      else:
        logger.warning("Invalid relationship state for document URLs.")


class DocumentEvidenceHandler(DocumentLinkHandler):
  """Handler for evidence field on document imports."""

  DOCUMENT_TYPE = models.Document.ATTACHMENT

  @staticmethod
  def _parse_line(line):
    """Parse a single line and return link and title.

    Args:
      line: string containing a single line from a cell.

    Returns:
      tuple containing a link and a title.
    """
    parts = line.strip().split()
    return parts[0], parts[0] if len(parts) == 1 else " ".join(parts[1:])

  def get_value(self):
    """Generate a new line separated string for all document links.

    Returns:
      string containing all evidence URLs and titles.
    """
    return u"\n".join(u"{} {}".format(d.link, d.title) for d in
                      self.row_converter.obj.document_evidence)

  def _get_old_map(self):
    return {d.link: d for d in self.row_converter.obj.document_evidence}


class DocumentUrlHandler(DocumentLinkHandler):
  """Handler for URL field on document imports."""

  DOCUMENT_TYPE = models.Document.URL

  @staticmethod
  def _parse_line(line):
    """Parse a single line and return link and title.

    Args:
      line: string containing a single line from a cell.

    Returns:
      tuple containing a link and a title.
    """
    return [line.strip()] * 2

  def _get_old_map(self):
    return {d.link: d for d in self.row_converter.obj.document_url}

  def get_value(self):
    """Generate a new line separated string for all document links.

    Returns:
      string containing all URLs
    """
    return "\n".join(doc.link for doc in self.row_converter.obj.document_url)


class ReferenceUrlHandler(DocumentLinkHandler):
  """Handler for REFERENCE URL field on document imports."""

  DOCUMENT_TYPE = models.Document.REFERENCE_URL

  @staticmethod
  def _parse_line(line):
    """Parse a single line and return link and title.

    Args:
      line: string containing a single line from a cell.

    Returns:
      tuple containing a link and a title.
    """
    return [line.strip()] * 2

  def _get_old_map(self):
    return {d.link: d for d in self.row_converter.obj.reference_url}

  def get_value(self):
    """Generate a new line separated string for all document links.

    Returns:
      string containing all URLs
    """
    return "\n".join(doc.link for doc in self.row_converter.obj.reference_url)
