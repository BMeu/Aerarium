#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Dict
from typing import Optional
from typing import Type

from collections import OrderedDict

from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import Field
from wtforms import Form
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import ValidationError
from wtforms.validators import NoneOf
from wtforms.validators import DataRequired
from wtforms.validators import Length

from app.userprofile import Permission
from app.userprofile import Role

"""
    Forms and form related functionality for the administration.
"""

# region Validators


class UniqueRoleName(object):
    """
        A WTForms validator to verify that an entered role name is not yet in use by another role.

        This validator requires the form to be initialized from an object if it is okay for the role name to stay
        the same.
    """

    def __init__(self, message=None) -> None:
        """
            :param message: The error message shown to the user if the validation fails.
        """
        if not message:
            message = _l('The role name already is in use.')

        self.message = message

    def __call__(self, form: Form, field: Field) -> None:
        """
            Execute the validator.

            :param form: The form to which the field belongs.
            :param field: The field to which this validator is assigned.
            :raise ValidationError: In case the validation fails.
        """
        name = field.data
        if not name:
            return

        # If
        if field.object_data == name:
            return

        # If there already is a role with that name and that role is not
        role = Role.load_from_name(name)
        if role:
            raise ValidationError(self.message)

# endregion

# region Forms


class BasePermissionForm(FlaskForm):
    """
        A base class for all forms having fields to select permissions.

        Do not instantiate this form directly. Instead, create a subclass of :class:`BasePermissionForm` with all the
        needed fields *except* for the permission fields. Then, use :meth:`create_permission_form` to create an object
        of your form including the permission fields. To define the position at which the permission fields will be
        inserted within the form, see :attr:`permission_fields_after`.
    """

    permission_fields_after: Optional[str] = None
    """
        The name of the field after which the permission fields will be inserted. If ``None``, the permission fields
        will be inserted before all other fields.
    """

    permission_fields: Dict[str, Permission] = OrderedDict()
    """
        A dictionary associating a permission field in this form (via its attribute name) to the permission which it
        sets.

        This dictionary will be initialized by the permission form factory, :meth:`create_permission_form`.
    """

    @property
    def permissions(self) -> Permission:
        """
            Get the permissions (:class:`.app.userprofile.Permission`) given by the form's data.

            :return: The (combined) permissions given by the form's data.
        """

        permissions = Permission(0)
        for field_name, permission in self.permission_fields.items():
            field = getattr(self, field_name, None)
            if not field:
                continue

            if field.data:
                permissions |= permission

        return permissions

    def order_fields(self) -> None:
        """
            Order all fields according to :attr:`permission_fields_after`.
        """

        # First, create a list of field names in the correct order: insert all field names including the one after which
        # the permission fields will be displayed into the list (in their current order). Then insert the names of the
        # permission fields. Finally, insert a wildcard * for all remaining fields.
        field_order = []
        if self.permission_fields_after is not None:

            # Insert all fields up until (and including) the field after which the permission fields will be displayed.
            for name, _field in self._unbound_fields:
                field_order.append(name)

                # If the current field is the one after which the permission fields will be inserted, break to be able
                # to insert the permission fields separately.
                if name == self.permission_fields_after:
                    break

        # Include the permission fields and all remaining fields.
        field_order.extend(self.permission_fields.keys())
        field_order.append('*')

        # Secondly, create a list of tuples with the actual fields based upon the ordered field name list from above:
        # the first item in the tuple is the field name, the second one the actual field. If the field is given
        # explicitly by its name find that field and insert it. If the wildcard name is encountered insert all fields
        # that are not named explicitly.
        ordered_fields = []
        csrf_token = None
        if getattr(self, 'csrf_token', None) is not None:
            csrf_token = self.csrf_token.name
            ordered_fields.append((csrf_token, self.csrf_token))

        for name in field_order:
            if name == '*':
                # Wildcard: add all fields not named explicitly.
                ordered_fields.extend([field for field in self._unbound_fields if field[0] not in field_order])
            else:
                # Explicit naming: find and insert the named field.
                ordered_fields.append([field for field in self._unbound_fields if field[0] == name][0])

        # Set the ordered fields on the form. The unbound field list does not contain the CSRF field, the bound field
        # dictionary contains this field.
        # noinspection PyAttributeOutsideInit
        self._unbound_fields = [(name, field) for (name, field) in ordered_fields if name != csrf_token]
        # noinspection PyAttributeOutsideInit
        self._fields = OrderedDict((name, self._fields[name]) for (name, _field) in ordered_fields)


class PermissionForm(BasePermissionForm):
    """
        A form to edit a role's permissions.

        The permission fields must be added dynamically with :meth:`create_permission_form`.
    """

    submit = SubmitField(_l('Save'))
    """
        The submit button.
    """


class RoleDeleteForm(FlaskForm):
    """
        A form to delete a role (and choose a new one for users assigned to the deleted role).
    """

    new_role = SelectField(_l('New Role:'), validators=[DataRequired()], coerce=int,
                           description=_l('Choose a new role for users to whom this role is assigned.'))
    """
        A field for selecting a new role for all users who were previously assigned to the role that will be deleted.
    """

    submit = SubmitField(_l('Delete'))
    """
        The submit button.
    """

    def __init__(self, role: Role, *args, **kwargs):
        """
            :param role: The role that will be deleted. Required for correctly initializing the :attr:`new_role` field.
            :param args: The arguments for initializing the form.
            :param kwargs: The keyword arguments for initializing the form.
        """

        super().__init__(*args, **kwargs)

        # If there are no users to whom this role is assigned it won't be necessary to provide a new role. Just delete
        # the field. Otherwise, fill the list with all roles but the current one.
        role_has_users = role.users.count() >= 1
        if not role_has_users:
            delattr(self, 'new_role')
        else:
            # Add an empty default value.
            choices = [(0, '')]

            # Add all but the current role.
            # noinspection PyProtectedMember
            all_roles = Role.query.filter(Role.id != role.id).order_by(Role._name).all()
            choices.extend([(r.id, r.name) for r in all_roles])

            self.new_role.choices = choices


class RoleHeaderDataForm(FlaskForm):
    """
        A form to edit a role's header data.
    """

    name = StringField(_l('Name:'),
                       validators=[DataRequired(), Length(max=255), NoneOf(Role.invalid_names), UniqueRoleName()],
                       description=_l('The name must be unique: different roles cannot have the same name.'))
    """
        A field for the role's name.
    """

    submit = SubmitField(_l('Save'))
    """
        The submit button.
    """


class RoleNewForm(RoleHeaderDataForm, PermissionForm):
    """
        A form to add a new role.

        This form automatically inherits the header data fields and the permission functionality from its two base
        classes (:class:`RoleHeaderDataForm`, :class:`PermissionForm`) to avoid redundancies.
    """

    permission_fields_after = 'name'
    """
        The name of the field after which the permission fields will be inserted.
    """

    submit = SubmitField(_l('Create'))
    """
        The submit button.
    """

# endregion

# region Factories


def create_permission_form(form_class: Type[BasePermissionForm], preset_permissions: Permission, *args,
                           disabled_permissions: Optional[Permission] = None, **kwargs) -> BasePermissionForm:
    """
        Create a form object of the given class with fields to select permissions.

        :param form_class: The *class* of the form of which the object will be created.
        :param preset_permissions: The permissions whose fields will be preselected.
        :param disabled_permissions: The permissions whose state cannot be changed.
        :param args: Further arguments that will be passed into the form constructor.
        :param kwargs: Further keyword arguments that will be passed into the form constructor.
        :return: An object of the given form class, extended with the fields for setting permissions.
        :raise ValueError: If ``form_class`` is not a subclass of :class:`BasePermissionForm`.
    """

    class ExtendedPermissionForm(form_class):
        """
            A subclass of the given permission form class to which the permission fields will be added and which will
            be instantiated and returned.
        """
        pass

    # Ensure we have all required functionality.
    if not issubclass(form_class, BasePermissionForm):
        raise ValueError('The form does not inherit from BasePermissionForm')

    if not disabled_permissions:
        disabled_permissions = Permission(0)

    # Insert the permission fields.
    # noinspection PyTypeChecker
    permissions = list(Permission)
    for permission in sorted(permissions, key=lambda p: p.title):

        # Preset the permission field if necessary.
        default = False
        if permission & preset_permissions == permission:
            default = True

        # Disable the field if necessary.
        disabled = False
        if permission & disabled_permissions == permission:
            disabled = True

        # Create the field.
        field_name = permission.name.lower()
        field = BooleanField(permission.title, description=permission.description, default=default,
                             render_kw={'disabled': disabled})

        # Add the field to the form and remember which permission it belongs to.
        setattr(ExtendedPermissionForm, field_name, field)
        ExtendedPermissionForm.permission_fields[field_name] = permission

    extended_form = ExtendedPermissionForm(*args, **kwargs)
    extended_form.order_fields()

    return extended_form

# endregion
