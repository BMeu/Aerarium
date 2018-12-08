#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import RolePagination
from app.userprofile import User


class RoleTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # region Initialization

    def test_load_from_id_success(self):
        """
            Test the role loader function with an existing role.

            Expected result: The role with the given ID is returned.
        """
        name = 'Administrator'
        role_id = 1
        role = Role(name=name)

        db.session.add(role)
        db.session.commit()

        self.assertEqual(role_id, role.id)

        loaded_role = Role.load_from_id(role_id)
        self.assertIsNotNone(loaded_role)
        self.assertEqual(role_id, loaded_role.id)
        self.assertEqual(name, loaded_role.name)

    def test_load_from_id_failure(self):
        """
            Test the role loader function with a non-existing role.

            Expected result: No role is returned.
        """
        loaded_role = Role.load_from_id(1)
        self.assertIsNone(loaded_role)

    def test_load_from_name_success(self):
        """
            Test loading an existing role via its name.

            Expected result: The role is returned.
        """
        name = 'Administrator'
        role = Role(name=name)
        role_id = 1

        db.session.add(role)
        db.session.commit()

        self.assertEqual(role_id, role.id)

        loaded_role = Role.load_from_name(name)
        self.assertIsNotNone(loaded_role)
        self.assertEqual(role_id, loaded_role.id)
        self.assertEqual(name, loaded_role.name)

    def test_load_from_name_failure(self):
        """
            Test loading a non-existing role via its name.

            Expected result: Nothing is returned.
        """
        loaded_role = Role.load_from_name('Administrator')
        self.assertIsNone(loaded_role)

    # endregion

    # region Permissions

    def test_permissions_get_none(self):
        """
            Test getting the permission enum member if there are no permissions.

            Expected result: The empty permission.
        """
        role = Role()

        self.assertIsNone(role._permissions)
        self.assertEqual(Permission(0), role.permissions)

    def test_permissions_get_less_than_zero(self):
        """
            Test getting the permission enum member if the permission integer is < 0.

            Expected result: The empty permission.
        """
        role = Role()
        role._permissions = -1

        self.assertEqual(Permission(0), role.permissions)

    def test_permissions_get_zero(self):
        """
            Test getting the permission enum member if the permission integer is 0.

            Expected result: The empty permission.
        """
        role = Role()
        db.session.add(role)
        db.session.commit()

        self.assertEqual(0, role._permissions)
        self.assertEqual(Permission(0), role.permissions)

    def test_permissions_get_power_of_two_exist(self):
        """
            Test getting the permission enum member if the permission integer is a power of two and the enum member
            exists.

            Expected result: The corresponding enum member is returned.
        """
        role = Role()

        role._permissions = Permission.EditRole.value
        self.assertEqual(Permission.EditRole, role.permissions)

        role._permissions = Permission.EditUser.value
        self.assertEqual(Permission.EditUser, role.permissions)

    def test_permissions_get_power_of_two_not_exists(self):
        """
            Test getting the permission enum member if the permission integer is a power of two and the enum member
            does not exist.

            Expected result: The corresponding enum member is returned.
        """
        role = Role()

        # Choose a value that is high enough to be very unlikely to exist as a permission.
        role._permissions = 2 ** 64
        with self.assertRaises(ValueError):
            permission = role.permissions
            self.assertIsNone(permission)

    def test_permissions_get_combination_exists(self):
        """
            Test getting the permission enum member if the permission integer is a combination of two existing enum
            members.

            Expected result: The corresponding enum member is returned.
        """
        role = Role()

        role._permissions = (Permission.EditRole | Permission.EditUser).value
        self.assertEqual(Permission.EditRole | Permission.EditUser, role.permissions)

    def test_permissions_get_combination_not_exists(self):
        """
            Test getting the permission enum member if the permission integer is not a power of two and the enum member
            does not exist.

            Expected result: The corresponding enum member is returned.
        """
        role = Role()

        # Choose a value that is high enough to be very unlikely to exist as a permission.
        role._permissions = (2 ** 64) + (2 ** 63)
        with self.assertRaises(ValueError):
            permission = role.permissions
            self.assertIsNone(permission)

    def test_permissions_set_none(self):
        """
            Test setting permissions without giving a permission.

            Expected result: The empty permission is set.
        """
        role = Role()
        role._permissions = Permission.EditRole.value
        self.assertEqual(Permission.EditRole, role.permissions)

        role.permissions = None
        self.assertEqual(Permission(0).value, role._permissions)

    def test_permissions_set_permission(self):
        """
            Test setting permissions with giving a permission.

            Expected result: The permission is set, overwriting previous values.
        """
        role = Role()
        role._permissions = Permission.EditRole.value
        self.assertEqual(Permission.EditRole, role.permissions)

        role.permissions = Permission.EditUser
        self.assertEqual(Permission.EditUser.value, role._permissions)

    def test_has_permission_no_permissions(self):
        """
            Test the has_permission() method if a role does not have any permissions.

            Expected result: `False`.
        """
        role = Role()
        db.session.add(role)
        db.session.commit()

        self.assertEqual(0, role._permissions)

        self.assertFalse(role.has_permission(Permission.EditRole))
        self.assertFalse(role.has_permission(Permission.EditUser))

    def test_has_permission_single_permission(self):
        """
            Test the has_permission() method if a role has the request permission (and only this one).

            Expected result: `True` when requesting this permission, `False` otherwise.
        """
        role = Role()

        role._permissions = Permission.EditRole.value
        self.assertTrue(role.has_permission(Permission.EditRole))
        self.assertFalse(role.has_permission(Permission.EditUser))

        # If a combination of multiple permissions is requested, the role does not have this permission.
        self.assertFalse(role.has_permission(Permission.EditRole | Permission.EditUser))

        role._permissions = Permission.EditUser.value
        self.assertFalse(role.has_permission(Permission.EditRole))
        self.assertTrue(role.has_permission(Permission.EditUser))

        # If a combination of multiple permissions is requested, the role does not have this permission.
        self.assertFalse(role.has_permission(Permission.EditRole | Permission.EditUser))

    def test_has_permissions_all_no_permissions(self):
        """
            Test the has_permissions_all() method if a role does not have any permissions.

            Expected result: `False`.
        """
        role = Role()
        db.session.add(role)
        db.session.commit()

        self.assertEqual(0, role._permissions)

        self.assertFalse(role.has_permissions_all(Permission.EditRole))
        self.assertFalse(role.has_permissions_all(Permission.EditUser))

    def test_has_permissions_all_empty_permission(self):
        """
            Test the has_permissions_all() method with the empty permission.

            Expected result: `False`.
        """
        role = Role()
        db.session.add(role)
        db.session.commit()

        self.assertEqual(0, role._permissions)
        self.assertFalse(role.has_permissions_all(Permission(0)))

        role._permissions = Permission.EditRole.value
        self.assertFalse(role.has_permissions_all(Permission(0)))

    def test_has_permissions_all_single_permission(self):
        """
            Test the has_permissions_all() method if a role has the request permission (and only this one).

            Expected result: `True` when requesting this permission, `False` otherwise.
        """
        role = Role()

        role._permissions = Permission.EditRole.value
        self.assertTrue(role.has_permissions_all(Permission.EditRole))
        self.assertFalse(role.has_permissions_all(Permission.EditUser))

        # If a combination of multiple permissions is requested, the role does not have this permission.
        self.assertFalse(role.has_permissions_all(Permission.EditRole | Permission.EditUser))

        role._permissions = Permission.EditUser.value
        self.assertFalse(role.has_permissions_all(Permission.EditRole))
        self.assertTrue(role.has_permissions_all(Permission.EditUser))

        # If a combination of multiple permissions is requested, the role does not have this permission.
        self.assertFalse(role.has_permissions_all(Permission.EditRole | Permission.EditUser))

    def test_has_permissions_all_multiple_permissions(self):
        """
            Test the has_permissions_all() method if a role has the requested permission (and others).

            Expected result: `True` when requesting the set permissions.
        """
        role = Role()

        role._permissions = (Permission.EditRole | Permission.EditUser).value
        self.assertTrue(role.has_permissions_all(Permission.EditRole))
        self.assertTrue(role.has_permissions_all(Permission.EditUser))
        self.assertTrue(role.has_permissions_all(Permission.EditRole, Permission.EditUser, Permission(0)))

    def test_has_permissions_one_of_no_permissions(self):
        """
            Test the has_permissions_one_of() method if a role does not have any permissions.

            Expected result: `False`.
        """
        role = Role()
        db.session.add(role)
        db.session.commit()

        self.assertEqual(0, role._permissions)

        self.assertFalse(role.has_permissions_one_of(Permission.EditRole))
        self.assertFalse(role.has_permissions_one_of(Permission.EditUser))

    def test_has_permissions_one_of_empty_permission(self):
        """
            Test the has_permissions_one_of() method with the empty permission.

            Expected result: `False`.
        """
        role = Role()
        db.session.add(role)
        db.session.commit()

        self.assertEqual(0, role._permissions)
        self.assertFalse(role.has_permissions_one_of(Permission(0)))

        role._permissions = Permission.EditRole.value
        self.assertFalse(role.has_permissions_one_of(Permission(0)))

    def test_has_permissions_one_of_single_permission(self):
        """
            Test the has_permissions_one_of() method if a role has the request permission (and only this one).

            Expected result: `True` when requesting this permission, `False` otherwise.
        """
        role = Role()

        role._permissions = Permission.EditRole.value
        self.assertTrue(role.has_permissions_one_of(Permission.EditRole))
        self.assertFalse(role.has_permissions_one_of(Permission.EditUser))

        # If a combination of multiple permissions is requested, the role does not have this permission.
        self.assertFalse(role.has_permissions_one_of(Permission.EditRole | Permission.EditUser))

        role._permissions = Permission.EditUser.value
        self.assertFalse(role.has_permissions_one_of(Permission.EditRole))
        self.assertTrue(role.has_permissions_one_of(Permission.EditUser))

        # If a combination of multiple permissions is requested, the role does not have this permission.
        self.assertFalse(role.has_permissions_one_of(Permission.EditRole | Permission.EditUser))

    def test_has_permissions_one_of_multiple_permissions(self):
        """
            Test the has_permissions_one_of() method if a role has the requested permission (and others).

            Expected result: `True` when requesting the set permissions.
        """
        role = Role()

        role._permissions = (Permission.EditRole | Permission.EditUser).value
        self.assertTrue(role.has_permissions_one_of(Permission.EditRole))
        self.assertTrue(role.has_permissions_one_of(Permission.EditUser))
        self.assertTrue(role.has_permissions_one_of(Permission.EditRole, Permission.EditUser, Permission(0)))

    def test_add_permission(self):
        """
            Test adding a single permission.

            Expected result: The permission is added, existing ones are kept.
        """
        role = Role()
        role.permissions = Permission.EditRole

        role.add_permission(Permission.EditGlobalSettings)
        self.assertTrue(role.has_permissions_all(Permission.EditRole, Permission.EditGlobalSettings))

    def test_add_permissions_none(self):
        """
            Test adding the value `None` as a permission.

            Expected result: An error is raised.
        """
        role = Role()
        with self.assertRaises(ValueError) as exception_cm:
            # noinspection PyTypeChecker
            role.add_permission(None)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))

    def test_add_permissions_empty(self):
        """
            Test adding the empty permission.

            Expected result: Nothing is changed.
        """
        role = Role()
        permission = Permission.EditRole
        role.permissions = permission

        role.add_permission(Permission(0))
        self.assertEqual(permission, role.permissions)

    def test_add_permissions_single_permission(self):
        """
            Test adding a permission to the permissions.

            Expected result: The new permission is added, existing ones are kept.
        """

        # No permission in the beginning.
        role = Role()
        self.assertEqual(Permission(0), role.permissions)

        # Add the first permission.
        role.add_permission(Permission.EditRole)
        self.assertEqual(Permission.EditRole, role.permissions)

        # Add another one.
        role.add_permission(Permission.EditUser)
        self.assertTrue(role.has_permissions_all(Permission.EditRole, Permission.EditUser))

    def test_add_permissions_multiple_permission(self):
        """
            Test adding multiple permissions add once to the permissions.

            Expected result: The new permissions are added, existing ones are kept.
        """

        # No permission in the beginning.
        role = Role()
        self.assertEqual(Permission(0), role.permissions)

        role.add_permissions(Permission.EditRole, Permission.EditUser)
        self.assertTrue(role.has_permissions_all(Permission.EditRole, Permission.EditUser))

    def test_add_permissions_existing_permission(self):
        """
            Test adding a permission if it already is set.

            Expected result: Nothing happens.
        """
        role = Role()
        permissions = Permission.EditRole | Permission.EditUser
        role.permissions = permissions

        role.add_permission(Permission.EditRole)
        self.assertEqual(permissions, role.permissions)

    def test_remove_permission(self):
        """
            Test removing a permission from the permissions.

            Expected result: The permission is removed, others are kept.
        """
        role = Role()
        role.add_permissions(Permission.EditGlobalSettings, Permission.EditRole, Permission.EditUser)

        role.remove_permission(Permission.EditRole)
        self.assertTrue(role.has_permissions_all(Permission.EditGlobalSettings, Permission.EditUser))
        self.assertFalse(role.has_permission(Permission.EditRole))

    def test_remove_permissions_none(self):
        """
            Test removing the value `None` from the permissions.

            Expected result: An error is raised.
        """
        role = Role()
        with self.assertRaises(ValueError) as exception_cm:
            # noinspection PyTypeChecker
            role.remove_permissions(None)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))

    def test_remove_permissions_empty(self):
        """
            Test removing the empty permission.

            Expected result: Nothing is changed.
        """
        role = Role()
        permission = Permission.EditRole
        role.permissions = permission

        role.remove_permissions(Permission(0))
        self.assertEqual(permission, role.permissions)

    def test_remove_permissions_single_permission(self):
        """
            Test removing a permission from the permissions.

            Expected result: The given permission is removed, others are kept.
        """

        # All permissions in the beginning.
        role = Role()
        role.permissions = Permission.EditRole | Permission.EditUser
        self.assertTrue(role.has_permissions_all(Permission.EditRole, Permission.EditUser))

        # Remove the first permission.
        role.remove_permissions(Permission.EditRole)
        self.assertEqual(Permission.EditUser, role.permissions)

        # Remove another one.
        role.remove_permissions(Permission.EditUser)
        self.assertEqual(Permission(0), role.permissions)

    def test_remove_permissions_multiple_permission(self):
        """
            Test removing multiple permissions add once from the permissions.

            Expected result: The given permissions are removed, existing ones are kept.
        """

        # All permissions in the beginning.
        role = Role()
        full_permissions = Permission.EditRole | Permission.EditUser
        role.permissions = full_permissions
        self.assertTrue(role.has_permissions_all(Permission.EditRole))
        self.assertTrue(role.has_permissions_all(Permission.EditUser))

        # Remove all.
        role.remove_permissions(Permission.EditRole, Permission.EditUser)
        self.assertEqual(Permission(0), role.permissions)

    def test_remove_permissions_non_existing_permission(self):
        """
            Test removing a permission if it is not set.

            Expected result: Nothing happens.
        """
        role = Role()
        permission_to_remove = Permission.EditRole
        permission = Permission.EditUser
        role.permissions = permission
        self.assertFalse(role.has_permissions_all(permission_to_remove))

        role.remove_permissions(permission_to_remove)
        self.assertEqual(permission, role.permissions)

    # endregion

    # region Delete

    def test_delete_same_role(self):
        """
            Test deleting a role if the same role is given.

            Expected result: An error is raised.
        """
        name = 'Administrator'
        role = Role(name=name)
        user = User('test@example.com', 'Jane Doe')
        user.role = role
        db.session.add(role)
        db.session.add(user)
        db.session.commit()

        with self.assertRaises(ValueError) as exception_cm:
            role.delete(role)

            loaded_role = Role.load_from_name(name)

            self.assertEqual('The new role must not be the role that will be deleted.', str(exception_cm.exception))
            self.assertIsNotNone(loaded_role)
            self.assertEqual(loaded_role, user.role)

    def test_delete_has_users_no_role(self):
        """
            Test deleting a role if there are still users and no role is given.

            Expected result: An error is raised.
        """
        name = 'Administrator'
        role = Role(name=name)
        user = User('test@example.com', 'Jane Doe')
        user.role = role
        db.session.add(role)
        db.session.add(user)
        db.session.commit()

        with self.assertRaises(ValueError) as exception_cm:
            role.delete()

            loaded_role = Role.load_from_name(name)

            self.assertIn('A new role must be given', str(exception_cm.exception))
            self.assertIsNotNone(loaded_role)
            self.assertEqual(loaded_role, user.role)

    def test_delete_no_users_no_role(self):
        """
            Test deleting a role if there are no users and no role is given.

            Expected result: The role is deleted.
        """
        name = 'Administrator'
        role = Role(name=name)
        db.session.add(role)
        db.session.commit()

        role.delete()
        loaded_role = Role.load_from_name(name)
        self.assertIsNone(loaded_role)

    def test_delete_has_users_new_role(self):
        """
            Test deleting a role if there are still users and a valid new role is given.

            Expected result: The role is deleted. The role is assigned to all users who had the old role (but not to
                             others).
        """
        # The role that will be deleted.
        name = 'Administrator'
        role = Role(name=name)
        user = User('test@example.com', 'Jane Doe')
        user.role = role
        db.session.add(role)
        db.session.add(user)

        # The new role for the user.
        new_role = Role(name='Guest')
        db.session.add(new_role)

        # Another role and user who will stay untouched.
        other_role = Role(name='User')
        other_user = User('mail@example.com', 'John Doe')
        other_user.role = other_role
        db.session.add(other_role)
        db.session.add(other_user)

        db.session.commit()

        role.delete(new_role)
        loaded_role = Role.load_from_name(name)
        self.assertIsNone(loaded_role)
        self.assertEqual(new_role, user.role)
        self.assertEqual(other_role, other_user.role)

    # endregion

    # region DB Queries

    def test_get_search_query_no_term(self):
        """
            Test getting a search query without providing a search term.

            :return: A query is returned that does not filter.
        """
        role_1 = Role(name='Administrator')
        role_2 = Role(name='Guest')
        role_3 = Role(name='User')
        role_4 = Role(name='Author')
        db.session.add(role_1)
        db.session.add(role_2)
        db.session.add(role_3)
        db.session.add(role_4)
        db.session.commit()

        result = [
            role_1,
            role_2,
            role_3,
            role_4,
        ]

        query = Role.get_search_query()
        self.assertIsNotNone(query)

        roles = query.all()
        self.assertListEqual(result, roles)

    def test_get_search_query_with_term_no_wildcards(self):
        """
            Test getting a search query providing a search term without wildcards.

            :return: A query is returned that filters exactly by the search term.
        """
        role_1 = Role(name='Administrator')
        role_2 = Role(name='Guest')
        role_3 = Role(name='User')
        role_4 = Role(name='Author')
        db.session.add(role_1)
        db.session.add(role_2)
        db.session.add(role_3)
        db.session.add(role_4)
        db.session.commit()

        # Matching term.
        query = Role.get_search_query(search_term='Administrator')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1], roles)

        # Not-matching term.
        query = Role.get_search_query(search_term='Editor')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([], roles)

        # Partially matching term, but no wildcards, thus no result.
        query = Role.get_search_query(search_term='A')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([], roles)

    def test_get_search_query_with_term_wildcards(self):
        """
            Test getting a search query providing a search term without wildcards.

            :return: A query is returned that filters by the search term allowing for partial matches.
        """
        role_1 = Role(name='Administrator')
        role_2 = Role(name='Guest')
        role_3 = Role(name='User')
        role_4 = Role(name='Author')
        role_5 = Role(name='Assistant')
        db.session.add(role_1)
        db.session.add(role_2)
        db.session.add(role_3)
        db.session.add(role_4)
        db.session.add(role_5)
        db.session.commit()

        # Matching term.
        query = Role.get_search_query(search_term='*Administrator*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1], roles)

        # Partially matching term with wildcard at the end.
        query = Role.get_search_query(search_term='A*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1, role_4, role_5], roles)

        # Partially matching term with wildcard at the front.
        query = Role.get_search_query(search_term='*r')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1, role_3, role_4], roles)

        # Partially matching term with wildcard in the middle.
        query = Role.get_search_query(search_term='A*r')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1, role_4], roles)

        # Partially matching term with wildcard at the front and end, case-insensitive.
        query = Role.get_search_query(search_term='*u*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_2, role_3, role_4], roles)

        # Wildcard term matching everything.
        query = Role.get_search_query(search_term='*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1, role_2, role_3, role_4, role_5], roles)

        # Wildcard term matching nothing.
        query = Role.get_search_query(search_term='E*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([], roles)

    def test_get_search_query_with_base_query_and_term(self):
        """
            Test getting a search query providing a base query and a search term.

            :return: A query is returned that filters exactly by the search term.
        """
        role_1 = Role(name='Administrator')
        role_2 = Role(name='Guest')
        role_3 = Role(name='User')
        role_4 = Role(name='Author')
        db.session.add(role_1)
        db.session.add(role_2)
        db.session.add(role_3)
        db.session.add(role_4)
        db.session.commit()

        base_query = Role.query.order_by(Role.name.desc())

        # Matching term.
        query = Role.get_search_query(query=base_query, search_term='A*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_4, role_1], roles)

        # Test that a different result is returned without the given base query.
        query = Role.get_search_query(search_term='A*')
        self.assertIsNotNone(query)
        roles = query.all()
        self.assertListEqual([role_1, role_4], roles)

    # endregion

    # region System

    def test_repr(self):
        """
            Test the string representation of the role.

            Expected result: The representation contains details on the role.
        """
        name = 'Administrator'
        permissions = Permission.EditRole | Permission.EditUser
        role = Role(name=name)

        self.assertEqual(f'<Role [None] "{name}" [Permission.0]>', str(role))

        role.permissions = permissions
        db.session.add(role)
        db.session.commit()

        self.assertEqual(f'<Role [1] "{name}" [{permissions}]>', str(role))

    # endregion


class RolePaginationTest(TestCase):

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

        # Add a few test models.
        role_1 = Role(name='A')
        role_2 = Role(name='B')
        role_3 = Role(name='C')
        role_4 = Role(name='D')
        role_5 = Role(name='E')
        role_6 = Role(name='F')
        role_7 = Role(name='G')
        db.session.add(role_1)
        db.session.add(role_2)
        db.session.add(role_3)
        db.session.add(role_4)
        db.session.add(role_5)
        db.session.add(role_6)
        db.session.add(role_7)
        db.session.commit()

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def test_get_info_text_search_term_multiple(self):
        """
            Test getting the info text with a search term for multiple rows on a page.

            Expected result: The search term is included, the first and last row on the page are given.
        """

        self.request_context.request.args = {'page': 1}
        search_term = 'Aerarium'
        pagination = RolePagination(Role.query)

        text = pagination.get_info_text(search_term)
        self.assertIn(f'roles {pagination.first_row} to {pagination.last_row} of {pagination.total_rows}', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_search_term_single(self):
        """
            Test getting the info text with a search term for a single row on a page.

            Expected result: The search term is included, the first row on the page is given.
        """

        self.request_context.request.args = {'page': 3}
        search_term = 'Aerarium'
        pagination = RolePagination(Role.query)

        text = pagination.get_info_text(search_term)
        self.assertIn(f'role {pagination.first_row} of {pagination.total_rows}', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_search_term_no_rows(self):
        """
            Test getting the info text with a search term for no rows on the page.

            Expected result: The search term is included, the info that no rows were found is given.
        """

        # Filter by some dummy value not related to the search term.
        self.request_context.request.args = {'page': 1}
        search_term = 'Aerarium'
        pagination = RolePagination(Role.query.filter(Role.id > 42))

        text = pagination.get_info_text(search_term)
        self.assertIn('No roles', text)
        self.assertIn(f'matching “{search_term}”', text)

    def test_get_info_text_no_search_term_multiple(self):
        """
            Test getting the info text without a search term for multiple rows on a page.

            Expected result: The search term is not included, the first and last row on the page are given.
        """

        self.request_context.request.args = {'page': 1}
        pagination = RolePagination(Role.query)

        text = pagination.get_info_text()
        self.assertIn(f'roles {pagination.first_row} to {pagination.last_row} of {pagination.total_rows}', text)
        self.assertNotIn(f'matching “', text)

    def test_get_info_text_no_search_term_single(self):
        """
            Test getting the info text without a search term for a single row on a page.

            Expected result: The search term is not included, the first row on the page is given.
        """

        self.request_context.request.args = {'page': 3}
        pagination = RolePagination(Role.query)

        text = pagination.get_info_text()
        self.assertIn(f'role {pagination.first_row} of {pagination.total_rows}', text)
        self.assertNotIn(f'matching “', text)

    def test_get_info_text_no_search_term_no_rows(self):
        """
            Test getting the info text without a search term for no rows on the page.

            Expected result: The search term is not included, the info that no rows were found is given.
        """

        # Filter the results to achieve zero rows.
        self.request_context.request.args = {'page': 1}
        pagination = RolePagination(Role.query.filter(Role.id > 42))

        text = pagination.get_info_text()
        self.assertIn('No roles', text)
        self.assertNotIn(f'matching “', text)
