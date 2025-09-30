import 'package:aquaroot/Authetication/loginScreen.dart';
import 'package:aquaroot/other_screens/change_language.dart';
import 'package:aquaroot/other_screens/farm_info.dart';
import 'package:aquaroot/other_screens/personalinfo.dart';
import 'package:aquaroot/other_screens/security_settings.dart';
import 'package:aquaroot/other_screens/support.dart';
import 'package:aquaroot/themes/theme_provider.dart';
import 'package:flutter/cupertino.dart';
import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:provider/provider.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Map<String, dynamic>? _userData;

  @override
  void initState() {
    super.initState();
    _fetchUserData();
  }

  Future<void> _fetchUserData() async {
    try {
      User? user = FirebaseAuth.instance.currentUser;
      if (user != null) {
        DocumentSnapshot doc = await FirebaseFirestore.instance
            .collection('customers')
            .doc(user.uid)
            .get();

        if (doc.exists) {
          setState(() {
            _userData = doc.data() as Map<String, dynamic>;
          });
        }
      }
    } catch (e) {
      print("Error fetching user data: $e");
    }
  }

  @override
  Widget build(BuildContext context) {
    final themeProvider = Provider.of<ThemeProvider>(context);

    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Profile',
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
        ),
        backgroundColor: Colors.grey[100],
        elevation: 0,
      ),
      body: _userData == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  /// --- Profile Header Card ---
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: _cardDecoration(),
                    child: Row(
                      children: [
                        CircleAvatar(
                          radius: 32,
                          backgroundColor: Colors.blueAccent.withOpacity(0.2),
                          child: const Icon(
                            Icons.person,
                            size: 40,
                            color: Colors.blueAccent,
                          ),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                _userData!['userName'] ?? 'User',
                                style: const TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _userData!['email'] ?? 'Email not provided',
                                style: const TextStyle(
                                  color: Colors.black54,
                                  fontSize: 14,
                                ),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                _userData!['phone'] ?? 'Phone not provided',
                                style: const TextStyle(
                                  color: Colors.black54,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  /// --- Settings List ---
                  _buildSettingTile(
                    icon: Icons.nightlight_round,
                    title: "Dark Mode",
                    trailing: CupertinoSwitch(
                      value: themeProvider.isDarkMode,
                      onChanged: (value) => themeProvider.toggleTheme(value),
                    ),
                  ),
                  _buildSettingTile(
                    icon: Icons.person,
                    title: "Personal details",
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PersonalDetails(),
                      ),
                    ),
                  ),
                  _buildSettingTile(
                    icon: Icons.agriculture,
                    title: "Farm Info",
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => FarmInfo()),
                    ),
                  ),
                  _buildSettingTile(
                    icon: Icons.language,
                    title: "Language",
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => ChangeLanguage()),
                    ),
                  ),
                  _buildSettingTile(
                    icon: Icons.security,
                    title: "Security",
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => SecuritySettings(),
                      ),
                    ),
                  ),
                  _buildSettingTile(
                    icon: Icons.support_agent,
                    title: "Support",
                    onTap: () => Navigator.push(
                      context,
                      MaterialPageRoute(builder: (context) => Support()),
                    ),
                  ),
                  _buildSettingTile(
                    icon: Icons.logout,
                    title: "Log out",
                    color: Colors.redAccent,
                    onTap: () async {
                      await FirebaseAuth.instance.signOut();
                      Navigator.pushReplacement(
                        context,
                        MaterialPageRoute(builder: (context) => LoginScreen()),
                      );
                    },
                  ),
                ],
              ),
            ),
    );
  }

  /// --- Reusable Setting Tile ---
  Widget _buildSettingTile({
    required IconData icon,
    required String title,
    Color color = Colors.blueAccent,
    Widget? trailing,
    VoidCallback? onTap,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: _cardDecoration(),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: color.withOpacity(0.15),
          child: Icon(icon, color: color),
        ),
        title: Text(
          title,
          style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
        ),
        trailing: trailing ?? const Icon(Icons.arrow_forward_ios, size: 16),
        onTap: onTap,
      ),
    );
  }

  /// --- Card Decoration ---
  BoxDecoration _cardDecoration() {
    return BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      boxShadow: [
        BoxShadow(
          color: Colors.black12.withOpacity(0.05),
          blurRadius: 6,
          spreadRadius: 2,
          offset: const Offset(0, 3),
        ),
      ],
    );
  }
}
