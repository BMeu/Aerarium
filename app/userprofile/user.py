# -*- coding: utf-8 -*-

"""
    Classes for representing the application's user model.
"""

from typing import cast
from typing import Optional

from datetime import timedelta

from flask import url_for
from flask_babel import gettext as _
from flask_easyjwt import EasyJWTError
from flask_login import confirm_login
from flask_login import current_user
from flask_login import login_user
from flask_login import logout_user
from flask_login import UserMixin
from flask_sqlalchemy import BaseQuery

from app import bcrypt
from app import db
from app import Email
from app import get_app
from app import login as app_login
from app import Pagination
from app import timedelta_to_minutes
from app.userprofile import Permission
from app.userprofile import Role
from app.userprofile import UserSettings
from app.userprofile.tokens import ChangeEmailAddressToken
from app.userprofile.tokens import DeleteAccountToken
from app.userprofile.tokens import ResetPasswordToken


class User(UserMixin, db.Model):  # type: ignore
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

    _password_hash = db.Column('password_hash', db.String(128))
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
        The user's settings (:class:`app.userprofile.UserSettings`).
    """

    _role_id = db.Column('role_id', db.Integer, db.ForeignKey('role.id'))
    """
        The ID of the role (:class:`.Role`) to which the user is assigned. The actual role object can be accessed via
        the attribute :attr:`role`.
    """

    @property
    def email(self) -> Optional[str]:
        """
            Get the user's email address.

            :return: The user's email address. `None` if the user is currently being created and the email address has
                     not yet been set.
        """

        return self._email  # type: ignore

    @property
    def is_active(self) -> bool:
        """
            The activation status of the user's account.

            :return: `True` if the user account is activated.
        """

        return self._is_activated  # type: ignore

    @is_active.setter
    def is_active(self, value: bool) -> None:
        """
            Set the activation status of this user account.

            :param value: `True` if the user account is activated.
        """

        self._is_activated = value

    # endregion

    # region Initialization

    def __init__(self, email: str, name: str) -> None:
        """
            :param email: The user's email address.
            :param name: The user's (full) name.
        """

        self._set_email(email)
        self.name = name

        self.settings = UserSettings()

    @staticmethod
    @app_login.user_loader  # type: ignore
    def load_from_id(user_id: int) -> Optional['User']:
        """
            Load the user with the given ID from the database.

            :param user_id: The ID of the user to load.
            :return: The loaded user if they exist, `None` otherwise.
        """

        return User.query.get(user_id)  # type: ignore

    @staticmethod
    def load_from_email(email: str) -> Optional['User']:
        """
            Load the user with the given email address from the database.

            :param email: The email address of the user to load.
            :return: The loaded user if they exist, `None` otherwise.
        """

        return User.query.filter_by(_email=email).first()  # type: ignore

    # endregion

    # region Login/Logout

    @staticmethod
    def login(email: str, password: str, remember_me: bool = False) -> Optional['User']:
        """
            Try to log in the user given by their email address and password.

            :param email: The user's email address.
            :param password: The user's (plaintext) password.
            :param remember_me: `True` if the user wishes to stay logged in across sessions.
            :return: The user if the email/password combination is valid and the user is logged in, `None` otherwise.
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
    def refresh_login(password: str) -> Optional['User']:
        """
            Try to refresh the current user's login.

            :param password: The user's (plaintext) password.
            :return: The user if the password is valid for the given user; `None` otherwise.
        """

        user_id = current_user.get_id()
        if user_id is None:
            return None

        user = User.load_from_id(user_id)
        if not user.check_password(password):
            return None

        confirm_login()
        return user  # type: ignore

    @staticmethod
    def logout() -> bool:
        """
            Log out the user.

            :return: `True` on successful logout.
        """

        logged_out = logout_user()
        return logged_out  # type: ignore

    # endregion

    # region Email

    def _set_email(self, email: str) -> bool:
        """
            Change the user's email address to the new given one.

            An email will be sent to the user's old email address informing them about this change.

            :param email: The user's new email address. Must not be used by a different user.
            :return: `False` if the email address is already in use by another user, `True` otherwise.
        """

        old_email = self.email
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

    def request_email_address_change(self, new_email_address: str) -> timedelta:
        """
            Request to change the user's email address to the given new email address.

            This method will only create a JWT and send it in an email to the user's new email address. The user will
            then have to verify this token within the token's validity to actually change the email address to the new
            one. Until this verification has taken place, the email address will not have been changed.

            To verify the token and actually set the new email address, execute :meth:`set_email_from_token`.

            :param new_email_address: The email address to which the token will be sent and to which the user's email
                                      will be changed upon verification.
            :return: The validity of the token.
        """

        token_obj = ChangeEmailAddressToken()
        token_obj.user_id = self.id
        token_obj.new_email = new_email_address

        token = token_obj.create()
        validity: timedelta = token_obj.get_validity()

        link = url_for('userprofile.change_email', token=token, _external=True)
        email_old = self.email

        email_obj = Email(_('Change Your Email Address'), 'userprofile/emails/change_email_address_request')
        email_obj.prepare(name=self.name, link=link, validity=timedelta_to_minutes(validity), email_old=email_old,
                          email_new=new_email_address)
        email_obj.send(new_email_address)

        return validity

    @staticmethod
    def set_email_address_from_token(token: str) -> bool:
        """
            Verify the token to change a user's email address. If it is valid, change the email address of the user
            given in the token to the email address given in the token.

            To get a token, execute :meth:`request_email_address_change`.

            :param token: The change-email token.
            :return: `True` if the email address has been set, `False` if the email address could not be set.
            :raise EasyJWTError: If the given token is invalid.
            :raise ValueError: If the user given in the token does not exist.
        """

        token_obj = ChangeEmailAddressToken.verify(token)
        user = User.load_from_id(token_obj.user_id)
        if user is None:
            raise ValueError(f'User {token_obj.user_id} does not exist')

        # Set the email address and commit the change to the DB on success.
        changed = user._set_email(token_obj.new_email)
        if not changed:
            return False

        db.session.commit()
        return True

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
        if self._password_hash is not None and self.email is not None:
            application = get_app()

            support_address = application.config.get('SUPPORT_ADDRESS', None)

            email = Email(_('Your Password Has Been Changed'), 'userprofile/emails/reset_password_confirmation')
            email.prepare(name=self.name, support_email=support_address)
            email.send(self.email)

        self._password_hash = bcrypt.generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """
            Check if the given password matches the user's password.

            :param password: The plaintext password to verify.
            :return: `True` if the given password matches the user's password.
        """

        if not self._password_hash:
            return False

        return bcrypt.check_password_hash(self._password_hash, password)  # type: ignore

    def request_password_reset(self) -> Optional[ResetPasswordToken]:
        """
            Send a mail for resetting the user's password to their email address.

            :return: The token send in the mail.
        """

        if self.email is None:
            return None

        token_obj = ResetPasswordToken()
        token_obj.user_id = self.id
        token = token_obj.create()

        validity = timedelta_to_minutes(token_obj.get_validity())

        link = url_for('userprofile.reset_password', token=token, _external=True)

        email = Email(_('Reset Your Password'), 'userprofile/emails/reset_password_request')
        email.prepare(name=self.name, link=link, validity=validity)
        email.send(self.email)

        return token_obj

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional['User']:
        """
            Verify a given token for resetting a password.

            :param token: The password-reset JWT.
            :return: The user for whom the token is valid. `None` if the token is invalid or if outside the
                     application context.
        """

        try:
            token_obj = ResetPasswordToken.verify(token)
        except EasyJWTError:
            return None

        return User.load_from_id(token_obj.user_id)  # type: ignore

    # endregion

    # region Delete

    def request_account_deletion(self) -> Optional[DeleteAccountToken]:
        """
            Send a token via email to the user to confirm their intention to delete their account.

            :return: The token sent in the mail. `None` if the user has no email.
        """

        token_obj = DeleteAccountToken()
        token_obj.user_id = self.id

        token = token_obj.create()
        validity = timedelta_to_minutes(token_obj.get_validity())

        link = url_for('userprofile.delete_profile', token=token, _external=True)

        if self.email is None:
            return None

        email = Email(_('Delete Your User Profile'), 'userprofile/emails/delete_account_request')
        email.prepare(name=self.name, link=link, validity=validity)
        email.send(self.email)

        return token_obj

    @staticmethod
    def delete_account_from_token(token: str) -> bool:
        """
            Delete the account of the user given in the :class:`DeleteAccountToken` token.

            The user that will deleted must be logged in.

            :param token: The token to delete an account, created with :class:`DeleteAccountToken`.
            :return: `True` if the user in the token has been deleted, `False` otherwise, e.g. if the token is invalid.
        """

        try:
            token_obj = DeleteAccountToken.verify(token)
        except EasyJWTError:
            return False

        user = User.load_from_id(token_obj.user_id)
        if user is None:
            return False

        # A user can only delete their own account with a token.
        if current_user != user:
            return False

        user._delete()
        return True

    def _delete(self) -> None:
        """
            Delete the user's account. Log them out first if necessary. Notify them via mail.

            This action will directly be committed to the database.
        """

        if self == current_user:
            self.logout()

        # Notify the user via email.
        application = get_app()
        support_address = application.config.get('SUPPORT_ADDRESS', None)

        if self.email is not None:
            email = Email(_('Your User Profile Has Been Deleted'), 'userprofile/emails/delete_account_confirmation')
            email.prepare(name=self.name, new_email=self.email, support_email=support_address)
            email.send(self.email)

        db.session.delete(self)
        db.session.commit()

    # endregion

    # region Permissions

    @staticmethod
    def current_user_has_permission(permission: Permission) -> bool:
        """
            Check if the current user (:attr:`flask_login.current_user`) has the given permission.

            :param permission: The permission to check for.
            :return: `True` if the current user has the permission, `False` otherwise.
        """

        # If the current user does not have a role, the user cannot have the permissions.
        role = User.get_role_of_current_user()
        if role is None or not role.has_permission(permission):
            return False

        return True

    @staticmethod
    def current_user_has_permissions_all(*permissions: Permission) -> bool:
        """
            Check if the current user (:attr:`flask_login.current_user`) has all of the given permissions.

            This does not check if the current user is logged in.

            :param permissions: The permission enumeration members to check for.
            :return: `True` if the current user has the permissions, `False` otherwise.
        """

        # If the current user does not have a role, the user cannot have the permissions.
        role = User.get_role_of_current_user()
        if role is None or not role.has_permissions_all(*permissions):
            return False

        return True

    @staticmethod
    def current_user_has_permissions_one_of(*permissions: Permission) -> bool:
        """
            Check if the current user (:attr:`flask_login.current_user`) has (at least) one of the given permissions.

            This does not check if the current user is logged in.

            :param permissions: The permission enumeration members to check for.
            :return: `True` if the current user the permissions, `False` otherwise.
        """

        # If the current user does not have a role, the user cannot have the permissions.
        role = User.get_role_of_current_user()
        if role is None or not role.has_permissions_one_of(*permissions):
            return False

        return True

    @staticmethod
    def get_role_of_current_user() -> Optional[Role]:
        """
            Get the role of the currently logged in user.

            :return: The role of the user who is currently logged in. `None` if the user is not logged in.
        """

        try:
            return cast(Role, current_user.role)
        except AttributeError:
            return None

    # endregion

    # region DB Queries

    @staticmethod
    def get_search_query(query: Optional[BaseQuery] = None, search_term: Optional[str] = None) -> BaseQuery:
        """
            Get a query that searches the users for the given search term on their names or email addresses.

            The search term may contain wildcards (``*``).

            :param query: A base query object. If not given, the :attr:`User.query` will be used.
            :param search_term: The term for which the users will be searched. If `None`, a non-filtering query will
                                be returned.
            :return: The query object.
        """

        if query is None:
            query = User.query

        if search_term is None or search_term == '':
            return query

        # Replace the wildcard character with the SQL wildcard.
        search_term = search_term.replace('*', '%')
        return query.filter(db.or_(User.name.like(search_term), User._email.like(search_term)))

    # endregion

    # region System

    def __repr__(self) -> str:
        """
            Get a string representation of the user.

            :return: A string representation of the user.
        """

        return f'<User [{self.id}] {self.email}>'

    # endregion


class UserPagination(Pagination):
    """
        A pagination object for users specializing the info texts.
    """

    def get_info_text(self, search_term: Optional[str] = None) -> str:
        """
            Get an informational text explaining how many results are being displayed on the current page.

            :param search_term: If given, this term will be included in the info text to explain that the results are
                                being filtered by this value.
            :return: The info text.
        """

        # Text with a search.
        if search_term:

            # More than one result on the page.
            if self.rows_on_page >= 2:
                return _('Displaying users %(first_result)d to %(last_result)d of %(total_results)d '  # type: ignore
                         'matching “%(search)s”',
                         first_result=self.first_row, last_result=self.last_row, total_results=self.total_rows,
                         search=search_term)

            # One result on the page.
            if self.rows_on_page == 1:
                return _('Displaying user %(result)d of %(total_results)d matching “%(search)s”',  # type: ignore
                         result=self.first_row, total_results=self.total_rows, search=search_term)

            # No results.
            return _('No users found matching “%(search)s”', search=search_term)  # type: ignore

        # Text without a search.

        # More than one result on the page.
        if self.rows_on_page >= 2:
            return _('Displaying users %(first_result)d to %(last_result)d of %(total_results)d',  # type: ignore
                     first_result=self.first_row, last_result=self.last_row, total_results=self.total_rows)

        # One result on the page.
        if self.rows_on_page == 1:
            return _('Displaying user %(result)d of %(total_results)d',  # type: ignore
                     result=self.first_row, total_results=self.total_rows)

        # No results.
        return _('No users')  # type: ignore
