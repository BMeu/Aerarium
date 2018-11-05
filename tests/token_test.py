#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase

from app import create_app
from app import db
from app.configuration import TestConfiguration
from app.exceptions import InvalidJWTokenPayloadError
from app.token import JWToken


class JWTokenTest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.app.config['TOKEN_VALIDITY'] = 600

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_init_default_validity(self):
        """
            Test initializing a new token object with the default validity.

            Expected Result: The instance variables are set correctly.
        """
        jwtoken = JWToken()
        self.assertEqual(jwtoken._get_class_name(), jwtoken._jwtoken_class)
        self.assertEqual(self.app.config['SECRET_KEY'], jwtoken._key)
        self.assertEqual(self.app.config['TOKEN_VALIDITY'], jwtoken._validity)
        self.assertIsNone(jwtoken._expiration_date)
        self.assertIsNone(jwtoken._token)

    def test_init_custom_validity(self):
        """
            Test creating a new token object with a custom validity.

            Expected Result: The validity is set to the custom value.
        """
        validity = 300
        jwtoken = JWToken(validity)
        self.assertEqual(jwtoken._get_class_name(), jwtoken._jwtoken_class)
        self.assertEqual(self.app.config['SECRET_KEY'], jwtoken._key)
        self.assertEqual(validity, jwtoken._validity)
        self.assertIsNone(jwtoken._expiration_date)
        self.assertIsNone(jwtoken._token)

    def test_verify_success(self):
        """
            Test verifying a valid token.

            Expected Result: An object representing the token is returned.
        """
        jwtoken_creation = JWToken(300)
        token = jwtoken_creation.create()

        jwtoken_verification = JWToken.verify(token)
        self.assertIsNotNone(jwtoken_verification)
        self.assertEqual(jwtoken_creation._key, jwtoken_verification._key)
        self.assertEqual(jwtoken_creation._validity, jwtoken_verification._validity)
        self.assertEqual(jwtoken_creation._expiration_date, jwtoken_verification._expiration_date)
        self.assertEqual(jwtoken_creation._token, jwtoken_verification._token)
        self.assertEqual(jwtoken_creation._jwtoken_class, jwtoken_verification._jwtoken_class)

    def test_verify_failure(self):
        """
            Test verifying an invalid token.

            Expected Result: No object representing the token is returned, but an error is raised.
        """
        jwtoken_creation = JWToken(300)

        # Add some payload field to the object that is not part of the class.
        fake_field = 'part_of_the_payload'
        jwtoken_creation.part_of_the_payload = True
        self.assertTrue(jwtoken_creation._is_payload_field(fake_field))

        token = jwtoken_creation.create()

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken_verification = JWToken.verify(token)
            self.assertIsNone(jwtoken_verification)
            self.assertIn(fake_field, exception)

    def test_create_uncached(self):
        """
             Test creating a token if it has not been created before.

             Expected Result: A token is created.
        """
        jwtoken = JWToken()
        self.assertIsNone(jwtoken._token)
        self.assertIsNone(jwtoken._expiration_date)

        token = jwtoken.create()
        self.assertIsNotNone(token)
        self.assertIsNotNone(jwtoken._expiration_date)
        self.assertEqual(token, jwtoken._token)

    def test_create_cached(self):
        """
             Test creating a token if it has been created before.

             Expected Result: The exact same token is returned.
        """
        jwtoken = JWToken()
        self.assertIsNone(jwtoken._token)
        self.assertIsNone(jwtoken._expiration_date)

        # Create the first time.
        token = jwtoken.create()
        expiration_date = jwtoken._expiration_date

        # Create the second time.
        self.assertEqual(token, jwtoken.create())
        self.assertEqual(expiration_date, jwtoken._expiration_date)
        self.assertEqual(token, jwtoken._token)

    def test_reset(self):
        """
            Test resetting a token object after a token has been created before.

            Expected result: After resetting, a new different token can be created.
        """
        jwtoken = JWToken()

        # Create the first time.
        old_token = jwtoken.create()
        old_expiration_date = jwtoken._expiration_date

        jwtoken.reset()
        self.assertIsNone(jwtoken._token)
        self.assertIsNone(jwtoken._expiration_date)
        self.assertEqual(jwtoken._get_class_name(), jwtoken._jwtoken_class)

        # Create a new token.
        new_token = jwtoken.create()
        self.assertNotEqual(old_token, new_token)
        self.assertEqual(new_token, jwtoken._token)
        self.assertNotEqual(old_expiration_date, jwtoken._expiration_date)

    def test_get_validity_in_seconds(self):
        """
            Test getting the validity in seconds.

            Expected Result: The validity is returned unaltered.
        """
        jwtoken = JWToken()
        self.assertEqual(jwtoken._validity, jwtoken.get_validity())

    def test_get_validity_in_minutes(self):
        """
            Test getting the validity in minutes.

            Expected Result: The validity is returned in minutes, rounded down to the nearest integer..
        """
        validity_in_minutes = 9
        # Set the validity to almost the next full minute to test the rounding down.
        jwtoken = JWToken(validity_in_minutes * 60 + 59)
        self.assertEqual(validity_in_minutes, jwtoken.get_validity(in_minutes=True))

    def test_get_payload_fields(self):
        """
            Test getting the list of payload fields.

            Expected Result: A list with the fields for the validity and expiration date is returned.
        """
        payload_fields = ['_jwtoken_class', '_validity', 'exp']
        jwtoken = JWToken()
        self.assertListEqual(payload_fields, jwtoken._get_payload_fields())

    def test_get_payload(self):
        """
            Test getting the payload dictionary.

            Expected Result: A dictionary with the entries for the validity and expiration date is returned.
        """
        payload = dict(
            _jwtoken_class='JWToken',
            _validity=self.app.config['TOKEN_VALIDITY'],
            exp=None,
        )
        jwtoken = JWToken()
        self.assertDictEqual(payload, jwtoken._get_payload())

    def test_payload_fields_and_payload_keys_equal(self):
        """
            Assert that the list of payload fields is exactly the same as the list of payload keys.

            Expected Result: The list of payload fields equals the list of payload keys.
        """
        jwtoken = JWToken()
        payload_fields = jwtoken._get_payload_fields()
        payload = jwtoken._get_payload()
        self.assertListEqual(payload_fields, list(payload.keys()))

    def test_restore_payload(self):
        """
            Test restoring a payload dictionary.

            Expected Result: The values in the payload are mapped to their respective instance variables.
        """
        payload = dict(
            _jwtoken_class='JWToken',
            _validity=42,
            exp=946684800.0,
        )

        jwtoken = JWToken()
        jwtoken._restore_payload(payload)
        self.assertEqual(payload['_validity'], jwtoken._validity)
        self.assertEqual(payload['exp'], jwtoken._expiration_date)

    def test_verify_payload_success(self):
        """
            Test verifying a valid payload.

            Expected result: `True`
        """
        jwtoken = JWToken()
        payload = jwtoken._get_payload()
        self.assertTrue(jwtoken._verify_payload(payload))

    def test_verify_payload_failure_missing_class(self):
        """
            Test verifying a payload with a missing class field.

            Expected result: An exception with an explaining message is raised.
        """
        jwtoken = JWToken()
        payload = jwtoken._get_payload()
        del payload['_jwtoken_class']

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken._verify_payload(payload)
            self.assertIn('Missing class specification', exception)

    def test_verify_payload_failure_wrong_class(self):
        """
            Test verifying a payload with a faulty value in the class field.

            Expected result: An exception with an explaining message is raised.
        """
        jwtoken = JWToken()
        payload = jwtoken._get_payload()
        payload['_jwtoken_class'] = 'InheritedJWToken'

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken._verify_payload(payload)
            self.assertIn('Wrong class: expected JWToken, got InheritedJWToken', exception)

    def test_verify_payload_failure_missing_fields(self):
        """
            Test verifying a payload with missing fields.

            Expected result: An exception with an explaining message is raised.
        """
        jwtoken = JWToken()
        payload = jwtoken._get_payload()
        del payload['_validity']

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken._verify_payload(payload)
            self.assertIn('Missing fields: {_validity}. Unexpected fields: {}', exception)

    def test_verify_payload_failure_unexpected_fields(self):
        """
            Test verifying a payload with unexpected fields.

            Expected result: An exception with an explaining message is raised.
        """
        jwtoken = JWToken()
        payload = jwtoken._get_payload()
        payload['user_id'] = 1

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken._verify_payload(payload)
            self.assertIn('Missing fields: {}. Unexpected fields: {user_id}', exception)

    def test_verify_payload_failure_missing_and_unexpected_fields(self):
        """
            Test verifying a payload with missing and unexpected fields.

            Expected result: An exception with an explaining message is raised.
        """
        jwtoken = JWToken()
        payload = jwtoken._get_payload()
        del payload['_validity']
        payload['user_id'] = 1

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken._verify_payload(payload)
            self.assertIn('Missing fields: {_validity}. Unexpected fields: {user_id}', exception)

    def test_get_class_name(self):
        """
            Test getting the name of the class.

            Expected Result: 'JWToken' is returned.
        """
        jwtoken = JWToken()
        self.assertEqual('JWToken', jwtoken._get_class_name())

    def test_get_decode_algorithms(self):
        """
            Test getting the algorithms for decoding a token.

            Expected Result: A set of all previous encoding algorithms and the current one is returned.
        """
        # Temporarily save the current class variables to restore them later. Otherwise, changes could influence other
        # parts of the tests.
        current_alg_temp = JWToken._algorithm
        previous_algs_temp = JWToken._previous_algorithms

        JWToken._algorithm = 'HS256'
        JWToken._previous_algorithms = ['SHA1', 'MD5']

        algorithms = {'HS256', 'SHA1', 'MD5'}
        self.assertSetEqual(algorithms, JWToken._get_decode_algorithms())

        # Restore the class variables.
        JWToken._algorithm = current_alg_temp
        JWToken._previous_algorithms = previous_algs_temp

    def test_is_payload_field_expiration_date(self):
        """
            Test if the instance variable for the expiration date is a payload field.

            Expected Result: `True`.
        """
        self.assertTrue(JWToken._is_payload_field('_expiration_date'))

    def test_is_payload_field_validity(self):
        """
            Test if the instance variable for the validity is a payload field.

            Expected Result: `True`.
        """
        self.assertTrue(JWToken._is_payload_field('_validity'))

    def test_is_payload_field_whitelist(self):
        """
            Test if the instance variables in the whitelist are payload fields.

            Expected Result: `True` for each entry in the whitelist.
        """
        for instance_var in JWToken._private_payload_fields:
            self.assertTrue(JWToken._is_payload_field(instance_var), f'{instance_var} is not a payload field')

    def test_is_payload_field_private_instance_vars(self):
        """
            Test if private instance variables that are not in the whitelist are payload fields.

            Expected Result: `False`
        """
        instance_var = '_not_part_of_the_payload'
        self.assertNotIn(instance_var, JWToken._private_payload_fields)
        self.assertFalse(JWToken._is_payload_field(instance_var))

    def test_is_payload_field_public_instance_vars(self):
        """
            Test if public instance variables (that are not in the whitelist) are payload fields.

            Expected Result: `True`
        """
        instance_var = 'part_of_the_payload'
        self.assertNotIn(instance_var, JWToken._private_payload_fields)
        self.assertTrue(JWToken._is_payload_field(instance_var))

    def test_map_instance_var_to_payload_field_expiration_date(self):
        """
            Test that the expiration date is mapped correctly from instance var to payload field.

            Expected Result: The payload field for the expiration date is returned.
        """
        self.assertEqual('exp', JWToken._map_instance_var_to_payload_field('_expiration_date'))

    def test_map_instance_var_to_payload_field_unmapped(self):
        """
            Test that an instance variable that is not in the map is returned as the payload field.

            Expected Result: The name of the instance variable is returned unchanged.
        """
        instance_var = 'part_of_the_payload'
        self.assertNotIn(instance_var, JWToken._instance_var_payload_field_mapping)
        self.assertEqual(instance_var, JWToken._map_instance_var_to_payload_field(instance_var))

    def test_map_payload_field_to_instance_var_expiration_date(self):
        """
            Test that the expiration date is mapped correctly from payload field to instance variable.

            Expected Result: The instance variable for the expiration date is returned.
        """
        self.assertEqual('_expiration_date', JWToken._map_payload_field_to_instance_var('exp'))

    def test_map_payload_field_to_instance_var_unmapped(self):
        """
            Test that payload field that is not in the map is returned as the instance variable.

            Expected Result: The name of the payload field is returned unchanged.
        """
        payload_field = 'part_of_the_payload'
        self.assertNotIn(payload_field, JWToken._instance_var_payload_field_mapping.inv)
        self.assertEqual(payload_field, JWToken._map_payload_field_to_instance_var(payload_field))

    def test_str(self):
        """
            Test converting the object to a string.

            Expected Result: The token is returned as if `create()` had been called.
        """
        jwtoken = JWToken()
        self.assertEqual(jwtoken.create(), str(jwtoken))


class InheritedJWTokenTest(TestCase):
    """
        Test that the JWToken objects work as intended by subclassing it and simply defining some payload fields.
    """

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.app.config['TOKEN_VALIDITY'] = 600

    def tearDown(self):
        """
            Reset the test cases.
        """
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_create_verify_success(self):
        """
            Test creating and verifying a token with some field defined in a sub class.

            Expected Result: All public fields are restored correctly, private fields are not. The default fields
                             are restored as well.
        """
        jwtoken_creation = InheritedJWToken(300)

        self.assertIsNotNone(jwtoken_creation)
        self.assertEqual(300, jwtoken_creation._validity)
        self.assertIsNone(jwtoken_creation.user_id)
        self.assertIsNone(jwtoken_creation.name)
        self.assertIsNone(jwtoken_creation.complex_field)
        self.assertIsNone(jwtoken_creation._hidden_field)

        jwtoken_creation.user_id = 42
        jwtoken_creation.name = 'Arthur Dent'
        jwtoken_creation.complex_field = dict(
            list_field=[1, 'b', 3.4],
            int_field=5,
            string_field='f',
            float_field=7.8
        )
        jwtoken_creation._hidden_field = 'Heart of Gold'

        token = jwtoken_creation.create()
        self.assertIsNotNone(token)

        jwtoken_verification = InheritedJWToken.verify(token)

        self.assertIsNotNone(jwtoken_verification)
        self.assertEqual(jwtoken_creation.user_id, jwtoken_verification.user_id)
        self.assertEqual(jwtoken_creation.name, jwtoken_verification.name)
        self.assertDictEqual(jwtoken_creation.complex_field, jwtoken_verification.complex_field)
        self.assertIsNone(jwtoken_verification._hidden_field)
        self.assertEqual(jwtoken_creation._token, jwtoken_verification._token)
        self.assertEqual(jwtoken_creation._expiration_date, jwtoken_verification._expiration_date)
        self.assertEqual(jwtoken_creation._validity, jwtoken_verification._validity)

    def test_create_verify_failure_wrong_class(self):
        """
            Test creating and verifying a token that is of the wrong class.

            Expected Result: The token is not restored.
        """
        jwtoken_creation = JWToken()

        token = jwtoken_creation.create()
        self.assertIsNotNone(token)

        with self.assertRaises(InvalidJWTokenPayloadError) as exception:
            jwtoken_verification = InheritedJWToken.verify(token)

            self.assertIsNone(jwtoken_verification)
            self.assertIn('Wrong class: expected InheritedJWToken, got JWToken', exception)

    def test_reset(self):
        """
            Test that resetting does not delete the payload.

            Expected Result: The payload values is left as is.
        """
        user_id = 42
        name = 'Arthur Dent'
        complex_field = dict(
            list_field=[1, 'b', 3.4],
            int_field=5,
            string_field='f',
            float_field=7.8
        )

        jwtoken = InheritedJWToken()
        jwtoken.user_id = user_id
        jwtoken.name = name
        jwtoken.complex_field = complex_field

        jwtoken.create()
        jwtoken.reset()

        self.assertIsNone(jwtoken._token)
        self.assertIsNone(jwtoken._expiration_date)
        self.assertIsNotNone(jwtoken._jwtoken_class)
        self.assertEqual(user_id, jwtoken.user_id)
        self.assertEqual(name, jwtoken.name)
        self.assertDictEqual(complex_field, jwtoken.complex_field)

    def test_get_class_name(self):
        """
            Test getting the name of the class.

            Expected Result: 'InheritedJWToken' is returned.
        """
        jwtoken = InheritedJWToken()
        self.assertEqual('InheritedJWToken', jwtoken._get_class_name())


class InheritedJWToken(JWToken):
    """
        A simple child class of a :class:`.JWToken` to check that the inheritance works correctly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.user_id = None
        self.name = None
        self.complex_field = None
        self._hidden_field = None
