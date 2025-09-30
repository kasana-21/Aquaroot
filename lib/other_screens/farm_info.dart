import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class FarmInfo extends StatefulWidget {
  const FarmInfo({super.key});

  @override
  _FarmInfoState createState() => _FarmInfoState();
}

class _FarmInfoState extends State<FarmInfo> {
  final User? user = FirebaseAuth.instance.currentUser;
  Map<String, dynamic>? farmData;
  bool isEditing = false;
  late TextEditingController locationController;
  late TextEditingController farmSizeController;
  late TextEditingController soilTypeController;
  bool _isUploading = false;

  @override
  void initState() {
    super.initState();
    locationController = TextEditingController();
    farmSizeController = TextEditingController();
    soilTypeController = TextEditingController();
    fetchFarmData();
  }

  Future<void> fetchFarmData() async {
    if (user != null) {
      try {
        QuerySnapshot query = await FirebaseFirestore.instance
            .collection('farminfo')
            .where('customerID', isEqualTo: user!.uid)
            .limit(1)
            .get();

        if (query.docs.isNotEmpty) {
          setState(() {
            farmData = query.docs.first.data() as Map<String, dynamic>?;
            locationController.text = farmData?['location'] ?? '';
            farmSizeController.text = farmData?['farmSize'] ?? '';
            soilTypeController.text = farmData?['soilType'] ?? '';
          });
        } else {
          setState(() {
            farmData = {'location': '', 'farmSize': '', 'soilType': ''};
          });
        }
      } catch (e) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error fetching farm data: $e')));
      }
    }
  }

  Future<void> saveChanges() async {
    if (user != null && farmData != null) {
      setState(() => _isUploading = true);
      try {
        QuerySnapshot query = await FirebaseFirestore.instance
            .collection('farminfo')
            .where('customerID', isEqualTo: user!.uid)
            .limit(1)
            .get();

        if (query.docs.isNotEmpty) {
          await FirebaseFirestore.instance
              .collection('farminfo')
              .doc(query.docs.first.id)
              .update({
                'location': locationController.text,
                'farmSize': farmSizeController.text,
                'soilType': soilTypeController.text,
                'customerID': user!.uid,
              });
        } else {
          await FirebaseFirestore.instance.collection('farminfo').add({
            'location': locationController.text,
            'farmSize': farmSizeController.text,
            'soilType': soilTypeController.text,
            'customerID': user!.uid,
            'createdAt': FieldValue.serverTimestamp(),
          });
        }

        setState(() {
          isEditing = false;
          _isUploading = false;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Changes saved successfully')),
        );
      } catch (e) {
        setState(() => _isUploading = false);
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('Error saving changes: $e')));
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      appBar: AppBar(
        title: const Text(
          'Farm Info',
          style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black87),
        ),
        elevation: 0,
        backgroundColor: Colors.grey[100],
        actions: [
          if (!isEditing)
            IconButton(
              icon: const Icon(Icons.edit, color: Colors.blueAccent),
              onPressed: () => setState(() => isEditing = true),
            ),
          if (isEditing)
            IconButton(
              icon: const Icon(Icons.save, color: Colors.green),
              onPressed: _isUploading ? null : saveChanges,
            ),
        ],
      ),
      body: farmData == null
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Container(
                padding: const EdgeInsets.all(20),
                decoration: _cardDecoration(),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    buildEditableField(
                      label: "Location",
                      controller: locationController,
                    ),
                    const SizedBox(height: 16),
                    buildEditableField(
                      label: "Farm Size",
                      controller: farmSizeController,
                    ),
                    const SizedBox(height: 16),
                    buildEditableField(
                      label: "Soil Type",
                      controller: soilTypeController,
                    ),
                  ],
                ),
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
    locationController.dispose();
    farmSizeController.dispose();
    soilTypeController.dispose();
    super.dispose();
  }
}
