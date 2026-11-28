"""Checks for global theme and accessibility CSS generation."""

import unittest

from utils.app_settings import settings_css


class AppSettingsTests(unittest.TestCase):
    def test_dark_theme_contains_dark_palette(self):
        css = settings_css("Dark", "Standard", False)
        self.assertIn("#171219", css)
        self.assertIn("color-scheme: dark", css)

    def test_light_theme_and_large_text(self):
        css = settings_css("Light", "Large", False)
        self.assertIn("color-scheme: light", css)
        self.assertIn("font-size: 1.12rem", css)

    def test_reduced_motion_disables_long_transitions(self):
        css = settings_css("Light", "Compact", True)
        self.assertIn("transition-duration: 0.001ms", css)
        self.assertIn("font-size: 0.94rem", css)

    def test_unknown_setting_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Theme"):
            settings_css("Blue", "Standard", False)
        with self.assertRaisesRegex(ValueError, "text size"):
            settings_css("Light", "Huge", False)


if __name__ == "__main__":
    unittest.main()
