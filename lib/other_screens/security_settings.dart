import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

class SecuritySettings extends StatefulWidget {
  const SecuritySettings({super.key});

  @override
  _SecuritySettingsState createState() => _SecuritySettingsState();
}

class _SecuritySettingsState extends State<SecuritySettings> {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final TextEditingController currentPasswordController =
      TextEditingController();
  final TextEditingController newPasswordController = TextEditingController();
  final TextEditingController confirmPasswordController =
      TextEditingController();

  Future<void> _showChangePasswordDialog() async {
    bool isLoading = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Change Password'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: currentPasswordController,
                  decoration: const InputDecoration(
                    labelText: 'Current Password',
                    border: OutlineInputBorder(),
                  ),
                  obscureText: true,
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: newPasswordController,
                  decoration: const InputDecoration(
                    labelText: 'New Password',
                    border: OutlineInputBorder(),
                  ),
                  obscureText: true,
                ),
                const SizedBox(height: 10),
                TextField(
                  controller: confirmPasswordController,
                  decoration: const InputDecoration(
                    labelText: 'Confirm New Password',
                    border: OutlineInputBorder(),
                  ),
                  obscureText: true,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                // Clear controllers when dialog is dismissed
                currentPasswordController.clear();
                newPasswordController.clear();
                confirmPasswordController.clear();
                Navigator.pop(context);
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: isLoading
                  ? null
                  : () async {
                      // Input validation
                      if (currentPasswordController.text.trim().isEmpty ||
                          newPasswordController.text.trim().isEmpty ||
                          confirmPasswordController.text.trim().isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Please fill in all fields'),
                          ),
                        );
                        return;
                      }
                      if (newPasswordController.text !=
                          confirmPasswordController.text) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('New passwords do not match'),
                          ),
                        );
                        return;
                      }
                      if (newPasswordController.text.length < 6) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text(
                              'New password must be at least 6 characters',
                            ),
                          ),
                        );
                        return;
                      }

                      setDialogState(() {
                        isLoading = true;
                      });

                      try {
                        User? user = _auth.currentUser;
                        if (user == null) {
                          throw Exception('No user is logged in');
                        }

                        // Reauthenticate user
                        AuthCredential credential =
                            EmailAuthProvider.credential(
                              email: user.email!,
                              password: currentPasswordController.text.trim(),
                            );
                        await user.reauthenticateWithCredential(credential);

                        // Update password
                        await user.updatePassword(
                          newPasswordController.text.trim(),
                        );

                        if (mounted) {
                          // Clear controllers on success
                          currentPasswordController.clear();
                          newPasswordController.clear();
                          confirmPasswordController.clear();
                          Navigator.pop(context); // Close dialog
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Password updated successfully'),
                            ),
                          );
                        }
                      } on FirebaseAuthException catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(
                                e.message ?? 'Authentication error',
                              ),
                            ),
                          );
                        }
                      } catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('An error occurred: $e')),
                          );
                        }
                      } finally {
                        setDialogState(() {
                          isLoading = false;
                        });
                      }
                    },
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.blue,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: isLoading
                  ? const SizedBox(
                      height: 20,
                      width: 20,
                      child: CircularProgressIndicator(color: Colors.white),
                    )
                  : const Text('Save', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    currentPasswordController.dispose();
    newPasswordController.dispose();
    confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Security Settings'), elevation: 0),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Card(
            elevation: 4,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
            ),
            child: Padding(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  GestureDetector(
                    onTap: _showChangePasswordDialog,
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 15.0),
                      child: Row(
                        children: const [
                          Icon(Icons.lock, size: 24, color: Colors.blue),
                          SizedBox(width: 10),
                          Text(
                            'Change Password',
                            style: TextStyle(fontSize: 16),
                          ),
                        ],
                      ),
                    ),
                  ),
                  const Divider(),
                  GestureDetector(
                    onTap: () {
                      // TODO: Implement Manage Login Methods functionality
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text(
                            'Manage Login Methods not implemented yet',
                          ),
                        ),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 15.0),
                      child: Row(
                        children: const [
                          Icon(Icons.login, size: 24, color: Colors.blue),
                          SizedBox(width: 10),
                          Text(
                            'Manage Login Methods',
                            style: TextStyle(fontSize: 16),
                          ),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
