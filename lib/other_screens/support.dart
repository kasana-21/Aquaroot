import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class Support extends StatefulWidget {
  const Support({super.key});

  @override
  _SupportState createState() => _SupportState();
}

class _SupportState extends State<Support> {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final TextEditingController messageController = TextEditingController();

  Future<void> _showContactAdminDialog() async {
    bool isLoading = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: const Text('Contact Admin'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: messageController,
                  decoration: const InputDecoration(
                    labelText: 'Your Message',
                    border: OutlineInputBorder(),
                    hintText: 'Enter your message here',
                  ),
                  maxLines: 4, // Minimum 4 lines
                  minLines: 4,
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                messageController.clear();
                Navigator.pop(context);
              },
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: isLoading
                  ? null
                  : () async {
                      // Input validation
                      if (messageController.text.trim().isEmpty) {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Please enter a message'),
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

                        // Save message to Firestore
                        await FirebaseFirestore.instance
                            .collection('support')
                            .add({
                              'userId': user.uid,
                              'message': messageController.text.trim(),
                              'createdAt': FieldValue.serverTimestamp(),
                            });

                        if (mounted) {
                          messageController.clear();
                          Navigator.pop(context); // Close dialog
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text('Message sent successfully'),
                            ),
                          );
                        }
                      } on FirebaseException catch (e) {
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(
                              content: Text(e.message ?? 'Firestore error'),
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
                  : const Text('Send', style: TextStyle(color: Colors.white)),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    messageController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Support'), elevation: 0),
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
                    onTap: _showContactAdminDialog,
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 15.0),
                      child: Row(
                        children: const [
                          Icon(
                            Icons.support_agent,
                            size: 24,
                            color: Colors.blue,
                          ),
                          SizedBox(width: 10),
                          Text('Contact Admin', style: TextStyle(fontSize: 16)),
                        ],
                      ),
                    ),
                  ),
                  const Divider(),
                  GestureDetector(
                    onTap: () {
                      // TODO: Implement App Manual functionality
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text('App Manual not implemented yet'),
                        ),
                      );
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(vertical: 15.0),
                      child: Row(
                        children: const [
                          Icon(Icons.book, size: 24, color: Colors.blue),
                          SizedBox(width: 10),
                          Text('App Manual', style: TextStyle(fontSize: 16)),
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
