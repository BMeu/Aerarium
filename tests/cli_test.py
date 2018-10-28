#!venv/bin/python
# -*- coding: utf-8 -*-

from time import sleep

from unittest import TestCase
from unittest.mock import call
from unittest.mock import MagicMock
from unittest.mock import patch

from app import cli
from app import create_app
from app.configuration import TestConfiguration


class CLITest(TestCase):

    def setUp(self):
        """
            Initialize the test cases.
        """
        self.app = create_app(TestConfiguration)
        cli.register(self.app)

        self.cli = self.app.test_cli_runner()

    @patch('app.cli.generate_password_hash')
    def test_pw_hash_rounds_minimum_too_long(self, mock_hasher: MagicMock):
        """
            Test that the minimum value is returned if the requested maximum time is too short for it.

            Expected result: The output suggests the value 4 and informs the user that the minimum value must be used.
        """
        def _hasher_side_effect(_password, rounds):
            """
                Sleep slightly longer than the number of rounds in milliseconds.
            """
            sleep((rounds + 1) / 1000.0)

        mock_hasher.side_effect = _hasher_side_effect

        response = self.cli.invoke(args=['pw_hash_rounds', '4'])
        output = response.output

        mock_hasher.assert_called_once_with('Aerarium', 4)
        self.assertIn('The minimum number of rounds took more time than allowed.', output)
        self.assertIn('However, the number of rounds must be at least: 4', output)
        self.assertNotIn('Found suiting number of hashing rounds', output)
        self.assertIn('BCRYPT_LOG_ROUNDS=4', output)
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.generate_password_hash')
    def test_pw_hash_rounds_minimum_ok(self, mock_hasher: MagicMock):
        """
            Test that the minimum value is returned if the requested maximum time fits.

            Expected result: The output suggests the value 4 and informs the user that the minimum value is fitting the
                             requirements.
        """
        def _hasher_side_effect(_password, rounds):
            """
                Sleep slightly shorter than the number of rounds in milliseconds.
            """
            sleep((rounds - 1) / 1000.0)

        mock_hasher.side_effect = _hasher_side_effect

        response = self.cli.invoke(args=['pw_hash_rounds', '4'])
        output = response.output

        self.assertEqual(2, mock_hasher.call_count)
        self.assertTupleEqual(call('Aerarium', 4), mock_hasher.call_args_list[0])
        self.assertTupleEqual(call('Aerarium', 5), mock_hasher.call_args_list[1])
        self.assertNotIn('| Duration', output)
        self.assertNotIn('Reached maximum number of hashing rounds.', output)
        self.assertNotIn('The minimum number of rounds took more time than allowed.', output)
        self.assertNotIn('However, the number of rounds must be at least', output)
        self.assertIn('Found suiting number of hashing rounds: 4', output)
        self.assertIn('BCRYPT_LOG_ROUNDS=4', output)
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.generate_password_hash')
    def test_pw_hash_rounds_medium_value_verbose(self, mock_hasher: MagicMock):
        """
            Test a medium value is returned if the requested maximum time fits.

            Expected result: The output suggests the value 12 and displays verbose information.
        """
        def _hasher_side_effect(_password, rounds):
            """
                Sleep slightly shorter than the number of rounds in milliseconds.
            """
            sleep((rounds - 1) / 1000.0)

        mock_hasher.side_effect = _hasher_side_effect

        response = self.cli.invoke(args=['pw_hash_rounds', '-v', '12'])
        output = response.output

        self.assertEqual(10, mock_hasher.call_count)
        self.assertTupleEqual(call('Aerarium', 4), mock_hasher.call_args_list[0])
        self.assertTupleEqual(call('Aerarium', 5), mock_hasher.call_args_list[1])
        self.assertTupleEqual(call('Aerarium', 6), mock_hasher.call_args_list[2])
        self.assertTupleEqual(call('Aerarium', 7), mock_hasher.call_args_list[3])
        self.assertTupleEqual(call('Aerarium', 8), mock_hasher.call_args_list[4])
        self.assertTupleEqual(call('Aerarium', 9), mock_hasher.call_args_list[5])
        self.assertTupleEqual(call('Aerarium', 10), mock_hasher.call_args_list[6])
        self.assertTupleEqual(call('Aerarium', 11), mock_hasher.call_args_list[7])
        self.assertTupleEqual(call('Aerarium', 12), mock_hasher.call_args_list[8])
        self.assertTupleEqual(call('Aerarium', 13), mock_hasher.call_args_list[9])
        self.assertIn('| Duration', output)
        self.assertNotIn('Reached maximum number of hashing rounds.', output)
        self.assertNotIn('The minimum number of rounds took more time than allowed.', output)
        self.assertNotIn('However, the number of rounds must be at least', output)
        self.assertIn('Found suiting number of hashing rounds: 12', output)
        self.assertIn('BCRYPT_LOG_ROUNDS=12', output)
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.generate_password_hash')
    def test_pw_hash_rounds_maximum_value(self, mock_hasher: MagicMock):
        """
            Test that the maximum value is returned if the requested maximum time is too long

            Expected result: The output suggests the value 31.
        """
        def _hasher_side_effect(_password, rounds):
            """
                Sleep slightly shorter than the number of rounds in milliseconds.
            """
            sleep((rounds - 1) / 1000.0)

        mock_hasher.side_effect = _hasher_side_effect

        response = self.cli.invoke(args=['pw_hash_rounds', '32'])
        output = response.output

        self.assertEqual(28, mock_hasher.call_count)
        self.assertTupleEqual(call('Aerarium', 4), mock_hasher.call_args_list[0])
        self.assertTupleEqual(call('Aerarium', 5), mock_hasher.call_args_list[1])
        self.assertTupleEqual(call('Aerarium', 6), mock_hasher.call_args_list[2])
        self.assertTupleEqual(call('Aerarium', 7), mock_hasher.call_args_list[3])
        self.assertTupleEqual(call('Aerarium', 8), mock_hasher.call_args_list[4])
        self.assertTupleEqual(call('Aerarium', 9), mock_hasher.call_args_list[5])
        self.assertTupleEqual(call('Aerarium', 10), mock_hasher.call_args_list[6])
        self.assertTupleEqual(call('Aerarium', 11), mock_hasher.call_args_list[7])
        self.assertTupleEqual(call('Aerarium', 12), mock_hasher.call_args_list[8])
        self.assertTupleEqual(call('Aerarium', 13), mock_hasher.call_args_list[9])
        self.assertTupleEqual(call('Aerarium', 14), mock_hasher.call_args_list[10])
        self.assertTupleEqual(call('Aerarium', 15), mock_hasher.call_args_list[11])
        self.assertTupleEqual(call('Aerarium', 16), mock_hasher.call_args_list[12])
        self.assertTupleEqual(call('Aerarium', 17), mock_hasher.call_args_list[13])
        self.assertTupleEqual(call('Aerarium', 18), mock_hasher.call_args_list[14])
        self.assertTupleEqual(call('Aerarium', 19), mock_hasher.call_args_list[15])
        self.assertTupleEqual(call('Aerarium', 20), mock_hasher.call_args_list[16])
        self.assertTupleEqual(call('Aerarium', 21), mock_hasher.call_args_list[17])
        self.assertTupleEqual(call('Aerarium', 22), mock_hasher.call_args_list[18])
        self.assertTupleEqual(call('Aerarium', 23), mock_hasher.call_args_list[19])
        self.assertTupleEqual(call('Aerarium', 24), mock_hasher.call_args_list[20])
        self.assertTupleEqual(call('Aerarium', 25), mock_hasher.call_args_list[21])
        self.assertTupleEqual(call('Aerarium', 26), mock_hasher.call_args_list[22])
        self.assertTupleEqual(call('Aerarium', 27), mock_hasher.call_args_list[23])
        self.assertTupleEqual(call('Aerarium', 28), mock_hasher.call_args_list[24])
        self.assertTupleEqual(call('Aerarium', 29), mock_hasher.call_args_list[25])
        self.assertTupleEqual(call('Aerarium', 30), mock_hasher.call_args_list[26])
        self.assertTupleEqual(call('Aerarium', 31), mock_hasher.call_args_list[27])
        self.assertNotIn('| Duration', output)
        self.assertNotIn('Reached maximum number of hashing rounds.', output)
        self.assertNotIn('The minimum number of rounds took more time than allowed.', output)
        self.assertNotIn('However, the number of rounds must be at least', output)
        self.assertIn('Found suiting number of hashing rounds: 31', output)
        self.assertIn('BCRYPT_LOG_ROUNDS=31', output)
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.generate_password_hash')
    def test_pw_hash_rounds_maximum_value_verbose(self, mock_hasher: MagicMock):
        """
            Test that the maximum value is returned if the requested maximum time is too long, and test verbose output.

            Expected result: The output suggests the value 31 and informs the user about the maximum number, since
                             verbose output is enabled.
        """
        def _hasher_side_effect(_password, rounds):
            """
                Sleep slightly shorter than the number of rounds in milliseconds.
            """
            sleep((rounds - 1) / 1000.0)

        mock_hasher.side_effect = _hasher_side_effect

        response = self.cli.invoke(args=['pw_hash_rounds', '-v', '32'])
        output = response.output

        self.assertEqual(28, mock_hasher.call_count)
        self.assertTupleEqual(call('Aerarium', 4), mock_hasher.call_args_list[0])
        self.assertTupleEqual(call('Aerarium', 5), mock_hasher.call_args_list[1])
        self.assertTupleEqual(call('Aerarium', 6), mock_hasher.call_args_list[2])
        self.assertTupleEqual(call('Aerarium', 7), mock_hasher.call_args_list[3])
        self.assertTupleEqual(call('Aerarium', 8), mock_hasher.call_args_list[4])
        self.assertTupleEqual(call('Aerarium', 9), mock_hasher.call_args_list[5])
        self.assertTupleEqual(call('Aerarium', 10), mock_hasher.call_args_list[6])
        self.assertTupleEqual(call('Aerarium', 11), mock_hasher.call_args_list[7])
        self.assertTupleEqual(call('Aerarium', 12), mock_hasher.call_args_list[8])
        self.assertTupleEqual(call('Aerarium', 13), mock_hasher.call_args_list[9])
        self.assertTupleEqual(call('Aerarium', 14), mock_hasher.call_args_list[10])
        self.assertTupleEqual(call('Aerarium', 15), mock_hasher.call_args_list[11])
        self.assertTupleEqual(call('Aerarium', 16), mock_hasher.call_args_list[12])
        self.assertTupleEqual(call('Aerarium', 17), mock_hasher.call_args_list[13])
        self.assertTupleEqual(call('Aerarium', 18), mock_hasher.call_args_list[14])
        self.assertTupleEqual(call('Aerarium', 19), mock_hasher.call_args_list[15])
        self.assertTupleEqual(call('Aerarium', 20), mock_hasher.call_args_list[16])
        self.assertTupleEqual(call('Aerarium', 21), mock_hasher.call_args_list[17])
        self.assertTupleEqual(call('Aerarium', 22), mock_hasher.call_args_list[18])
        self.assertTupleEqual(call('Aerarium', 23), mock_hasher.call_args_list[19])
        self.assertTupleEqual(call('Aerarium', 24), mock_hasher.call_args_list[20])
        self.assertTupleEqual(call('Aerarium', 25), mock_hasher.call_args_list[21])
        self.assertTupleEqual(call('Aerarium', 26), mock_hasher.call_args_list[22])
        self.assertTupleEqual(call('Aerarium', 27), mock_hasher.call_args_list[23])
        self.assertTupleEqual(call('Aerarium', 28), mock_hasher.call_args_list[24])
        self.assertTupleEqual(call('Aerarium', 29), mock_hasher.call_args_list[25])
        self.assertTupleEqual(call('Aerarium', 30), mock_hasher.call_args_list[26])
        self.assertTupleEqual(call('Aerarium', 31), mock_hasher.call_args_list[27])
        self.assertIn('| Duration', output)
        self.assertIn('Reached maximum number of hashing rounds.', output)
        self.assertNotIn('The minimum number of rounds took more time than allowed.', output)
        self.assertNotIn('However, the number of rounds must be at least', output)
        self.assertIn('Found suiting number of hashing rounds: 31', output)
        self.assertIn('BCRYPT_LOG_ROUNDS=31', output)
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.os.system')
    def test_translate_compile_success(self, mock_system: MagicMock):
        """
            Test the Babel compile call.

            Expected result: Babel is instructed to compile the translations.
        """
        mock_system.return_value = 0

        response = self.cli.invoke(args=['translate', 'compile'])

        mock_system.assert_called_once()
        self.assertIn('babel compile', str(mock_system.call_args))
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.os.system')
    def test_translate_compile_failure(self, mock_system: MagicMock):
        """
            Test the Babel compile call.

            Expected result: Babel is instructed to compile the translations, but fails.
        """
        mock_system.return_value = 1

        response = self.cli.invoke(args=['translate', 'compile'])

        mock_system.assert_called_once()
        self.assertIn('babel compile', str(mock_system.call_args))
        self.assertIn('Compilation failed', response.output)
        self.assertEqual(1, response.exit_code)

    @patch('app.cli.os.remove')
    @patch('app.cli.os.system')
    def test_translate_extract_failure(self, mock_system: MagicMock, mock_remove: MagicMock):
        """
            Test the Babel extract call.

            This can only be tested via a CLI call since the extract function is defined within the register function.

            Expected result: Babel is instructed to extract the translations, but fails.
        """
        def _system_return_value(value):
            """
                Only fail the extract command.
            """
            if 'extract' in value:
                return 1
            return 0

        mock_system.side_effect = _system_return_value

        response = self.cli.invoke(args=['translate', 'init', 'de'])

        mock_remove.assert_not_called()
        mock_system.assert_called_once()
        self.assertIn('babel extract', str(mock_system.call_args))
        self.assertIn('Extraction failed', response.output)
        self.assertEqual(1, response.exit_code)

    @patch('app.cli.os.remove')
    @patch('app.cli.os.system')
    def test_translate_init_success(self, mock_system: MagicMock, mock_remove: MagicMock):
        """
            Test the Babel init call.

            Expected result: Babel is instructed to extract and initialize the translations.
        """
        mock_system.return_value = 0

        response = self.cli.invoke(args=['translate', 'init', 'de'])

        mock_remove.assert_called_once()
        mock_system.assert_called()
        self.assertEqual(2, mock_system.call_count)
        self.assertIn('babel extract', str(mock_system.call_args_list[0]))
        self.assertIn('babel init', str(mock_system.call_args_list[1]))
        self.assertIn('-l de', str(mock_system.call_args_list[1]))
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.os.remove')
    @patch('app.cli.os.system')
    def test_translate_init_failure(self, mock_system: MagicMock, mock_remove: MagicMock):
        """
            Test the Babel update call.

            Expected result: Babel is instructed to update the translations, but fails.
        """
        def _system_return_value(value):
            """
                Don't fail the extract command.
            """
            if 'extract' in value:
                return 0
            return 1

        mock_system.side_effect = _system_return_value

        response = self.cli.invoke(args=['translate', 'init', 'de'])

        mock_remove.assert_not_called()
        mock_system.assert_called()
        self.assertIn('babel extract', str(mock_system.call_args_list[0]))
        self.assertIn('babel init', str(mock_system.call_args_list[1]))
        self.assertIn('-l de', str(mock_system.call_args_list[1]))
        self.assertIn('Language initialization failed', response.output)
        self.assertEqual(1, response.exit_code)

    @patch('app.cli.os.remove')
    @patch('app.cli.os.system')
    def test_translate_update_success(self, mock_system: MagicMock, mock_remove: MagicMock):
        """
            Test the Babel update call.

            Expected result: Babel is instructed to extract and update the translations.
        """
        mock_system.return_value = 0

        response = self.cli.invoke(args=['translate', 'update'])

        mock_remove.assert_called_once()
        mock_system.assert_called()
        self.assertEqual(2, mock_system.call_count)
        self.assertIn('babel extract', str(mock_system.call_args_list[0]))
        self.assertIn('babel update', str(mock_system.call_args_list[1]))
        self.assertEqual(0, response.exit_code)

    @patch('app.cli.os.remove')
    @patch('app.cli.os.system')
    def test_translate_update_failure(self, mock_system: MagicMock, mock_remove: MagicMock):
        """
            Test the Babel update call.

            Expected result: Babel is instructed to update the translations, but fails.
        """
        def _system_return_value(value):
            """
                Don't fail the extract command.
            """
            if 'extract' in value:
                return 0
            return 1

        mock_system.side_effect = _system_return_value

        response = self.cli.invoke(args=['translate', 'update'])

        mock_remove.assert_not_called()
        mock_system.assert_called()
        self.assertIn('babel extract', str(mock_system.call_args_list[0]))
        self.assertIn('babel update', str(mock_system.call_args_list[1]))
        self.assertIn('Update failed', response.output)
        self.assertEqual(1, response.exit_code)
