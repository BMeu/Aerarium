#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User


class RolesTest(TestCase):

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

    def test_roles_list(self):
        """
            Test the list of all roles.

            Expected result: All roles that fit on the requested page are displayed, sorted by name.
        """
        self.app.config['ITEMS_PER_PAGE'] = 2

        # Add roles, but not sorted by name.
        role_guest = Role(name='Guest')
        db.session.add(role_guest)

        role_user = Role(name='User')
        db.session.add(role_user)

        role_admin = Role(name='Administrator')
        role_admin.permissions = Permission.EditRole
        db.session.add(role_admin)
        db.session.commit()

        roles_assorted = [
            role_guest,
            role_user,
            role_admin,
        ]

        # Ensure that they are not sorted by name on the DB.
        roles = Role.query.all()
        self.assertListEqual(roles_assorted, roles)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = role_admin
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get('administration/roles', follow_redirects=True)
        data = response.get_data(as_text=True)

        title_role_admin = f'Edit role “{role_admin.name}”'
        title_role_guest = f'Edit role “{role_guest.name}”'
        title_role_user = f'Edit role “{role_user.name}”'

        self.assertIn('Roles', data)
        self.assertIn(title_role_admin, data)
        self.assertIn(title_role_guest, data)
        self.assertNotIn(title_role_user, data)
        self.assertIn('Displaying roles 1 to 2 of 3', data)

        # Test that the order of the admin and guest role match.
        pos_of_admin = data.find(title_role_admin)
        pos_of_guest = data.find(title_role_guest)
        self.assertLess(pos_of_admin, pos_of_guest)
