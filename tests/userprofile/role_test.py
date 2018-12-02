#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role


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
            Test addign a single permission.

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
            role.add_permissions(None)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))

    def test_add_permissions_empty(self):
        """
            Test adding the empty permission.

            Expected result: Nothing is changed.
        """
        role = Role()
        permission = Permission.EditRole
        role.permissions = permission

        role.add_permissions(Permission(0))
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
        role.add_permissions(Permission.EditRole)
        self.assertEqual(Permission.EditRole, role.permissions)

        # Add another one.
        role.add_permissions(Permission.EditUser)
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

        role.add_permissions(Permission.EditRole)
        self.assertEqual(permissions, role.permissions)

    def test_remove_permission_none(self):
        """
            Test removing the value `None` from the permissions.

            Expected result: An error is raised.
        """
        role = Role()
        with self.assertRaises(ValueError) as exception_cm:
            # noinspection PyTypeChecker
            role.remove_permission(None)
            self.assertEqual('None is not a valid permission', str(exception_cm.exception))

    def test_remove_permission_empty(self):
        """
            Test removing the empty permission.

            Expected result: Nothing is changed.
        """
        role = Role()
        permission = Permission.EditRole
        role.permissions = permission

        role.remove_permission(Permission(0))
        self.assertEqual(permission, role.permissions)

    def test_remove_permission_single_permission(self):
        """
            Test removing a permission from the permissions.

            Expected result: The given permission is removed, others are kept.
        """

        # All permissions in the beginning.
        role = Role()
        role.permissions = Permission.EditRole | Permission.EditUser
        self.assertTrue(role.has_permissions_all(Permission.EditRole, Permission.EditUser))

        # Remove the first permission.
        role.remove_permission(Permission.EditRole)
        self.assertEqual(Permission.EditUser, role.permissions)

        # Remove another one.
        role.remove_permission(Permission.EditUser)
        self.assertEqual(Permission(0), role.permissions)

    def test_remove_permission_multiple_permission(self):
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
        role.remove_permission(full_permissions)
        self.assertEqual(Permission(0), role.permissions)

    def test_remove_permission_non_existing_permission(self):
        """
            Test removing a permission if it is not set.

            Expected result: Nothing happens.
        """
        role = Role()
        permission_to_remove = Permission.EditRole
        permission = Permission.EditUser
        role.permissions = permission
        self.assertFalse(role.has_permissions_all(permission_to_remove))

        role.remove_permission(permission_to_remove)
        self.assertEqual(permission, role.permissions)

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
