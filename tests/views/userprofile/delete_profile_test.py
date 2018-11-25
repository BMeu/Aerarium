#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
from unittest.mock import patch

from app import create_app
from app import db
from app import mail
from app.configuration import TestConfiguration
from app.userprofile import User
from app.userprofile.tokens import DeleteAccountToken
from app.views.userprofile.forms import DeleteUserProfileForm


class DeleteProfileTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    @staticmethod
    def validate_on_submit():
        """
            A mock method for validating forms that will always fail.

            :return: `False`
        """
        return False

    # region Request

    def test_delete_profile_request_success(self):
        """
            Test requesting the deletion of the user's account.

            Expected result: An email with a link to delete the account is sent.
        """
        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        with mail.record_messages() as outgoing:
            response = self.client.post('/delete-profile', follow_redirects=True, data=dict())
            data = response.get_data(as_text=True)

            self.assertEqual(1, len(outgoing))
            self.assertIn('Delete Your User Profile', outgoing[0].subject)

            self.assertIn('An email has been sent to your email address.', data)
            self.assertIn('to delete your user profile.', data)
            self.assertIn('<h1>User Profile</h1>', data)

    @patch.object(DeleteUserProfileForm, 'validate_on_submit', validate_on_submit)
    def test_delete_profile_request_failure(self):
        """
            Test requesting the deletion of the user's account with an invalid form.
            Expected result: No email is sent.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        with mail.record_messages() as outgoing:
            response = self.client.post('/delete-profile', follow_redirects=True, data=dict())
            data = response.get_data(as_text=True)

            self.assertEqual(0, len(outgoing))

            self.assertNotIn('An email has been sent to your email address.', data)
            self.assertNotIn('to delete your user profile.', data)
            self.assertIn('<h1>User Profile</h1>', data)

    # endregion

    # region Execution

    def test_delete_profile_success(self):
        """
            Test deleting the account with a valid token.

            Expected result: The account is successfully deleted.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        token_obj = DeleteAccountToken()
        token_obj.user_id = user.id

        token = token_obj.create()
        response = self.client.get('/delete-profile/' + token, follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIsNone(User.load_from_id(user_id))
        self.assertIn('Your user profile and all data linked to it have been deleted.', data)

    def test_delete_profile_failure(self):
        """
            Test deleting the account with an invalid token.

            Expected result: The account is not deleted.
        """

        email = 'test@example.com'
        password = '123456'
        name = 'John Doe'
        user_id = 1
        user = User(email, name)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()
        self.assertEqual(user_id, user.id)

        self.client.post('/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('/delete-profile/invalid-token', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertEqual(404, response.status_code)
        self.assertIsNotNone(User.load_from_id(user_id))
        self.assertNotIn('Your user profile and all data linked to it have been deleted.', data)

    # endregion
