#!venv/bin/python
# -*- coding: utf-8 -*-

from typing import Optional
from typing import Tuple

from flask import url_for
# noinspection PyProtectedMember
from flask_babel import _
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login import UserMixin

from app import bcrypt
from app import db
from app import Email
from app import get_app
from app import login as app_login
from app.userprofile import Permission
from app.userprofile import UserSettings
from app.userprofile.tokens import ChangeEmailAddressToken
from app.userprofile.tokens import DeleteAccountToken
from app.userprofile.tokens import ResetPasswordToken

"""
    The application's user model.
"""


class User(UserMixin, db.Model):
    """
        The class representing the application's users.
    """

    # region Fields and Properties

    id = db.Column(db.Integer, primary_key=True)
    """
        The user's unique ID.
    """

    _email = db.Column('email', db.String(255), index=True, unique=True)
    """
        The user's email address.
    """

    password_hash = db.Column(db.String(128))
    """
        The user's password, salted and hashed.
    """

    name = db.Column(db.String(255))
    """
        The user's (full) name.
    """

    _is_activated = db.Column('is_activated', db.Boolean, default=True)
    """
        Whether the user has activated their account.
    """

    settings = db.relationship('UserSettings', backref='user', cascade='all, delete-orphan', uselist=False)
    """
        The user's settings (:class:`UserSettings`).
    """

    _role_id = db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
    """
        The ID of the role (:class:`.Role`) to which the user is assigned. The actual role object can be accessed via
        the attribute `role`.
    """

    @property
    def is_active(self) -> bool:
        """
            Determine if the user has activated their account.

            :return: ``True`` if the user account is activated.
        """
        return self._is_activated

    @is_active.setter
    def is_active(self, value: bool) -> None:
        """
            Set the activation status of this user account.

            :param value: ``True`` if the user account is activated.
        """
        self._is_activated = value

    # endregion

    # region Initialization

    def __init__(self, email: str, name: str) -> None:
        """
            Initialize the user.

            :param email: The user's email address.
            :param name: The user's (full) name.
        """
        self.set_email(email)
        self.name = name

        self.settings = UserSettings()

    @staticmethod
    @app_login.user_loader
    def load_from_id(user_id: int) -> Optional['User']:
        """
            Load the user with the given ID from the database.

            :param user_id: The ID of the user to load.
            :return: The loaded user if it exists, ``None`` otherwise.
        """

        return User.query.get(user_id)

    @staticmethod
    def load_from_email(email: str) -> Optional['User']:
        """
            Load the user with the given email address from the database.

            :param email: The email address of the user to load.
            :return: The loaded user if it exists, ``None`` otherwise.
        """

        return User.query.filter_by(_email=email).first()

    # endregion

    # region Login/Logout

    @staticmethod
    def login(email: str, password: str, remember_me: bool = False) -> Optional['User']:
        """
            Try to log in the user given by their email address and password.

            :param email: The user's email address.
            :param password: The user's (plaintext) password.
            :param remember_me: ``True`` if the user shall be kept logged in across sessions.
            :return: The user if the email/password combination is valid and the user is logged in, ``None`` otherwise.
        """

        user = User.load_from_email(email)
        if user is None:
            return None

        if not user.check_password(password):
            return None

        logged_in = login_user(user, remember=remember_me)
        if not logged_in:
            return None

        return user

    @staticmethod
    def logout() -> bool:
        """
            Log out the user.

            :return: ``True`` on successful logout.
        """

        logged_out = logout_user()
        return logged_out

    # endregion

    # region Email

    def get_email(self) -> str:
        """
            Get the user's email address.

            :return: The user's email address.
        """
        return self._email

    def set_email(self, email: str) -> bool:
        """
            Change the user's email address to the new given one.

            :param email: The user's new email address. Must not be used by a different user.
            :return: ``False`` if the email address already is in use by another user, ``True`` otherwise.
        """

        old_email = self.get_email()
        if old_email == email:
            return True

        user = User.load_from_email(email)
        if user is not None and user != self:
            return False

        self._email = email
        if not old_email:
            # If there is no old email the user has just been created. Do not send an email in this case.
            return True

        application = get_app()
        support_address = application.config.get('SUPPORT_ADDRESS', None)

        email_obj = Email(_('Your Email Address Has Been Changed'),
                          'userprofile/emails/change_email_address_confirmation')
        email_obj.prepare(name=self.name, new_email=email, support_email=support_address)
        email_obj.send(old_email)

        return True

    def send_change_email_address_email(self, email: str) -> ChangeEmailAddressToken:
        """
            Send a token to the user to change their email address.

            :param email: The email address to which the token will be sent and to which the user's email will be
                          changed upon verification.
            :return: The token send in the mail.
        """

        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = self.id
        token_obj.new_email = email

        token = token_obj.create()
        validity = token_obj.get_validity(in_minutes=True)

        link = url_for('userprofile.change_email', token=token, _external=True)
        email_old = self.get_email()

        email_obj = Email(_('Change Your Email Address'), 'userprofile/emails/change_email_address_request')
        email_obj.prepare(name=self.name, link=link, validity=validity, email_old=email_old, email_new=email)
        email_obj.send(email)

        return token_obj

    @staticmethod
    def verify_change_email_address_token(token: str) -> Tuple[Optional['User'], Optional[str]]:
        """
            Verify the JWT to change a user's email address.

            :param token: The change-email token.
            :return: The user to which the token belongs and the new email address; both are ``None`` if the token is
                     invalid.
        """
        token_obj = ChangeEmailAddressToken.verify(token)
        user = User.load_from_id(token_obj.user_id)
        return user, token_obj.new_email

    # endregion

    # region Password

    def set_password(self, password: str) -> None:
        """
            Hash and set the given password.

            :param password: The plaintext password.
        """

        if not password:
            return

        # If the password stayed the same do not do anything; especially, do not send an email.
        if self.check_password(password):
            return

        # If the user does not have a password at the moment, their account has been newly created. Do not send an email
        # in this case.
        if self.password_hash is not None:
            application = get_app()

            support_address = application.config.get('SUPPORT_ADDRESS', None)

            email = Email(_('Your Password Has Been Changed'), 'userprofile/emails/reset_password_confirmation')
            email.prepare(name=self.name, support_email=support_address)
            email.send(self.get_email())

        self.password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
            Check if the given password matches the user's password.

            :param password: The plaintext password to verify.
            :return: ``True`` if the ``password`` matches the user's password.
        """
        if not self.password_hash:
            return False

        return bcrypt.check_password_hash(self.password_hash, password)

    def send_password_reset_email(self) -> Optional[ResetPasswordToken]:
        """
            Send a mail for resetting the user's password to their email address.

            :return: The token send in the mail
        """

        if self.get_email() is None:
            return None

        token_obj = ResetPasswordToken()
        token_obj.user_id = self.id
        token = token_obj.create()

        validity = token_obj.get_validity(in_minutes=True)

        link = url_for('userprofile.reset_password', token=token, _external=True)

        email = Email(_('Reset Your Password'), 'userprofile/emails/reset_password_request')
        email.prepare(name=self.name, link=link, validity=validity)
        email.send(self.get_email())

        return token_obj

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional['User']:
        """
            Verify a given token for resetting a password.

            :param token: The password-reset JWT.
            :return: The user for whom the token is valid. ``None`` if the token is invalid or if outside the
                     application context.
        """
        token_obj = ResetPasswordToken.verify(token)
        return User.load_from_id(token_obj.user_id)

    # endregion

    # region Delete

    def send_delete_account_email(self) -> DeleteAccountToken:
        """
            Send a token to the user to confirm their intention to delete their account.

            :return: The token sent in the mail.
        """
        token_obj = DeleteAccountToken()
        token_obj.user_id = self.id

        token = token_obj.create()
        validity = token_obj.get_validity(in_minutes=True)

        link = url_for('userprofile.delete_profile', token=token, _external=True)

        email = Email(_('Delete Your User Profile'), 'userprofile/emails/delete_account_request')
        email.prepare(name=self.name, link=link, validity=validity)
        email.send(self.get_email())

        return token_obj

    @staticmethod
    def verify_delete_account_token(token: str) -> Optional['User']:
        """
            Verify the JWT to delete a user's account.

            :param token: The delete-account token.
            :return: The user to which the token belongs; ``None`` if the token is invalid.
        """
        token_obj = DeleteAccountToken.verify(token)
        user = User.load_from_id(token_obj.user_id)
        return user

    def delete(self) -> None:
        """
            Delete the user's account. Log them out first if necessary. Notify them via mail.

            This action will directly be committed to the database.
        """
        if self == current_user:
            self.logout()

        # Notify the user via email.
        application = get_app()
        support_address = application.config.get('SUPPORT_ADDRESS', None)

        email = Email(_('Your User Profile Has Been Deleted'), 'userprofile/emails/delete_account_confirmation')
        email.prepare(name=self.name, new_email=self.get_email(), support_email=support_address)
        email.send(self.get_email())

        db.session.delete(self)
        db.session.commit()

    # endregion

    # region Permissions

    @staticmethod
    def current_user_has_permissions_all(*permissions: Permission) -> bool:
        """
            Check if the current user has all of the given permissions.

            This does not check if the current user is logged in.

            :param permissions: The permission enumeration members to check for.
            :return: `True` if the current user has the permissions, `False` otherwise.
        """
        permission = Permission.bitwise_or(*permissions)

        # If the current user does not have a role, the user cannot have the permissions.
        try:
            role = current_user.role
        except AttributeError:
            return False

        if role is None or not role.has_permission(permission):
            return False

        return True

    @staticmethod
    def current_user_has_permissions_one_of(*permissions: Permission) -> bool:
        """
            Check if the current user has (at least) one of the given permissions.

            This does not check if the current user is logged in.

            :param permissions: The permission enumeration members to check for.
            :return: `True` if the current user the permissions, `False` otherwise.
        """

        # If the current user does not have a role, the user cannot have the permissions.
        try:
            role = current_user.role
        except AttributeError:
            return False

        if role is None:
            return False

        has_permission = False
        for permission in permissions:
            has_permission = has_permission or role.has_permission(permission)

        return has_permission

    # endregion

    # region System

    def __repr__(self) -> str:
        """
            Get a string representation of the user.

            :return: A string representation of the user.
        """
        return f'<User [{self.id}] {self.get_email()}>'

    # endregion
