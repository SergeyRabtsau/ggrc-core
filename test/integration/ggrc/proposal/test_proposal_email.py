import ddt
import mock

from ggrc.models import all_models
from integration.ggrc import TestCase
from integration.ggrc.api_helper import Api
from integration.ggrc.models import factories
from ggrc.utils import proposal as proposal_utils


@ddt.ddt
class TestProposalApi(TestCase):

  def setUp(self):
    super(TestProposalApi, self).setUp()
    self.api = Api()
    self.client.get("/login")

  @ddt.data(True, False)
  def test_presentation_proposal_notifications(self, is_admin):
    """Test presentation of proposal digest email if is_admin is {0}."""
    person = factories.PersonFactory()
    self.api.set_user(person=person)
    with mock.patch("ggrc.rbac.permissions.is_admin", return_value=is_admin):
       resp = self.client.get("/_notifications/show_proposal_digest")
    if is_admin:
      self.assert200(resp)
    else:
      self.assert403(resp)

  def test_email_sending(self):
    with factories.single_commit():
      control = factories.ControlFactory()
      person_1 = factories.PersonFactory()  # has 1 role
      person_2 = factories.PersonFactory()  # has no roles
      person_3 = factories.PersonFactory()  # has 2 roles
      factories.PersonFactory()  # not related to control at all
      role_1 = factories.AccessControlRoleFactory(object_type=control.type,
                                                  notify_about_proposal=True)
      role_2 = factories.AccessControlRoleFactory(object_type=control.type,
                                                  notify_about_proposal=True)
      role_3 = factories.AccessControlRoleFactory(object_type=control.type,
                                                  notify_about_proposal=False)
      factories.AccessControlListFactory(ac_role=role_1,
                                         object=control,
                                         person=person_1)
      factories.AccessControlListFactory(ac_role=role_1,
                                         object=control,
                                         person=person_3)
      factories.AccessControlListFactory(ac_role=role_2,
                                         object=control,
                                         person=person_3)
      factories.AccessControlListFactory(ac_role=role_3,
                                         object=control,
                                         person=person_2)
      proposal_1 = factories.ProposalFactory(
          instance=control,
          content={
              "fields": {"title": "a"},
              "access_control_list": {},
              "custom_attribute_values": {},
              "mapping_fields": {},
              "mapping_list_fields": {},
          },
          agenda="agenda 1")
      proposal_2 = factories.ProposalFactory(
          instance=control,
          content={
              "fields": {"title": "b"},
              "access_control_list": {},
              "custom_attribute_values": {},
              "mapping_fields": {},
              "mapping_list_fields": {},
          },
          agenda="agenda 2")
    self.assertIsNone(proposal_1.proposed_notified_datetime)
    self.assertIsNone(proposal_2.proposed_notified_datetime)
    with mock.patch("google.appengine.api.mail.send_mail") as mailer_mock:
      with mock.patch.object(
              all_models.Proposal.NotificationContext.DIGEST_TMPL,
              "render") as bodybuilder_mock:
        proposal_utils.send_notification()
    self.assertIsNotNone(proposal_1.proposed_notified_datetime)
    self.assertIsNotNone(proposal_2.proposed_notified_datetime)
    self.assertEqual(2, len(bodybuilder_mock.call_args_list))
    self.assertEqual(2, len(mailer_mock.call_args_list))
    # email to each required person
    self.assertListEqual(
        sorted([person_1.email, person_3.email]),
        sorted([a[1]["to"] for a in mailer_mock.call_args_list]))
    # no matter how many roles each proposal should be otified
    # only once for that person
    self.assertListEqual(
        [2] * 2,
        [len(a[1]["proposals"]) for a in bodybuilder_mock.call_args_list])
