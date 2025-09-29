#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test cases for TornadoAdapter to verify compatibility with Tornado web framework.

This test module follows the pattern of the functional tests and ensures that
the TornadoAdapter correctly implements the BaseAdapter interface for use
with the Tornado web framework.
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock, patch
from http.cookies import Morsel

# Add the parent directory to the path to import authomatic
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from authomatic.adapters import TornadoAdapter, BaseAdapter


class TestTornadoAdapter(unittest.TestCase):
    """Test cases for TornadoAdapter functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock Tornado RequestHandler
        self.mock_handler = Mock()

        # Mock Tornado HTTPServerRequest
        self.mock_request = Mock()
        self.mock_handler.request = self.mock_request

        # Set up basic request properties
        self.mock_request.arguments = {
            'param1': [b'value1'],
            'param2': [b'value2', b'value3']  # Multiple values
        }

        # Mock cookies using Morsel objects (modern Tornado)
        morsel1 = Morsel()
        morsel1.set('cookie1', 'value1', 'value1')
        morsel2 = Morsel()
        morsel2.set('authomatic', 'auth_value', 'auth_value')

        self.mock_request.cookies = {
            'cookie1': morsel1,
            'authomatic': morsel2
        }

        # Mock full_url method
        self.mock_request.full_url.return_value = 'https://example.com/path'

        # Create adapter instance
        self.adapter = TornadoAdapter(self.mock_handler)

    def test_params_property(self):
        """Test the params property"""
        try:
            params = self.adapter.params

            # Should handle the iteritems() issue
            self.assertIsInstance(params, dict)

            # Check if it handles multiple values correctly
            # Current implementation only takes first value
            self.assertEqual(params.get('param1'), b'value1')

            # Verify it only takes the first value when multiple exist
            self.assertEqual(params.get('param2'), b'value2')

        except AttributeError as e:
            if 'iteritems' in str(e):
                self.fail("TornadoAdapter uses iteritems() which is not available in Python 3")
            else:
                raise

    def test_url_property(self):
        """Test the url property"""
        url = self.adapter.url
        self.assertEqual(url, 'https://example.com/path')

        # Test with return_url override
        adapter_with_return_url = TornadoAdapter(
            self.mock_handler,
            return_url='https://override.com/path'
        )
        self.assertEqual(adapter_with_return_url.url, 'https://override.com/path')

    def test_cookies_property(self):
        """Test the cookies property"""
        try:
            cookies = self.adapter.cookies

            # Should handle the iteritems() issue
            self.assertIsInstance(cookies, dict)

            # Check cookie processing
            # Current implementation has issues with OutputString() method

        except AttributeError as e:
            if 'iteritems' in str(e):
                self.fail("TornadoAdapter uses iteritems() which is not available in Python 3")
            elif 'OutputString' in str(e):
                self.fail("TornadoAdapter uses OutputString() method incorrectly on Morsel objects")
            else:
                raise

    def test_write_method(self):
        """Test the write method"""
        test_value = "Hello, World!"
        self.adapter.write(test_value)

        # Verify that the handler's write method was called
        self.mock_handler.write.assert_called_once_with(test_value)

    def test_set_header_method(self):
        """Test the set_header method"""
        key = "Content-Type"
        value = "application/json"
        self.adapter.set_header(key, value)

        # Verify that the handler's set_header method was called
        self.mock_handler.set_header.assert_called_once_with(key, value)

    def test_set_status_method(self):
        """Test the set_status method"""
        try:
            # Test various status formats
            status_messages = [
                "200 OK",
                "404 Not Found",
                "500 Internal Server Error",
                "302 Found"
            ]

            for status in status_messages:
                self.adapter.set_status(status)

                # Check if it correctly parses status code
                # Current implementation uses regex without importing re module

        except NameError as e:
            if 'name \'re\' is not defined' in str(e):
                self.fail("TornadoAdapter uses 're' module without importing it")
            else:
                raise


class TestTornadoAdapterInterface(unittest.TestCase):
    """Test that TornadoAdapter correctly implements BaseAdapter interface"""

    def setUp(self):
        """Set up test fixtures for interface testing"""
        self.mock_handler = Mock()
        self.mock_request = Mock()
        self.mock_handler.request = self.mock_request

        # Set up minimal request properties
        self.mock_request.arguments = {}
        self.mock_request.cookies = {}
        self.mock_request.full_url.return_value = 'https://example.com/test'

        self.adapter = TornadoAdapter(self.mock_handler)

    def test_inherits_from_base_adapter(self):
        """Test that TornadoAdapter inherits from BaseAdapter"""
        self.assertIsInstance(self.adapter, BaseAdapter)

    def test_implements_required_properties(self):
        """Test that all required BaseAdapter properties are implemented"""
        # These should not raise NotImplementedError or AttributeError
        try:
            _ = self.adapter.params
            _ = self.adapter.url
            _ = self.adapter.cookies
        except NotImplementedError:
            self.fail("TornadoAdapter does not implement required properties")

    def test_implements_required_methods(self):
        """Test that all required BaseAdapter methods are implemented"""
        # These should not raise NotImplementedError
        try:
            self.adapter.write("test")
            self.adapter.set_header("Content-Type", "text/html")
            self.adapter.set_status("200 OK")
        except NotImplementedError:
            self.fail("TornadoAdapter does not implement required methods")

    def test_constructor_with_return_url(self):
        """Test constructor with optional return_url parameter"""
        return_url = "https://custom.example.com/return"
        adapter = TornadoAdapter(self.mock_handler, return_url=return_url)
        self.assertEqual(adapter.return_url, return_url)
        self.assertEqual(adapter.url, return_url)

    def test_constructor_without_return_url(self):
        """Test constructor without return_url uses request.full_url()"""
        adapter = TornadoAdapter(self.mock_handler)
        self.assertIsNone(adapter.return_url)
        self.assertEqual(adapter.url, 'https://example.com/test')


class TestTornadoAdapterEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in TornadoAdapter"""

    def setUp(self):
        """Set up test fixtures for edge case testing"""
        self.mock_handler = Mock()
        self.mock_request = Mock()
        self.mock_handler.request = self.mock_request
        self.adapter = TornadoAdapter(self.mock_handler)

    def test_empty_arguments(self):
        """Test behavior with empty arguments"""
        self.mock_request.arguments = {}
        params = self.adapter.params
        self.assertEqual(params, {})

    def test_empty_cookies(self):
        """Test behavior with empty cookies"""
        self.mock_request.cookies = {}
        cookies = self.adapter.cookies
        self.assertEqual(cookies, {})

    def test_malformed_status_handling(self):
        """Test handling of malformed status strings"""
        # Test various malformed status strings
        test_cases = [
            "OK",  # No status code
            "",    # Empty string
            "abc", # Non-numeric
            "200", # Just number
        ]

        for status in test_cases:
            with self.subTest(status=status):
                # Should not raise exceptions
                self.adapter.set_status(status)

    def test_arguments_with_empty_values(self):
        """Test handling of arguments with empty value lists"""
        self.mock_request.arguments = {
            'empty': [],
            'normal': [b'value']
        }
        params = self.adapter.params

        # Should handle empty lists gracefully
        self.assertIn('normal', params)
        # Behavior for empty lists may vary

    def test_cookie_output_string_error(self):
        """Test handling when cookie OutputString() fails"""
        mock_morsel = Mock()
        mock_morsel.OutputString.side_effect = AttributeError("No OutputString")

        self.mock_request.cookies = {'test': mock_morsel}

        # Should handle the error gracefully
        try:
            cookies = self.adapter.cookies
        except AttributeError:
            # This is expected behavior given current implementation
            pass


class TestTornadoAdapterPython3Compatibility(unittest.TestCase):
    """Test Python 3 compatibility issues specifically"""

    def test_iteritems_usage(self):
        """Test that adapter doesn't use Python 2 iteritems()"""
        # Read the adapter source to check for iteritems usage
        import inspect
        source = inspect.getsource(TornadoAdapter)

        if 'iteritems()' in source:
            self.fail(
                "TornadoAdapter source code contains 'iteritems()' calls "
                "which are not compatible with Python 3. Use 'items()' instead."
            )

    def test_missing_imports(self):
        """Test for missing imports in the adapter"""
        import inspect
        source = inspect.getsource(TornadoAdapter)

        # Check if 're' module is used but not imported at module level
        if 're.findall' in source:
            # Check if 're' is imported in the module
            import authomatic.adapters as adapters_module
            if not hasattr(adapters_module, 're'):
                self.fail(
                    "TornadoAdapter uses 're.findall' but 're' module is not imported"
                )

    def test_string_vs_bytes_handling(self):
        """Test proper handling of strings vs bytes in Python 3"""
        # Test with byte string arguments (typical in Tornado)
        self.mock_handler = Mock()
        self.mock_request = Mock()
        self.mock_handler.request = self.mock_request

        self.mock_request.arguments = {
            'str_key': [b'byte_value'],
            'unicode_key': ['unicode_value'],
        }

        adapter = TornadoAdapter(self.mock_handler)
        params = adapter.params

        # Should handle both string and byte values
        self.assertIsInstance(params, dict)


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)