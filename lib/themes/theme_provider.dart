import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class ThemeProvider extends ChangeNotifier {
  bool _isDarkMode = false;

  ThemeProvider() {
    _loadTheme(); // Load the theme from shared preferences when the app starts
  }

  bool get isDarkMode => _isDarkMode;

  ThemeData get themeData {
    return _isDarkMode ? ThemeData.dark() : ThemeData.light();
  }

  // Toggle theme and save the preference
  void toggleTheme(bool value) async {
    _isDarkMode = !_isDarkMode;
    notifyListeners();

    // Save the theme preference
    SharedPreferences prefs = await SharedPreferences.getInstance();
    prefs.setBool('isDarkMode', _isDarkMode);
  }

  // Load the saved theme preference
  void _loadTheme() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    _isDarkMode = prefs.getBool('isDarkMode') ?? false;
    notifyListeners(); // Notify listeners once the theme is loaded
  }
}
