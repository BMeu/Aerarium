#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from collections import OrderedDict

from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import User
from app.views.administration.forms import BasePermissionForm
from app.views.administration.forms import create_permission_form
from app.views.administration.forms import PermissionForm
from app.views.administration.forms import RoleDeleteForm
from app.views.administration.forms import UniqueRoleName

# region Validators


class UniqueRoleNameTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
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

    def test_init_default_message(self):
        """
            Test initializing the UniqueRoleName validator with the default error message.

            Expected result: The default error message is used.
        """
        validator = UniqueRoleName()
        self.assertEqual('The role name already is in use.', validator.message)

    def test_init_custom_message(self):
        """
            Test initializing the UniqueRoleName validator with a custom error message.

            Expected result: The custom error message is used.
        """
        message = 'Another role already uses this name.'
        validator = UniqueRoleName(message=message)
        self.assertEqual(message, validator.message)

    def test_call_no_data(self):
        """
            Test the validator on an empty field.

            Expected result: No error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        form = UniqueRoleNameForm()
        validator = UniqueRoleName()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.name)
        self.assertIsNone(validation)

    def test_call_unused_name(self):
        """
            Test the validator on a field with an unused name.

            Expected result: No error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        form = UniqueRoleNameForm()
        form.name.data = 'Administrator'
        validator = UniqueRoleName()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.name)
        self.assertIsNone(validation)

    def test_call_name_of_current_role(self):
        """
            Test the validator on a field with the current role's name

            Expected result: No error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        # Create a test role.
        name = 'Administrator'
        role = Role(name=name)
        db.session.add(role)
        db.session.commit()

        form = UniqueRoleNameForm(obj=role)
        form.name.data = name
        validator = UniqueRoleName()

        # noinspection PyNoneFunctionAssignment
        validation = validator(form, form.name)
        self.assertIsNone(validation)

    def test_call_name_of_different_role(self):
        """
            Test the validator on a field with a different role's name.

            Expected result: An error is raised.
        """

        class UniqueRoleNameForm(FlaskForm):
            name = StringField('Name')

        # Create a test user.
        name = 'Administrator'
        role = Role(name=name)
        db.session.add(role)
        db.session.commit()

        message = 'Another role already uses this name.'
        form = UniqueRoleNameForm()
        form.name.data = name
        validator = UniqueRoleName()

        with self.assertRaises(ValidationError) as thrown_message:
            # noinspection PyNoneFunctionAssignment
            validation = validator(form, form.name)
            self.assertIsNone(validation)
            self.assertEqual(message, thrown_message)

# endregion

# region Forms


class BasePermissionFormTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
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

    def test_class_variables(self):
        """
            Test the default values of the class variables.

            Expected result: The values are empty.
        """
        self.assertIsNone(BasePermissionForm.permission_fields_after)
        self.assertEqual(OrderedDict(), BasePermissionForm.permission_fields)

    def test_selected_permissions_get_no_fields(self):
        """
            Test getting the tested permissions if no permission fields exist.

            Expected result: The empty permission is returned without any errors.
        """
        form = BasePermissionForm()
        self.assertEqual(Permission(0), form.permissions)

    def test_selected_permissions_get_faulty_field_dict(self):
        """
            Test getting the tested permissions if no permission fields exist, but the permission fields dict say
            otherwise..

            Expected result: The empty permission is returned without any errors.
        """
        form = BasePermissionForm()
        permission = Permission.EditGlobalSettings
        form.permission_fields = OrderedDict([(permission.name, permission)])

        self.assertEqual(Permission(0), form.permissions)

    def test_order_fields_no_fields(self):
        """
            Test ordering the permission fields without any fields in the form.

            Expected result: No errors are raised.
        """
        form = BasePermissionForm()

        form.order_fields()
        actual_fields = list(form)
        self.assertListEqual([], actual_fields)

    def test_order_fields_field_after_not_existent(self):
        """
            Test ordering the permission fields without any fields in the form, but a field is given after which the
            permission field should be inserted.

            Expected result: No errors are raised.
        """
        form = BasePermissionForm()
        form.permission_fields_after = 'name'

        form.order_fields()
        actual_fields = list(form)
        self.assertListEqual([], actual_fields)


class PermissionFormTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
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

    def test_class_variables(self):
        """
            Test that the permission fields will before all other fields.

            Expected result: The attribute to define the order is `None`.
        """
        self.assertIsNone(PermissionForm.permission_fields_after)


class RoleDeleteFormTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
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

    def test_init_no_users(self):
        """
            Test that the form is correctly initialized if the role does not have any users.

            Expected result: The new_role field is deleted.
        """
        role = Role(name='Administrator')
        db.session.add(role)
        db.session.commit()

        self.assertListEqual([], role.users.all())

        form = RoleDeleteForm(role)
        self.assertIsNone(form.new_role)

    def test_init_has_users(self):
        """
            Test that the form is correctly initialized if the role has users.

            Expected result: The new_role field exists and is initialized with all other roles.
        """
        role = Role(name='Administrator')
        user = User('test@example.com', 'Jane Doe')
        user.role = role

        other_role_1 = Role(name='Visitor')
        other_role_2 = Role(name='Guest')

        db.session.add(role)
        db.session.add(user)
        db.session.add(other_role_1)
        db.session.add(other_role_2)

        db.session.commit()

        # The role choices are ordered by name and skip the role to delete.
        choices = [
            (0, ''),
            (other_role_2.id, other_role_2.name),
            (other_role_1.id, other_role_1.name),
        ]

        self.assertLess(other_role_1.id, other_role_2.id)
        self.assertListEqual([user], role.users.all())

        form = RoleDeleteForm(role)
        self.assertIsNotNone(form.new_role)
        self.assertListEqual(choices, form.new_role.choices)

# endregion

# region Factories


class PermissionFormFactoryTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.request_context = self.app.test_request_context()
        self.request_context.push()
        db.create_all()

        self.permissions = Permission.EditRole | Permission.EditGlobalSettings

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.request_context.pop()
        self.app_context.pop()

    def test_incorrect_base_class(self):
        """
            Test that the creation is aborted if the given form does not inherit from BasePermissionForm.

            Expected result: A value error is raised.
        """

        class IncorrectBaseClassForm(FlaskForm):
            """
                A form not inheriting from BasePermissionForm.
            """
            pass

        with self.assertRaises(ValueError) as exception_cm:
            create_permission_form(IncorrectBaseClassForm, self.permissions)
            self.assertEqual('The form does not inherit from BasePermissionForm', str(exception_cm.exception))

    def test_field_existence(self):
        """
            Test that the fields for the permissions are correctly added.

            Expected result: For each permission, a field is added and correctly preset. The permissions field
                             dictionary is filled. Permissions given as disabled result in their fields being disabled.
        """

        class PermissionTestForm(BasePermissionForm):
            """
                A simple form to which permission fields will be added.
            """
            pass

        disabled_permissions = Permission.EditRole
        form = create_permission_form(PermissionTestForm, self.permissions, disabled_permissions=disabled_permissions)

        self.assertIsNotNone(form)
        self.assertTrue(isinstance(form, PermissionTestForm))

        # Test that all permissions have got a field.
        # noinspection PyTypeChecker
        permissions = list(Permission)
        for permission in permissions:
            field_name = permission.name.lower()
            field = getattr(form, field_name, None)

            self.assertIsNotNone(field, msg=f'No field for permission {permission}')

            # The label and description are set according to the permission.
            self.assertEqual(permission.title, field.label.text,
                             msg=f'Label wrong for permission {permission}')
            self.assertEqual(permission.description, field.description,
                             msg=f'Description wrong for permission {permission}')

            # The field is selected if the permission is given as a preset permission.
            if permission & self.permissions == permission:
                self.assertTrue(field.default, msg=f'Field for permission {permission} not preselected')
            else:
                self.assertFalse(field.default, msg=f'Field for permission {permission} incorrectly preselected')

            # The field is disabled if the permission is given as a disabled permission.
            if permission & disabled_permissions == permission:
                self.assertTrue(field.render_kw.get('disabled', False),
                                msg=f'Field for permission {permission} is not disabled')
            else:
                self.assertFalse(field.render_kw.get('disabled', False),
                                 msg=f'Field for permission {permission} is incorrectly disabled')

            # The field to permission relation is remembered in the dictionary.
            self.assertEqual(permission, form.permission_fields.get(field_name, None))

        # Ensure that there not more or less fields in the field to permission dictionary than there are permissions.
        self.assertEqual(len(permissions), len(form.permission_fields))

    def test_selected_permissions_get(self):
        """
            Test getting the set permissions from the form.

            Expected result: The `permissions` property returns all permissions that are selected in the form.
        """

        class PermissionTestForm(BasePermissionForm):
            """
                A simple form to which permission fields will be added.
            """
            pass

        # The preselected permissions.
        form = create_permission_form(PermissionTestForm, self.permissions)
        self.assertEqual(self.permissions, form.permissions)

        # Changed permissions with some selected.
        form = create_permission_form(PermissionTestForm, self.permissions)
        form.edituser.data = True
        form.editglobalsettings.data = False
        self.assertEqual(Permission.EditRole | Permission.EditUser, form.permissions)

        # No selection of permissions.
        form = create_permission_form(PermissionTestForm, self.permissions)
        form.editglobalsettings.data = False
        form.editrole.data = False
        self.assertEqual(Permission(0), form.permissions)

    def test_field_order_at_beginning(self):
        """
            Test the field order of the permissions if they are to be inserted before all other fields.

            Expected results: The permission fields appear before all other fields and are in themselves ordered
                              alphabetically by their label.
        """

        class PermissionTestForm(BasePermissionForm):
            """
                A simple form to which permission fields will be added.
            """

            permission_fields_after = None

            submit = SubmitField('Submit')

        form = create_permission_form(PermissionTestForm, self.permissions)

        # The permission field are sorted by their label.
        permission_fields = [form._fields[field_name] for field_name in form.permission_fields]
        sorted_permission_fields = sorted(permission_fields, key=lambda f: f.label.text)
        self.assertListEqual(sorted_permission_fields, permission_fields)

        # The expected fields are in the front, followed by the remaining field, the submit button.
        expected_fields = permission_fields
        expected_fields.append(form.submit)

        actual_fields = list(form)
        self.assertListEqual(expected_fields, actual_fields)

    def test_field_order_at_beginning_with_csrf(self):
        """
            Test the field order of the permissions if they are to be inserted before all other fields, with the CSRF
            field enabled.

            Expected results: The permission fields appear before all other fields, but after the CSRF field, and are in
                              themselves ordered alphabetically by their label.
        """

        self.app.config['WTF_CSRF_ENABLED'] = True

        class PermissionTestForm(BasePermissionForm):
            """
                A simple form to which permission fields will be added.
            """

            permission_fields_after = None

            submit = SubmitField('Submit')

        form = create_permission_form(PermissionTestForm, self.permissions)

        # The permission field are sorted by their label.
        permission_fields = [form._fields[field_name] for field_name in form.permission_fields]
        sorted_permission_fields = sorted(permission_fields, key=lambda f: f.label.text)
        self.assertListEqual(sorted_permission_fields, permission_fields)

        # The expected fields are in the front, followed by the remaining field, the submit button.
        expected_fields = [form.csrf_token]
        expected_fields.extend(permission_fields)
        expected_fields.append(form.submit)

        actual_fields = list(form)
        self.assertListEqual(expected_fields, actual_fields)

    def test_field_order_after_other_field(self):
        """
            Test the field order of the permissions if they are to be inserted after another field.

            Expected results: The permission fields appear after the email field and before the submit field.
        """

        class PermissionTestForm(BasePermissionForm):
            """
                A simple form to which permission fields will be added.
            """

            permission_fields_after = 'email'

            name = StringField('Name')
            email = StringField('Email')
            submit = SubmitField('Submit')

        form = create_permission_form(PermissionTestForm, self.permissions)

        # The permission field are sorted by their label.
        permission_fields = [form._fields[field_name] for field_name in form.permission_fields]
        sorted_permission_fields = sorted(permission_fields, key=lambda f: f.label.text)
        self.assertListEqual(sorted_permission_fields, permission_fields)

        # The expected fields are in the front, followed by the remaining field, the submit button.
        expected_fields = [form.name, form.email]
        expected_fields.extend(permission_fields)
        expected_fields.append(form.submit)

        actual_fields = list(form)
        self.assertListEqual(expected_fields, actual_fields)

# endregion
