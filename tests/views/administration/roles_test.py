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

    def test_role_edit_get_no_role(self):
        """
            Test editing a role that does not exist.

            Expected result: An error 404 is returned.
        """

        role = Role(name='Administrator')
        role.add_permission(Permission.EditRole)
        db.session.add(role)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = role
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        non_existing_role = 'Guest'
        self.assertIsNone(Role.load_from_name(non_existing_role))

        response = self.client.get(f'/administration/role/{non_existing_role}', follow_redirects=True)
        self.assertEqual(404, response.status_code)

    def test_role_edit_get_existing_role(self):
        """
            Test showing the edit form for an existing role.

            Expected result: The edit page is shown.
        """

        role_name = 'Administrator'
        role = Role(name=role_name)
        role.add_permission(Permission.EditRole)
        db.session.add(role)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = role
        db.session.add(user)
        db.session.commit()

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.get(f'/administration/role/{role_name}', follow_redirects=True)
        data = response.get_data(as_text=True)

        self.assertIn(f'Edit Role “{role_name}”', data)

    def test_role_edit_post_header_data_existing_name(self):
        """
            Test editing a role by setting an existing name.

            Expected result: The edit page is shown, the role is not updated.
        """

        role_existing_name = 'Guest'
        role_existing = Role(name=role_existing_name)
        db.session.add(role_existing)

        role_name = 'Administrator'
        role = Role(name=role_name)
        role.add_permission(Permission.EditRole)
        db.session.add(role)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = role
        db.session.add(user)
        db.session.commit()

        role_id = role.id

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post(f'/administration/role/{role_name}', follow_redirects=True, data=dict(
            header_name=role_existing_name,
            header_submit=True,
        ))
        data = response.get_data(as_text=True)
        role = Role.load_from_id(role_id)

        self.assertIn(f'Edit Role “{role_name}”', data)
        self.assertNotIn('The role has been updated.', data)
        self.assertEqual(role_name, role.name)

    def test_role_edit_post_header_data_new_name(self):
        """
            Test editing a role by setting a new name.

            Expected result: The edit page is shown, the role is updated.
        """

        role_name = 'Administrator'
        role = Role(name=role_name)
        role.add_permission(Permission.EditRole)
        db.session.add(role)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = role
        db.session.add(user)
        db.session.commit()

        role_id = role.id
        new_name = 'Guest'

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post(f'/administration/role/{role_name}', follow_redirects=True, data=dict(
            header_name=new_name,
            header_submit=True,
        ))
        data = response.get_data(as_text=True)
        role = Role.load_from_id(role_id)

        self.assertIn(f'Edit Role “{new_name}”', data)
        self.assertIn('The role has been updated.', data)
        self.assertEqual(new_name, role.name)

    def test_role_edit_post_delete_no_users(self):
        """
            Test deleting a role that has no users.

            Expected result: The role is deleted.
        """

        other_role_name = 'Administrator'
        other_role = Role(name=other_role_name)
        other_role.add_permission(Permission.EditRole)
        db.session.add(other_role)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = other_role
        db.session.add(user)

        # Add a role that will be deleted.
        role_name = 'Guest'
        role = Role(name=role_name)
        db.session.add(role)
        db.session.commit()

        role_id = role.id

        self.assertListEqual([], role.users.all())

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post(f'/administration/role/{role_name}', follow_redirects=True, data=dict(
            delete_new_role=0,
            delete_submit=True,
        ))
        data = response.get_data(as_text=True)
        role = Role.load_from_id(role_id)

        self.assertIsNone(role)
        self.assertIsNotNone(other_role.id)
        self.assertNotIn('<h1>Edit Role “', data)
        self.assertIn('The role has been deleted.', data)

    def test_role_edit_post_delete_has_users(self):
        """
            Test deleting a role that has users.

            Expected result: The role is deleted.
        """

        other_role_name = 'Administrator'
        other_role = Role(name=other_role_name)
        other_role.add_permission(Permission.EditRole)
        db.session.add(other_role)

        # Add a user with permissions to view this page.
        name = 'Jane Doe'
        email = 'test@example.com'
        password = '123456'
        user = User(email, name)
        user.set_password(password)
        user.role = other_role
        db.session.add(user)

        # Add a role that will be deleted.
        role_name = 'Guest'
        role = Role(name=role_name)
        db.session.add(role)

        # Add a user for the role to delete.
        other_user = User('mail@example.com', 'John Doe')
        other_user.role = role
        db.session.commit()

        role_id = role.id

        self.assertListEqual([other_user], role.users.all())

        self.client.post('/user/login', follow_redirects=True, data=dict(
            email=email,
            password=password
        ))

        response = self.client.post(f'/administration/role/{role_name}', follow_redirects=True, data=dict(
            delete_new_role=other_role.id,
            delete_submit=True,
        ))
        data = response.get_data(as_text=True)
        role = Role.load_from_id(role_id)

        self.assertIsNone(role)
        self.assertIsNotNone(other_role.id)
        self.assertNotIn('<h1>Edit Role “', data)
        self.assertIn('The role has been deleted.', data)
        self.assertEqual(other_role, other_user.role)
