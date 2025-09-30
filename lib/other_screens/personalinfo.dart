import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class PersonalDetails extends StatefulWidget {
  const PersonalDetails({super.key});

  @override
  _PersonalDetailsState createState() => _PersonalDetailsState();
}

class _PersonalDetailsState extends State<PersonalDetails> {
  final User? user = FirebaseAuth.instance.currentUser;
  Map<String, dynamic>? agentData;
  bool isEditing = false;
  late TextEditingController phoneController;
  late TextEditingController emailController;
  final bool _isUploading = false;

  @override
  void initState() {
    super.initState();
    phoneController = TextEditingController();
    emailController = TextEditingController();
    fetchAgentData();
  }

  Future<void> fetchAgentData() async {
    if (user != null) {
      DocumentSnapshot doc = await FirebaseFirestore.instance
          .collection('customers')
          .doc(user!.uid)
          .get();
      setState(() {
        agentData = doc.data() as Map<String, dynamic>?;
        phoneController.text = agentData?['phone'] ?? '';
        emailController.text = agentData?['email'] ?? '';
      });
    }
  }

  Future<void> saveChanges() async {
    if (user != null && agentData != null) {
      await FirebaseFirestore.instance
          .collection('customers')
          .doc(user!.uid)
          .update({
            'phone': phoneController.text,
            'email': emailController.text,
          });

      setState(() {
        isEditing = false;
        agentData!['phone'] = phoneController.text;
        agentData!['email'] = emailController.text;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Changes saved successfully')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Personal Details',
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
        ),
        backgroundColor: Colors.grey[100],
        elevation: 0,
        actions: [
          if (!isEditing)
            IconButton(
              icon: const Icon(Icons.edit, color: Colors.blueAccent),
              onPressed: () {
                setState(() => isEditing = true);
              },
            ),
          if (isEditing)
            IconButton(
              icon: const Icon(Icons.save, color: Colors.green),
              onPressed: _isUploading ? null : saveChanges,
            ),
        ],
      ),
      body: agentData == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                children: [
                  /// --- Profile Header ---
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
                          child: Text(
                            agentData!['userName'] ?? 'User',
                            style: const TextStyle(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),

                  /// --- Editable Form ---
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: _cardDecoration(),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        buildEditableField(
                          label: "Phone Number",
                          controller: phoneController,
                        ),
                        const SizedBox(height: 16),
                        buildEditableField(
                          label: "Email Address",
                          controller: emailController,
                        ),
                      ],
                    ),
                  ),

                  /// --- ID Image ---
                  if (agentData!['idImage'] != null) ...[
                    const SizedBox(height: 20),
                    Container(
                      decoration: _cardDecoration(),
                      child: ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.network(
                          agentData!['idImage'],
                          height: 200,
                          width: double.infinity,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  /// --- Reusable Editable Field ---
  Widget buildEditableField({
    required String label,
    required TextEditingController controller,
  }) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            color: Colors.black54,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: controller,
          enabled: isEditing,
          decoration: InputDecoration(
            filled: true,
            fillColor: isEditing ? Colors.white : Colors.grey[100],
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 12,
              vertical: 10,
            ),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(
                color: isEditing ? Colors.blueAccent : Colors.grey.shade300,
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide(color: Colors.grey.shade300),
            ),
          ),
        ),
      ],
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

  @override
  void dispose() {
    phoneController.dispose();
    emailController.dispose();
    super.dispose();
  }
}
