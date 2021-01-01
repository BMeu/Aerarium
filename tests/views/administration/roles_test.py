# -*- coding: utf-8 -*-

from app.userprofile import Permission
from app.userprofile import Role
from tests.views import ViewTestCase


class RolesTest(ViewTestCase):

    def test_roles_list(self):
        """
            Test the list of all roles.

            Expected result: All roles that fit on the requested page are displayed, sorted by name.
        """

        self.app.config['ITEMS_PER_PAGE'] = 2

        # Add roles, but not sorted by name.
        role_guest = self.create_role(name='Guest')
        role_user = self.create_role(name='User')
        role_admin = self.create_role(Permission.EditRole, name='Administrator')

        roles_assorted = [
            role_guest,
            role_user,
            role_admin,
        ]

        # Ensure that they are not sorted by name on the DB.
        # noinspection PyUnresolvedReferences
        roles = Role.query.all()
        self.assertListEqual(roles_assorted, roles)

        # Add a user with permissions to view this page.
        self.create_and_login_user(role=role_admin)

        data = self.get('administration/roles')

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

    def test_role_header_get_no_role(self):
        """
            Test editing a role that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        non_existing_role = 'Guest'
        self.assertIsNone(Role.load_from_name(non_existing_role))

        self.get(f'/administration/role/{non_existing_role}', expected_status=404)

    def test_role_new_get(self):
        """
            Test showing the form to create a new role.

            Expected result: The new-role page is shown.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        data = self.get('/administration/role/new')

        self.assertIn('Add a New Role', data)
        self.assertNotIn('The new role has been created.', data)

    def test_role_new_post_invalid_name(self):
        """
            Test creating a new role with an invalid name.

            Expected result: The new-role page is shown and no role has been created.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        name = Role.invalid_names[0]
        data = self.post('/administration/role/new', data=dict(
            name=name
        ))

        self.assertIn('Add a New Role', data)
        self.assertNotIn('The new role has been created.', data)
        self.assertIsNone(Role.load_from_name(name))

    def test_role_new_post_success(self):
        """
            Test creating a new role.

            Expected result: The list of roles is shown and the new role has been created.
        """

        role = self.create_role(Permission.EditRole, name='Administrator')
        self.create_and_login_user(role=role)

        name = 'Guest'
        permissions = Permission.EditRole | Permission.EditGlobalSettings
        data = self.post('/administration/role/new', data=dict(
            name=name,
            editrole=True,
            editglobalsettings=True
        ))

        self.assertIn('Roles', data)
        self.assertNotIn('Add a New Role', data)
        self.assertIn('The new role has been created.', data)

        role = Role.load_from_name(name)
        self.assertIsNotNone(role)
        self.assertEqual(permissions, role.permissions)

    def test_role_header_get_existing_role(self):
        """
            Test showing the edit form for an existing role.

            Expected result: The edit page is shown.
        """

        role = self.create_role(Permission.EditRole, name='Administrator')
        self.create_and_login_user(role=role)

        data = self.get(f'/administration/role/{role.name}')

        self.assertIn(f'Edit Role “{role.name}”', data)
        self.assertIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)

    def test_role_header_post_header_data_existing_name(self):
        """
            Test editing a role by setting an existing name.

            Expected result: The edit page is shown, the role is not updated.
        """

        existing_role = self.create_role(name='Guest')

        name = 'Administrator'
        role = self.create_role(Permission.EditRole, name=name)
        self.create_and_login_user(role=role)

        role_id = role.id

        data = self.post(f'/administration/role/{role.name}', data=dict(
            name=existing_role.name
        ))

        role = Role.load_from_id(role_id)

        self.assertIn(f'Edit Role “{name}”', data)
        self.assertNotIn('The role has been updated.', data)
        self.assertEqual(name, role.name)
        self.assertIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)

    def test_role_header_post_header_data_new_name(self):
        """
            Test editing a role by setting a new name.

            Expected result: The edit page is shown, the role is updated.
        """

        name = 'Administrator'
        role = self.create_role(Permission.EditRole, name=name)

        self.create_and_login_user(role=role)

        new_name = 'Guest'
        data = self.post(f'/administration/role/{name}', data=dict(
            name=new_name
        ))

        role = Role.load_from_id(role.id)

        self.assertIn(f'Edit Role “{new_name}”', data)
        self.assertIn('The role has been updated.', data)
        self.assertEqual(new_name, role.name)
        self.assertIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)

    def test_role_permissions_get_no_role(self):
        """
            Test editing the permissions of a role that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditRole, name='Administrator')
        self.create_and_login_user(role=role)

        non_existing_role = 'Guest'
        self.assertIsNone(Role.load_from_name(non_existing_role))

        self.get(f'/administration/role/{non_existing_role}/permissions', expected_status=404)

    def test_role_permissions_get(self):
        """
            Test accessing the permissions page of a role.

            Expected result: The permissions are listed.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        data = self.get(f'/administration/role/{role.name}/permissions')

        self.assertIn('<h1>Edit Role “', data)
        self.assertIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Edit the role\'s header data', data)

    def test_role_permissions_post(self):
        """
            Test updating the permissions of a role.

            Expected result: The new permissions are set on the role.
        """

        other_role = self.create_role(Permission.EditRole, name='Administrator')
        role = self.create_role(Permission.EditRole, name='Moderator')
        self.create_and_login_user(role=other_role)

        new_permissions = Permission.EditRole | Permission.EditGlobalSettings
        data = self.post(f'/administration/role/{role.name}/permissions', data=dict(
            editglobalsettings=True,
            editrole=True,
            edituser=None,
        ))

        role = Role.load_from_name(role.name)
        self.assertEqual(new_permissions, role.permissions)
        self.assertIn('<h1>Edit Role “', data)
        self.assertIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        # The apostrophe is escaped...
        self.assertIn('The role&#39;s permissions have been updated.', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Edit the role\'s header data', data)

    def test_role_permissions_post_only_role_to_edit_roles(self):
        """
            Test updating the permissions of a role that is the only role allowed to edit roles. Unset the permission
            to edit roles.

            Expected result: The new permissions are set on the role, but the role keeps the permission to edit roles.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        self.assertTrue(role.is_only_role_allowed_to_edit_roles())

        new_permissions = Permission.EditRole | Permission.EditGlobalSettings
        data = self.post(f'/administration/role/{role.name}/permissions', data=dict(
            editglobalsettings=True,
            editrole=False,
            edituser=None,
        ))

        role = Role.load_from_name(role.name)
        self.assertEqual(new_permissions, role.permissions)
        self.assertIn('<h1>Edit Role “', data)
        self.assertIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        # The apostrophe is escaped...
        self.assertIn('The role&#39;s permissions have been updated.', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Edit the role\'s header data', data)

    def test_role_users_get_no_role(self):
        """
            Test listing the users of a role that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditRole, name='Administrator')
        self.create_and_login_user(role=role)

        non_existing_role = 'Guest'
        self.assertIsNone(Role.load_from_name(non_existing_role))

        self.get(f'/administration/role/{non_existing_role}/users', expected_status=404)

    def test_role_users_get(self):
        """
            Test accessing the user page of a role.

            Expected result: The users are listed.
        """

        name = 'Jane Doe'
        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(name=name, role=role)

        data = self.get(f'/administration/role/{role.name}/users')

        self.assertIn('<h1>Edit Role “', data)
        self.assertIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        self.assertIn(name, data)

    def test_role_delete_get_no_role(self):
        """
            Test deleting a role that does not exist.

            Expected result: An error 404 is returned.
        """

        role = self.create_role(Permission.EditRole, name='Administrator')
        self.create_and_login_user(role=role)

        non_existing_role = 'Guest'
        self.assertIsNone(Role.load_from_name(non_existing_role))

        self.get(f'/administration/role/{non_existing_role}/delete', expected_status=404)

    def test_role_delete_get_only_allowed_to_edit_roles(self):
        """
            Test accessing the delete page if the role is the only one allowed to edit roles.

            Expected result: The role delete form is not shown.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        role_id = role.id

        data = self.get(f'/administration/role/{role.name}/delete')
        role = Role.load_from_id(role_id)

        self.assertIsNotNone(role)
        self.assertIsNotNone(role.id)
        self.assertIn('<h1>Edit Role “', data)
        self.assertIn('This role cannot be deleted because it is the only one that can edit roles.', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn('The role has been deleted.', data)

    def test_role_delete_get(self):
        """
            Test accessing the delete page.

            Expected result: The role delete form.
        """

        other_role = self.create_role(Permission.EditRole, name='Administrator')
        role = self.create_role(name='Guest')
        self.create_and_login_user(role=other_role)

        role_id = role.id

        self.assertListEqual([], role.users.all())

        data = self.get(f'/administration/role/{role.name}/delete')
        role = Role.load_from_id(role_id)

        self.assertIsNotNone(role)
        self.assertIsNotNone(other_role.id)
        self.assertIn('<h1>Edit Role “', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        self.assertIn(f'Permanently delete this role', data)
        self.assertNotIn('The role has been deleted.', data)

    def test_role_delete_post_no_users(self):
        """
            Test deleting a role that has no users.

            Expected result: The role is deleted.
        """

        other_role = self.create_role(Permission.EditRole, name='Administrator')
        role = self.create_role(name='Guest')
        self.create_and_login_user(role=other_role)

        role_id = role.id

        self.assertListEqual([], role.users.all())

        data = self.post(f'/administration/role/{role.name}/delete', data=dict(
            new_role=0
        ))
        role = Role.load_from_id(role_id)

        self.assertIsNone(role)
        self.assertIsNotNone(other_role.id)
        self.assertNotIn('<h1>Edit Role “', data)
        self.assertIn('The role has been deleted.', data)

    def test_role_delete_post_only_allowed_to_edit_roles(self):
        """
            Test accessing the delete page if the role is the only one allowed to edit roles.

            Expected result: The role delete form is not shown.
        """

        role = self.create_role(Permission.EditRole)
        self.create_and_login_user(role=role)

        role_id = role.id

        data = self.post(f'/administration/role/{role.name}/delete', data=dict(
            new_role=0,
        ))
        role = Role.load_from_id(role_id)

        self.assertIsNotNone(role)
        self.assertIsNotNone(role.id)
        self.assertIn('<h1>Edit Role “', data)
        self.assertIn('This role cannot be deleted because it is the only one that can edit roles.', data)
        self.assertNotIn(f'View the users who have this role assigned to them', data)
        self.assertNotIn(f'Edit the role\'s header data', data)
        self.assertNotIn(f'Define the permissions which the users to whom this role is assigned will have.', data)
        self.assertNotIn(f'Permanently delete this role', data)
        self.assertNotIn('The role has been deleted.', data)

    def test_role_delete_post_has_users(self):
        """
            Test deleting a role that has users.

            Expected result: The role is deleted.
        """

        other_role = self.create_role(Permission.EditRole, name='Administrator')
        role = self.create_role(name='Guest')

        self.create_and_login_user(role=other_role)

        # Add a user for the role to delete.
        other_user = self.create_user(email='john@doe.com', name='John Doe', password='ABC123!', role=role)

        role_id = role.id

        self.assertListEqual([other_user], role.users.all())

        data = self.post(f'/administration/role/{role.name}/delete', data=dict(
            new_role=other_role.id
        ))
        role = Role.load_from_id(role_id)

        self.assertIsNone(role)
        self.assertIsNotNone(other_role.id)
        self.assertNotIn('<h1>Edit Role “', data)
        self.assertIn('The role has been deleted.', data)
        # noinspection PyUnresolvedReferences
        self.assertEqual(other_role, other_user.role)
