import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class ChangeLanguage extends StatefulWidget {
  const ChangeLanguage({super.key});

  @override
  _ChangeLanguageState createState() => _ChangeLanguageState();
}

class _ChangeLanguageState extends State<ChangeLanguage> {
  final User? user = FirebaseAuth.instance.currentUser;
  String? _selectedLanguage = 'English'; // Default to English
  bool _isLoading = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _fetchLanguage();
  }

  Future<void> _fetchLanguage() async {
    if (user != null) {
      try {
        DocumentSnapshot doc = await FirebaseFirestore.instance
            .collection('customers')
            .doc(user!.uid)
            .get();

        if (doc.exists && doc.data() != null) {
          final data = doc.data() as Map<String, dynamic>;
          setState(() {
            _selectedLanguage = data['language'] ?? 'English';
            _isLoading = false;
          });
        } else {
          setState(() {
            _isLoading = false;
          });
        }
      } catch (e) {
        setState(() {
          _isLoading = false;
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error fetching language: $e')));
      }
    } else {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _saveLanguage() async {
    if (user != null && _selectedLanguage != null) {
      setState(() {
        _isSaving = true;
      });
      try {
        await FirebaseFirestore.instance
            .collection('customers')
            .doc(user!.uid)
            .update({
              'language': _selectedLanguage,
              'updatedAt': FieldValue.serverTimestamp(),
            });

        setState(() {
          _isSaving = false;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Language saved successfully')),
        );
      } catch (e) {
        setState(() {
          _isSaving = false;
        });
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error saving language: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Change Language'), elevation: 0),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Center(
              child: SingleChildScrollView(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
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
                          RadioListTile<String>(
                            title: const Text(
                              'English',
                              style: TextStyle(fontSize: 16),
                            ),
                            value: 'English',
                            groupValue: _selectedLanguage,
                            onChanged: (value) {
                              setState(() {
                                _selectedLanguage = value;
                              });
                            },
                            activeColor: Colors.blue[800],
                          ),
                          RadioListTile<String>(
                            title: const Text(
                              'Swahili',
                              style: TextStyle(fontSize: 16),
                            ),
                            value: 'Swahili',
                            groupValue: _selectedLanguage,
                            onChanged: (value) {
                              setState(() {
                                _selectedLanguage = value;
                              });
                            },
                            activeColor: Colors.blue[800],
                          ),
                          const SizedBox(height: 20),
                          ElevatedButton(
                            onPressed: _isSaving ? null : _saveLanguage,
                            style: ElevatedButton.styleFrom(
                              backgroundColor: Colors.blue[800],
                              padding: const EdgeInsets.symmetric(
                                horizontal: 40,
                                vertical: 15,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(8),
                              ),
                            ),
                            child: const Text(
                              'Save',
                              style: TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
    );
  }
}
