# -*- coding: utf-8 -*-

from unittest.mock import patch

from app import mail
from app.userprofile import User
from app.userprofile.tokens import DeleteAccountToken
from app.views.userprofile.forms import DeleteUserProfileForm
from tests.views import ViewTestCase


class DeleteProfileTest(ViewTestCase):

    # region Request

    def test_delete_profile_request_success(self):
        """
            Test requesting the deletion of the user's account.

            Expected result: An email with a link to delete the account is sent.
        """

        self.create_and_login_user()

        with mail.record_messages() as outgoing:
            data = self.post('/user/delete')

            self.assertEqual(1, len(outgoing))
            self.assertIn('Delete Your User Profile', outgoing[0].subject)

            self.assertIn('An email has been sent to your email address.', data)
            self.assertIn('to delete your user profile.', data)
            self.assertIn('<h1>User Profile</h1>', data)

    @patch.object(DeleteUserProfileForm, 'validate_on_submit', ViewTestCase.get_false)
    def test_delete_profile_request_failure_invalid_form(self):
        """
            Test requesting the deletion of the user's account with an invalid form.

            Expected result: No email is sent.
        """

        self.create_and_login_user()

        with mail.record_messages() as outgoing:
            data = self.post('/user/delete')

            self.assertEqual(0, len(outgoing))

            self.assertNotIn('An email has been sent to your email address.', data)
            self.assertNotIn('to delete your user profile.', data)
            self.assertIn('<h1>User Profile</h1>', data)

    def test_delete_profile_request_failure_no_email(self):
        """
            Test requesting the deletion of the user's account with an invalid form.

            Expected result: No email is sent.
        """

        user = self.create_and_login_user()

        user._email = None

        with mail.record_messages() as outgoing:
            data = self.post('/user/delete')

            self.assertEqual(0, len(outgoing))

            self.assertIn('We were not able to send you an email', data)
            self.assertIn('email address in your profile is valid.', data)
            self.assertIn('<h1>User Profile</h1>', data)

    # endregion

    # region Execution

    def test_delete_profile_success(self):
        """
            Test deleting the account with a valid token.

            Expected result: The account is successfully deleted.
        """

        user = self.create_and_login_user()
        user_id = user.id

        token_obj = DeleteAccountToken()
        token_obj.user_id = user_id

        token = token_obj.create()
        data = self.get('/user/delete/' + token)

        self.assertIsNone(User.load_from_id(user_id))
        self.assertIn('Your user profile and all data linked to it have been deleted.', data)

    def test_delete_profile_failure(self):
        """
            Test deleting the account with an invalid token.

            Expected result: The account is not deleted.
        """

        user = self.create_and_login_user()
        user_id = user.id

        data = self.get('/user/delete/invalid-token', expected_status=404)

        self.assertIsNotNone(User.load_from_id(user_id))
        self.assertNotIn('Your user profile and all data linked to it have been deleted.', data)

    # endregion
