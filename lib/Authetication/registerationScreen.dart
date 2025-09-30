import 'package:aquaroot/Authetication/loginScreen.dart';
import 'package:aquaroot/widgets/bottom_navbar.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class Registerationscreen extends StatefulWidget {
  const Registerationscreen({super.key});

  @override
  State<Registerationscreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<Registerationscreen>
    with SingleTickerProviderStateMixin {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // State
  bool _isLoading = false;
  bool _obscurePwd = true;

  // Email form
  final TextEditingController _userNameEmailCtrl = TextEditingController();
  final TextEditingController _emailCtrl = TextEditingController();
  final TextEditingController _phoneEmailCtrl = TextEditingController();
  final TextEditingController _passwordCtrl = TextEditingController();

  // Phone form
  final TextEditingController _userNamePhoneCtrl = TextEditingController();
  final TextEditingController _phoneCtrl = TextEditingController();
  final TextEditingController _optionalEmailCtrl = TextEditingController();

  // OTP
  String? _verificationId;
  int? _resendToken;

  @override
  void dispose() {
    _userNameEmailCtrl.dispose();
    _emailCtrl.dispose();
    _phoneEmailCtrl.dispose();
    _passwordCtrl.dispose();
    _userNamePhoneCtrl.dispose();
    _phoneCtrl.dispose();
    _optionalEmailCtrl.dispose();
    super.dispose();
  }

  // --------------------------- HELPERS ---------------------------
  void _showSnack(String msg, {Color? color}) {
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: color));
  }

  Future<void> _withLoading(Future<void> Function() fn) async {
    setState(() => _isLoading = true);
    try {
      await fn();
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  String _normalizePhone(String raw) {
    final trimmed = raw.trim().replaceAll(' ', '');
    if (trimmed.startsWith('+')) return trimmed;
    if (trimmed.startsWith('0')) return '+254${trimmed.substring(1)}';
    return '+$trimmed';
  }

  Future<void> _navigateHome() async {
    if (!mounted) return;
    Navigator.pushReplacement(
      context,
      MaterialPageRoute(builder: (_) => const BottomNavBar()),
    );
  }

  // --------------------------- CREATE FARM INFO ---------------------------
  Future<void> _createFarmInfo(String uid) async {
    final farmCollection = FirebaseFirestore.instance.collection('farminfo');

    // Create or update the default farm info for this user
    await farmCollection.doc(uid).set({
      "Humidity": 45,
      "farmSize": "Unknown",
      "irrigationTime": 24,
      "location": "Unknown",
      "soilMoisture": 30,
      "soilTemp": 34,
      "soilType": "Unknown",
      "customerID": uid,
      "createdAt": FieldValue.serverTimestamp(),
    }, SetOptions(merge: true));
  }

  // --------------------------- EMAIL SIGN UP ---------------------------
  Future<void> _signUpWithEmail() async {
    if (_userNameEmailCtrl.text.trim().isEmpty ||
        _emailCtrl.text.trim().isEmpty ||
        _phoneEmailCtrl.text.trim().isEmpty ||
        _passwordCtrl.text.trim().isEmpty) {
      _showSnack("Please fill in all fields");
      return;
    }

    await _withLoading(() async {
      try {
        final uc = await _auth.createUserWithEmailAndPassword(
          email: _emailCtrl.text.trim(),
          password: _passwordCtrl.text.trim(),
        );

        if (!uc.user!.emailVerified) {
          await uc.user!.sendEmailVerification();
        }

        final uid = uc.user!.uid;
        await FirebaseFirestore.instance.collection('customers').doc(uid).set({
          'userName': _userNameEmailCtrl.text.trim(),
          'email': _emailCtrl.text.trim(),
          'phone': _phoneEmailCtrl.text.trim(),
          'createdAt': FieldValue.serverTimestamp(),
          'authProvider': 'email',
        });

        // Create default farm info
        await _createFarmInfo(uid);

        _showSnack("Account created. Verification email sent.");
        await _navigateHome();
      } on FirebaseAuthException catch (e) {
        _showSnack(e.message ?? "Authentication error");
      } on FirebaseException catch (e) {
        _showSnack(e.message ?? "Firestore error");
      } catch (e) {
        _showSnack("Unexpected error: $e");
      }
    });
  }

  // --------------------------- PHONE SIGN UP ---------------------------
  Future<void> _startPhoneVerification() async {
    if (_userNamePhoneCtrl.text.trim().isEmpty ||
        _phoneCtrl.text.trim().isEmpty) {
      _showSnack("Please provide name and phone number");
      return;
    }

    final phone = _normalizePhone(_phoneCtrl.text);

    await _withLoading(() async {
      await _auth.verifyPhoneNumber(
        phoneNumber: phone,
        forceResendingToken: _resendToken,
        verificationCompleted: (PhoneAuthCredential credential) async {
          try {
            final uc = await _auth.signInWithCredential(credential);
            await _createOrUpdateCustomerAfterPhone(uc.user!);
            await _navigateHome();
          } catch (e) {
            _showSnack("Auto verification failed: $e");
          }
        },
        verificationFailed: (FirebaseAuthException e) {
          _showSnack(e.message ?? "Phone verification failed");
        },
        codeSent: (String verificationId, int? resendToken) async {
          _verificationId = verificationId;
          _resendToken = resendToken;
          if (!mounted) return;
          _showOtpSheet();
        },
        codeAutoRetrievalTimeout: (String verificationId) {
          _verificationId = verificationId;
        },
        timeout: const Duration(seconds: 60),
      );
    });
  }

  Future<void> _verifyOtp(String smsCode) async {
    if (_verificationId == null) {
      _showSnack("No verification in progress");
      return;
    }
    await _withLoading(() async {
      try {
        final credential = PhoneAuthProvider.credential(
          verificationId: _verificationId!,
          smsCode: smsCode.trim(),
        );
        final uc = await _auth.signInWithCredential(credential);
        await _createOrUpdateCustomerAfterPhone(uc.user!);
        if (mounted) Navigator.pop(context);
        await _navigateHome();
      } on FirebaseAuthException catch (e) {
        _showSnack(e.message ?? "Invalid code");
      } catch (e) {
        _showSnack("Error verifying code: $e");
      }
    });
  }

  Future<void> _createOrUpdateCustomerAfterPhone(User user) async {
    final docRef = FirebaseFirestore.instance
        .collection('customers')
        .doc(user.uid);
    final snap = await docRef.get();

    await docRef.set({
      'userName': _userNamePhoneCtrl.text.trim(),
      'phone': _normalizePhone(_phoneCtrl.text),
      if (_optionalEmailCtrl.text.trim().isNotEmpty)
        'email': _optionalEmailCtrl.text.trim(),
      'createdAt': FieldValue.serverTimestamp(),
      'authProvider': 'phone',
    }, SetOptions(merge: snap.exists));

    // Create default farm info
    await _createFarmInfo(user.uid);
  }

  // --------------------------- OTP SHEET ---------------------------
  void _showOtpSheet() {
    final otpCtrl = TextEditingController();
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (_) {
        return Padding(
          padding: EdgeInsets.only(
            bottom: MediaQuery.of(context).viewInsets.bottom,
          ),
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  "Enter the 6-digit code",
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: otpCtrl,
                  keyboardType: TextInputType.number,
                  maxLength: 6,
                  decoration: InputDecoration(
                    labelText: "OTP",
                    prefixIcon: const Icon(Icons.sms, color: Colors.blueAccent),
                    counterText: "",
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                ElevatedButton(
                  onPressed: _isLoading ? null : () => _verifyOtp(otpCtrl.text),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                  child: const Text(
                    "Verify & Create Account",
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: _isLoading ? null : _startPhoneVerification,
                  child: const Text("Resend code"),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // --------------------------- BUILD ---------------------------
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[100],
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              children: [
                CircleAvatar(
                  radius: 40,
                  backgroundColor: Colors.blueAccent.withOpacity(0.2),
                  child: const Icon(
                    Icons.person_add,
                    size: 40,
                    color: Colors.blueAccent,
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Create an Account',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Sign up with Email or Phone (OTP)',
                  style: TextStyle(color: Colors.black54),
                ),
                const SizedBox(height: 24),

                DefaultTabController(
                  length: 2,
                  child: Column(
                    children: [
                      Container(
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: const TabBar(
                          indicatorColor: Colors.blueAccent,
                          labelColor: Colors.blueAccent,
                          unselectedLabelColor: Colors.black54,
                          tabs: [
                            Tab(text: 'Email'),
                            Tab(text: 'Phone (OTP)'),
                          ],
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        height: 500,
                        child: TabBarView(
                          children: [
                            // Email form
                            Column(
                              children: [
                                _input(
                                  controller: _userNameEmailCtrl,
                                  label: "User Name",
                                  icon: Icons.person,
                                ),
                                const SizedBox(height: 14),
                                _input(
                                  controller: _emailCtrl,
                                  label: "Email",
                                  icon: Icons.email,
                                  keyboardType: TextInputType.emailAddress,
                                ),
                                const SizedBox(height: 14),
                                _input(
                                  controller: _phoneEmailCtrl,
                                  label: "Phone No",
                                  icon: Icons.phone,
                                  keyboardType: TextInputType.phone,
                                ),
                                const SizedBox(height: 14),
                                _input(
                                  controller: _passwordCtrl,
                                  label: "Password",
                                  icon: Icons.lock,
                                  obscure: _obscurePwd,
                                  suffix: IconButton(
                                    icon: Icon(
                                      _obscurePwd
                                          ? Icons.visibility_off
                                          : Icons.visibility,
                                    ),
                                    onPressed: () => setState(
                                      () => _obscurePwd = !_obscurePwd,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 24),
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                    onPressed: _isLoading
                                        ? null
                                        : _signUpWithEmail,
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.blueAccent,
                                      padding: const EdgeInsets.symmetric(
                                        vertical: 16,
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                    ),
                                    child: Text(
                                      _isLoading
                                          ? 'Please wait...'
                                          : 'Sign Up with Email',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),

                            // Phone form
                            Column(
                              children: [
                                _input(
                                  controller: _userNamePhoneCtrl,
                                  label: "User Name",
                                  icon: Icons.person,
                                ),
                                const SizedBox(height: 14),
                                _input(
                                  controller: _phoneCtrl,
                                  label: "Phone No (e.g. 07xx... or +254...)",
                                  icon: Icons.phone_android,
                                  keyboardType: TextInputType.phone,
                                ),
                                const SizedBox(height: 14),
                                _input(
                                  controller: _optionalEmailCtrl,
                                  label: "Email (optional)",
                                  icon: Icons.alternate_email,
                                  keyboardType: TextInputType.emailAddress,
                                ),
                                const SizedBox(height: 24),
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                    onPressed: _isLoading
                                        ? null
                                        : _startPhoneVerification,
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: Colors.blueAccent,
                                      padding: const EdgeInsets.symmetric(
                                        vertical: 16,
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(12),
                                      ),
                                    ),
                                    child: Text(
                                      _isLoading
                                          ? 'Sending...'
                                          : 'Send OTP & Verify',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),

                const SizedBox(height: 20),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Text(
                      "Already have an account?",
                      style: TextStyle(color: Colors.black54),
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.pushReplacement(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const LoginScreen(),
                          ),
                        );
                      },
                      child: const Text(
                        'Sign In',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // styled input field
  Widget _input({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    bool obscure = false,
    Widget? suffix,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return TextField(
      controller: controller,
      obscureText: obscure,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon, color: Colors.blueAccent),
        suffixIcon: suffix,
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
      ),
    );
  }
}

// import 'package:aquaroot/Authetication/loginScreen.dart';
// import 'package:aquaroot/widgets/bottom_navbar.dart';
// import 'package:cloud_firestore/cloud_firestore.dart';
// import 'package:firebase_auth/firebase_auth.dart';
// import 'package:flutter/material.dart';

// class Registerationscreen extends StatefulWidget {
//   const Registerationscreen({super.key});

//   @override
//   State<Registerationscreen> createState() => _SignupScreenState();
// }

// class _SignupScreenState extends State<Registerationscreen>
//     with SingleTickerProviderStateMixin {
//   final FirebaseAuth _auth = FirebaseAuth.instance;

//   // State
//   bool _isLoading = false;
//   bool _obscurePwd = true;

//   // Email form
//   final TextEditingController _userNameEmailCtrl = TextEditingController();
//   final TextEditingController _emailCtrl = TextEditingController();
//   final TextEditingController _phoneEmailCtrl = TextEditingController();
//   final TextEditingController _passwordCtrl = TextEditingController();

//   // Phone form
//   final TextEditingController _userNamePhoneCtrl = TextEditingController();
//   final TextEditingController _phoneCtrl = TextEditingController();
//   final TextEditingController _optionalEmailCtrl = TextEditingController();

//   // OTP
//   String? _verificationId;
//   int? _resendToken;

//   @override
//   void dispose() {
//     _userNameEmailCtrl.dispose();
//     _emailCtrl.dispose();
//     _phoneEmailCtrl.dispose();
//     _passwordCtrl.dispose();
//     _userNamePhoneCtrl.dispose();
//     _phoneCtrl.dispose();
//     _optionalEmailCtrl.dispose();
//     super.dispose();
//   }

//   // --------------------------- HELPERS ---------------------------
//   void _showSnack(String msg, {Color? color}) {
//     ScaffoldMessenger.of(
//       context,
//     ).showSnackBar(SnackBar(content: Text(msg), backgroundColor: color));
//   }

//   Future<void> _withLoading(Future<void> Function() fn) async {
//     setState(() => _isLoading = true);
//     try {
//       await fn();
//     } finally {
//       if (mounted) setState(() => _isLoading = false);
//     }
//   }

//   String _normalizePhone(String raw) {
//     final trimmed = raw.trim().replaceAll(' ', '');
//     if (trimmed.startsWith('+')) return trimmed;
//     if (trimmed.startsWith('0')) return '+254${trimmed.substring(1)}';
//     return '+$trimmed';
//   }

//   Future<void> _navigateHome() async {
//     if (!mounted) return;
//     Navigator.pushReplacement(
//       context,
//       MaterialPageRoute(builder: (_) => const BottomNavBar()),
//     );
//   }

//   // --------------------------- EMAIL SIGN UP ---------------------------
//   Future<void> _signUpWithEmail() async {
//     if (_userNameEmailCtrl.text.trim().isEmpty ||
//         _emailCtrl.text.trim().isEmpty ||
//         _phoneEmailCtrl.text.trim().isEmpty ||
//         _passwordCtrl.text.trim().isEmpty) {
//       _showSnack("Please fill in all fields");
//       return;
//     }

//     await _withLoading(() async {
//       try {
//         final uc = await _auth.createUserWithEmailAndPassword(
//           email: _emailCtrl.text.trim(),
//           password: _passwordCtrl.text.trim(),
//         );

//         if (!uc.user!.emailVerified) {
//           await uc.user!.sendEmailVerification();
//         }

//         final uid = uc.user!.uid;
//         await FirebaseFirestore.instance.collection('customers').doc(uid).set({
//           'userName': _userNameEmailCtrl.text.trim(),
//           'email': _emailCtrl.text.trim(),
//           'phone': _phoneEmailCtrl.text.trim(),
//           'createdAt': FieldValue.serverTimestamp(),
//           'authProvider': 'email',
//         });

//         _showSnack("Account created. Verification email sent.");
//         await _navigateHome();
//       } on FirebaseAuthException catch (e) {
//         _showSnack(e.message ?? "Authentication error");
//       } on FirebaseException catch (e) {
//         _showSnack(e.message ?? "Firestore error");
//       } catch (e) {
//         _showSnack("Unexpected error: $e");
//       }
//     });
//   }

//   // --------------------------- PHONE SIGN UP ---------------------------
//   Future<void> _startPhoneVerification() async {
//     if (_userNamePhoneCtrl.text.trim().isEmpty ||
//         _phoneCtrl.text.trim().isEmpty) {
//       _showSnack("Please provide name and phone number");
//       return;
//     }

//     final phone = _normalizePhone(_phoneCtrl.text);

//     await _withLoading(() async {
//       await _auth.verifyPhoneNumber(
//         phoneNumber: phone,
//         forceResendingToken: _resendToken,
//         verificationCompleted: (PhoneAuthCredential credential) async {
//           try {
//             final uc = await _auth.signInWithCredential(credential);
//             await _createOrUpdateCustomerAfterPhone(uc.user!);
//             await _navigateHome();
//           } catch (e) {
//             _showSnack("Auto verification failed: $e");
//           }
//         },
//         verificationFailed: (FirebaseAuthException e) {
//           _showSnack(e.message ?? "Phone verification failed");
//         },
//         codeSent: (String verificationId, int? resendToken) async {
//           _verificationId = verificationId;
//           _resendToken = resendToken;
//           if (!mounted) return;
//           _showOtpSheet();
//         },
//         codeAutoRetrievalTimeout: (String verificationId) {
//           _verificationId = verificationId;
//         },
//         timeout: const Duration(seconds: 60),
//       );
//     });
//   }

//   Future<void> _verifyOtp(String smsCode) async {
//     if (_verificationId == null) {
//       _showSnack("No verification in progress");
//       return;
//     }
//     await _withLoading(() async {
//       try {
//         final credential = PhoneAuthProvider.credential(
//           verificationId: _verificationId!,
//           smsCode: smsCode.trim(),
//         );
//         final uc = await _auth.signInWithCredential(credential);
//         await _createOrUpdateCustomerAfterPhone(uc.user!);
//         if (mounted) Navigator.pop(context);
//         await _navigateHome();
//       } on FirebaseAuthException catch (e) {
//         _showSnack(e.message ?? "Invalid code");
//       } catch (e) {
//         _showSnack("Error verifying code: $e");
//       }
//     });
//   }

//   Future<void> _createOrUpdateCustomerAfterPhone(User user) async {
//     final docRef = FirebaseFirestore.instance
//         .collection('customers')
//         .doc(user.uid);
//     final snap = await docRef.get();

//     await docRef.set({
//       'userName': _userNamePhoneCtrl.text.trim(),
//       'phone': _normalizePhone(_phoneCtrl.text),
//       if (_optionalEmailCtrl.text.trim().isNotEmpty)
//         'email': _optionalEmailCtrl.text.trim(),
//       'createdAt': FieldValue.serverTimestamp(),
//       'authProvider': 'phone',
//     }, SetOptions(merge: snap.exists));
//   }

//   // --------------------------- OTP SHEET ---------------------------
//   void _showOtpSheet() {
//     final otpCtrl = TextEditingController();
//     showModalBottomSheet(
//       context: context,
//       isScrollControlled: true,
//       useSafeArea: true,
//       shape: const RoundedRectangleBorder(
//         borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
//       ),
//       builder: (_) {
//         return Padding(
//           padding: EdgeInsets.only(
//             bottom: MediaQuery.of(context).viewInsets.bottom,
//           ),
//           child: Padding(
//             padding: const EdgeInsets.all(20),
//             child: Column(
//               mainAxisSize: MainAxisSize.min,
//               children: [
//                 const Text(
//                   "Enter the 6-digit code",
//                   style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
//                 ),
//                 const SizedBox(height: 12),
//                 TextField(
//                   controller: otpCtrl,
//                   keyboardType: TextInputType.number,
//                   maxLength: 6,
//                   decoration: InputDecoration(
//                     labelText: "OTP",
//                     prefixIcon: const Icon(Icons.sms, color: Colors.blueAccent),
//                     counterText: "",
//                     border: OutlineInputBorder(
//                       borderRadius: BorderRadius.circular(12),
//                     ),
//                   ),
//                 ),
//                 const SizedBox(height: 12),
//                 ElevatedButton(
//                   onPressed: _isLoading ? null : () => _verifyOtp(otpCtrl.text),
//                   style: ElevatedButton.styleFrom(
//                     backgroundColor: Colors.blueAccent,
//                     padding: const EdgeInsets.symmetric(vertical: 14),
//                     shape: RoundedRectangleBorder(
//                       borderRadius: BorderRadius.circular(12),
//                     ),
//                   ),
//                   child: const Text(
//                     "Verify & Create Account",
//                     style: TextStyle(
//                       color: Colors.white,
//                       fontWeight: FontWeight.bold,
//                     ),
//                   ),
//                 ),
//                 const SizedBox(height: 8),
//                 TextButton(
//                   onPressed: _isLoading ? null : _startPhoneVerification,
//                   child: const Text("Resend code"),
//                 ),
//               ],
//             ),
//           ),
//         );
//       },
//     );
//   }

//   // --------------------------- BUILD ---------------------------
//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       backgroundColor: Colors.grey[100],
//       body: SafeArea(
//         child: Center(
//           child: SingleChildScrollView(
//             padding: const EdgeInsets.all(24),
//             child: Column(
//               children: [
//                 CircleAvatar(
//                   radius: 40,
//                   backgroundColor: Colors.blueAccent.withOpacity(0.2),
//                   child: const Icon(
//                     Icons.person_add,
//                     size: 40,
//                     color: Colors.blueAccent,
//                   ),
//                 ),
//                 const SizedBox(height: 12),
//                 const Text(
//                   'Create an Account',
//                   style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
//                 ),
//                 const SizedBox(height: 6),
//                 const Text(
//                   'Sign up with Email or Phone (OTP)',
//                   style: TextStyle(color: Colors.black54),
//                 ),
//                 const SizedBox(height: 24),

//                 DefaultTabController(
//                   length: 2,
//                   child: Column(
//                     children: [
//                       Container(
//                         decoration: BoxDecoration(
//                           color: Colors.white,
//                           borderRadius: BorderRadius.circular(12),
//                         ),
//                         child: const TabBar(
//                           indicatorColor: Colors.blueAccent,
//                           labelColor: Colors.blueAccent,
//                           unselectedLabelColor: Colors.black54,
//                           tabs: [
//                             Tab(text: 'Email'),
//                             Tab(text: 'Phone (OTP)'),
//                           ],
//                         ),
//                       ),
//                       const SizedBox(height: 16),
//                       SizedBox(
//                         height: 500,
//                         child: TabBarView(
//                           children: [
//                             // Email form
//                             Column(
//                               children: [
//                                 _input(
//                                   controller: _userNameEmailCtrl,
//                                   label: "User Name",
//                                   icon: Icons.person,
//                                 ),
//                                 const SizedBox(height: 14),
//                                 _input(
//                                   controller: _emailCtrl,
//                                   label: "Email",
//                                   icon: Icons.email,
//                                   keyboardType: TextInputType.emailAddress,
//                                 ),
//                                 const SizedBox(height: 14),
//                                 _input(
//                                   controller: _phoneEmailCtrl,
//                                   label: "Phone No",
//                                   icon: Icons.phone,
//                                   keyboardType: TextInputType.phone,
//                                 ),
//                                 const SizedBox(height: 14),
//                                 _input(
//                                   controller: _passwordCtrl,
//                                   label: "Password",
//                                   icon: Icons.lock,
//                                   obscure: _obscurePwd,
//                                   suffix: IconButton(
//                                     icon: Icon(
//                                       _obscurePwd
//                                           ? Icons.visibility_off
//                                           : Icons.visibility,
//                                     ),
//                                     onPressed: () => setState(
//                                       () => _obscurePwd = !_obscurePwd,
//                                     ),
//                                   ),
//                                 ),
//                                 const SizedBox(height: 24),
//                                 SizedBox(
//                                   width: double.infinity,
//                                   child: ElevatedButton(
//                                     onPressed: _isLoading
//                                         ? null
//                                         : _signUpWithEmail,
//                                     style: ElevatedButton.styleFrom(
//                                       backgroundColor: Colors.blueAccent,
//                                       padding: const EdgeInsets.symmetric(
//                                         vertical: 16,
//                                       ),
//                                       shape: RoundedRectangleBorder(
//                                         borderRadius: BorderRadius.circular(12),
//                                       ),
//                                     ),
//                                     child: Text(
//                                       _isLoading
//                                           ? 'Please wait...'
//                                           : 'Sign Up with Email',
//                                       style: const TextStyle(
//                                         color: Colors.white,
//                                         fontWeight: FontWeight.bold,
//                                       ),
//                                     ),
//                                   ),
//                                 ),
//                               ],
//                             ),

//                             // Phone form
//                             Column(
//                               children: [
//                                 _input(
//                                   controller: _userNamePhoneCtrl,
//                                   label: "User Name",
//                                   icon: Icons.person,
//                                 ),
//                                 const SizedBox(height: 14),
//                                 _input(
//                                   controller: _phoneCtrl,
//                                   label: "Phone No (e.g. 07xx... or +254...)",
//                                   icon: Icons.phone_android,
//                                   keyboardType: TextInputType.phone,
//                                 ),
//                                 const SizedBox(height: 14),
//                                 _input(
//                                   controller: _optionalEmailCtrl,
//                                   label: "Email (optional)",
//                                   icon: Icons.alternate_email,
//                                   keyboardType: TextInputType.emailAddress,
//                                 ),
//                                 const SizedBox(height: 24),
//                                 SizedBox(
//                                   width: double.infinity,
//                                   child: ElevatedButton(
//                                     onPressed: _isLoading
//                                         ? null
//                                         : _startPhoneVerification,
//                                     style: ElevatedButton.styleFrom(
//                                       backgroundColor: Colors.blueAccent,
//                                       padding: const EdgeInsets.symmetric(
//                                         vertical: 16,
//                                       ),
//                                       shape: RoundedRectangleBorder(
//                                         borderRadius: BorderRadius.circular(12),
//                                       ),
//                                     ),
//                                     child: Text(
//                                       _isLoading
//                                           ? 'Sending...'
//                                           : 'Send OTP & Verify',
//                                       style: const TextStyle(
//                                         color: Colors.white,
//                                         fontWeight: FontWeight.bold,
//                                       ),
//                                     ),
//                                   ),
//                                 ),
//                               ],
//                             ),
//                           ],
//                         ),
//                       ),
//                     ],
//                   ),
//                 ),

//                 const SizedBox(height: 20),
//                 Row(
//                   mainAxisAlignment: MainAxisAlignment.center,
//                   children: [
//                     const Text(
//                       "Already have an account?",
//                       style: TextStyle(color: Colors.black54),
//                     ),
//                     TextButton(
//                       onPressed: () {
//                         Navigator.pushReplacement(
//                           context,
//                           MaterialPageRoute(
//                             builder: (context) => const LoginScreen(),
//                           ),
//                         );
//                       },
//                       child: const Text(
//                         'Sign In',
//                         style: TextStyle(fontWeight: FontWeight.bold),
//                       ),
//                     ),
//                   ],
//                 ),
//               ],
//             ),
//           ),
//         ),
//       ),
//     );
//   }

//   // styled input field
//   Widget _input({
//     required TextEditingController controller,
//     required String label,
//     required IconData icon,
//     bool obscure = false,
//     Widget? suffix,
//     TextInputType keyboardType = TextInputType.text,
//   }) {
//     return TextField(
//       controller: controller,
//       obscureText: obscure,
//       keyboardType: keyboardType,
//       decoration: InputDecoration(
//         labelText: label,
//         prefixIcon: Icon(icon, color: Colors.blueAccent),
//         suffixIcon: suffix,
//         filled: true,
//         fillColor: Colors.white,
//         border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
//       ),
//     );
//   }
// }
