#!venv/bin/python
# -*- coding: utf-8 -*-

"""
    Definitions for handling JSON Web Tokens (JWT).
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Set

from time import time

from bidict import bidict
from jwt import decode
from jwt import encode

from app import get_app
from app.exceptions import InvalidJWTokenPayloadError


class JWToken(object):
    """
        A base class for representing JSON Web Tokens (JWT).

        To use a JWT, you have to create a subclass inheriting from :class:`JWToken`. All public instance variables of
        this class (that is, all instance variables not starting with an underscore) will make up the payload of your
        token (there will be a few meta payload fields in the token as well that :class:`JWToken` needs to verify the
        token).

        For example, assume you want to allow your users to change their email address, but you want to be sure that the
        users actually have access to the new address. Therefore, you want to send them a confirmation mail to the new
        address, with a link that the users will have to open to verify their new email address. The user's old
        email address will not be changed until the user opens the link. The link contains a token with payload
        fields for the user's ID and their new email address in order to correctly identify the user to whom the token
        was send and to remember their new email address without having to save it in your database.

        .. code-block:: python

            from app.token import JWToken

            class ChangeEmailAddressToken(JWToken):

                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)

                    # These two instance variables will end up in the payload.
                    self.user_id = None
                    self.new_email = None

                    # This instance variable will not since it starts with an underscore.
                    self._old_email = None

            def send_verification_mail(user_id, new_email, old_email):
                # Create a token to send to a user.
                token_obj = ChangeEmailAddressToken(validity=300)
                token_obj.user_id = user_id
                token_obj.email = new_email
                token_obj._old_email = old_email

                token = token_obj.create()

                # Send the actual mail.
                # ...

            def verify_token(token):
                # Verify the above token.
                received_token_obj = ChangeEmailAddressToken.verify(token)

                # Actually change the address.
                # ...

                # Assuming, the token has been created with user_id = 42,
                # new_email = 'test@example.com' and, old_email = 'mail@example.com'
                assert received_token_obj.user_id == 42
                assert received_token_obj.email == 'test@example.com'
                assert received_token_obj._old_email is None

    """

    _algorithm: str = 'HS256'
    """
        The algorithm used for encoding the token.

        When changing the algorithm, its old value must be added to :attr:`_previous_algorithms` so that old tokens may
        still be decoded properly.
    """

    _previous_algorithms: List[str] = []
    """
        All algorithms that have previously been used for encoding the token, needed for decoding the token.

        When changing the :attr:`_algorithm`, its old value must be added to this list. The algorithm specified in
        :attr:`_algorithm` does not have to be part of this list.
    """

    _instance_var_payload_field_mapping: bidict = bidict(
        _expiration_date='exp',
    )
    """
        A bidirectional mapping from the name of an instance variable to its name in the payload (and vice versa).

        Before creating the payload for a token, all instance variables collected for the payload will be renamed
        according to this mapping. If an instance variable is not found in this mapping, its name will be used in the
        payload.

        When restoring the payload from a token, all payload fields will be written to the instance variable given by
        the inverse mapping. If a payload field is not found in this inverse mapping, its name will be used as the
        instance variable.
    """

    _private_payload_fields: List[str] = [
        '_expiration_date',
        '_jwtoken_class',
        '_validity',
    ]
    """
        List of instance variable names that are part of the payload although their names begin with an underscore.
    """

    def __init__(self, validity: Optional[int] = None) -> None:
        """
            :param validity: If not `None`, the specified value will be used as the validity (in seconds) for the
                             token from its time of creation. If `None`, the validity set in the application
                             configuration (`TOKEN_VALIDITY`) will be used.
        """
        application = get_app()

        self._jwtoken_class: str = self._get_class_name()
        """
            The name of the class creating the token.

            Used for validation of a token.
        """

        self._key: str = application.config['SECRET_KEY']
        """
            The private key for encoding and decoding the token.
        """

        self._validity: int = application.config['TOKEN_VALIDITY']
        """
            The time in seconds how long the token will be valid after its time of creation.
        """

        if validity is not None:
            self._validity = validity

        self._expiration_date: Optional[float] = None
        """
            The date and time when this token will be expire.

            Specified as the time in seconds since the epoch_.

            .. _epoch: https://docs.python.org/3/library/time.html#epoch
        """

        self._token: Optional[str] = None
        """
            Cache the token once it has been created to always return the same one (required due to the validity of the
            token).
        """

    @classmethod
    def verify(cls, token: str) -> 'JWToken':
        """
            Verify the given JSON Web Token.

            :param token: The JWT to verify.
            :return: The object representing the token with the values of the payload set to the corresponding instance
                     variables.
            :raise InvalidJWTokenPayloadError: If the given token's payload is invalid.
        """
        algorithms = cls._get_decode_algorithms()

        jwtoken = cls()

        # Save the token in the object so that calling `create` on it later would return a new token.
        jwtoken._token = token
        payload = decode(token, jwtoken._key, algorithms=algorithms)

        jwtoken._verify_payload(payload)
        jwtoken._restore_payload(payload)

        return jwtoken

    def create(self) -> str:
        """
            Create the actual token from the :class:`JWToken` object. The expiration date is set to the time that is the
            defined number of seconds in the future from the time of creation (see :class:`JWToken`).

            The created token is cached. If :meth:`create` is called multiple times the returned tokens will always
            be the same, and especially will have the expiration date set during the first call of :meth:`create`. To
            reset the cache, use :meth:`reset`.

            If this object has been instantiated from an actual token (see :meth:`verify`) this token will be returned.

            :return: The token represented by the current state of the object.
        """

        # Cache the token once it has been created to always return the same one (required due to the validity of the
        # token).
        if self._token:
            return self._token

        self._expiration_date = time() + self.get_validity()

        payload = self._get_payload()
        token = encode(payload, self._key, algorithm=self._algorithm)
        self._token = token.decode('utf-8')
        return self._token

    def reset(self) -> None:
        """
            Reset the cached token so that the next call of :meth:`create` will return a fresh token.

            The payload will not be reset.
        """
        self._expiration_date = None
        self._token = None

    def get_validity(self, in_minutes: bool = False) -> int:
        """
            Get the validity of the token in seconds.

            :param in_minutes: If `True`, the returned value will specify the validity in minutes, rounded down to the
                               closest integer.
            :return: The validity of the token from its time of creation in seconds.
        """
        if in_minutes:
            return self._validity // 60

        return self._validity

    def _get_payload_fields(self) -> List[str]:
        """
            Get all fields that are part of the payload.

            The expiration date field is not included.

            :return: A list of instance variable that make up the payload fields.
        """
        return [self._map_instance_var_to_payload_field(field)
                for field in vars(self) if self._is_payload_field(field)]

    def _get_payload(self) -> Dict[str, Any]:
        """
            Get the payload for the token.

            The expiration date is not included.

            :return: A dictionary of instance variables with their current values that make of the token's payload.
        """
        return {JWToken._map_instance_var_to_payload_field(field): value
                for (field, value) in vars(self).items() if self._is_payload_field(field)}

    def _restore_payload(self, payload: Dict[str, Any]) -> None:
        """
            Restore the token data from the given payload.

            The payload's values will be written to the field's corresponding instance variable.

            :param payload: The payload from which the state will be restored.
        """
        for field, value in payload.items():
            field = self._map_payload_field_to_instance_var(field)
            setattr(self, field, value)

    def _verify_payload(self, payload: Dict[str, Any]) -> bool:
        """
            Verify that the payload contains exactly the expected fields, that is, expected fields must not be missing
            from the payload and the payload must not contain any additional fields. Furthermore, verify that this
            object is of the right class for the token.

            Expected fields are all those that would be used in a token created by this object.

            :param payload: The payload to verify.
            :return: `True` if the payload contains all expected fields.
            :raise InvalidJWTokenPayloadError: If the payload does not contain exactly the expected fields or if the
                                               class is wrong.
        """
        class_name = self._get_class_name()
        payload_class_name = payload.get('_jwtoken_class', None)
        if payload_class_name is None:
            raise InvalidJWTokenPayloadError('Invalid payload. Missing class specification.')

        if payload_class_name != class_name:
            message = f'Invalid payload. Wrong class: expected {class_name}, got {payload_class_name}'
            raise InvalidJWTokenPayloadError(message)

        expected_fields = set(self._get_payload_fields())
        actual_fields = set(payload.keys())

        missing_fields = expected_fields.difference(actual_fields)
        additional_fields = actual_fields.difference(expected_fields)

        # If there are no missing fields or additional fields, everything is fine.
        if len(missing_fields) == 0 and len(additional_fields) == 0:
            return True

        # Otherwise, raise an exception.
        message = f'Invalid payload. Missing fields: {missing_fields}. Unexpected fields: {additional_fields}'
        raise InvalidJWTokenPayloadError(message)

    def _get_class_name(self) -> str:
        """
            Get the class of the own object.

            :return: The name of the class of which `self` is.
        """
        return type(self).__name__

    @classmethod
    def _get_decode_algorithms(cls) -> Set[str]:
        """
            Get all algorithms for decoding.

            :return: A list of all previous encoding algorithms and the current one.
        """
        return set(cls._previous_algorithms + [cls._algorithm])

    @classmethod
    def _is_payload_field(cls, instance_var: str) -> bool:
        """
            Determine if a given instance variable is part of the token's payload.

            An instance variable will be considered to be a part of the payload if:

            * it is listed in :attr:`_private_payload_fields`, or
            * it does not start with an underscore.

            :param instance_var: The name of the instance variable to check.
            :return: `True` if the instance variable is part of the payload.
        """

        # Some instance variables are always included in the payload.
        if instance_var in cls._private_payload_fields:
            return True

        return not instance_var.startswith('_')

    @classmethod
    def _map_instance_var_to_payload_field(cls, instance_var: str) -> str:
        """
            Map an instance variable that will be part of the payload to its name in the payload.

            :param instance_var: The name of the instance variable to map.
            :return: The name of the corresponding payload field.
        """

        # If the instance variable is not defined in the mapping return the variable's name.
        return cls._instance_var_payload_field_mapping.get(instance_var, instance_var)

    @classmethod
    def _map_payload_field_to_instance_var(cls, payload_field: str) -> str:
        """
            Map a field in the payload to the name of its instance variable.

            :param payload_field: The name of the payload field to map.
            :return: The name of the corresponding instance variable.
        """

        # If the payload field is not defined in the mapping return its field name.
        return cls._instance_var_payload_field_mapping.inv.get(payload_field, payload_field)

    def __str__(self):
        """
            Create the token.

            Alias of :meth:`create()`.

            :return: The token represented by the current state of the object.
        """
        return self.create()
