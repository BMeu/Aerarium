#!venv/bin/python
# -*- coding: utf-8 -*-

from unittest import TestCase
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
