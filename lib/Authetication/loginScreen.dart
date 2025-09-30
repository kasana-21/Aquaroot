// ignore_for_file: unused_local_variable

import 'package:aquaroot/Authetication/registerationScreen.dart';
import 'package:aquaroot/widgets/bottom_navbar.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  _LoginScreenState createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final FirebaseAuth _auth = FirebaseAuth.instance;

  // State
  bool _isLoading = false;
  bool _obscurePwd = true;

  // Email form controllers
  final TextEditingController _emailCtrl = TextEditingController();
  final TextEditingController _passwordCtrl = TextEditingController();

  // Phone form controllers
  final TextEditingController _phoneCtrl = TextEditingController();

  // OTP
  String? _verificationId;
  int? _resendToken;

  @override
  void dispose() {
    _emailCtrl.dispose();
    _passwordCtrl.dispose();
    _phoneCtrl.dispose();
    super.dispose();
  }

  // ----------------- Helpers -----------------
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

  // ----------------- Email Login -----------------
  Future<void> _signInWithEmail() async {
    if (_emailCtrl.text.trim().isEmpty || _passwordCtrl.text.trim().isEmpty) {
      _showSnack("Please fill in all fields");
      return;
    }

    await _withLoading(() async {
      try {
        final uc = await _auth.signInWithEmailAndPassword(
          email: _emailCtrl.text.trim(),
          password: _passwordCtrl.text.trim(),
        );

        if (uc.user != null) {
          await _navigateHome();
        }
      } on FirebaseAuthException catch (e) {
        _showSnack(e.message ?? "Authentication error");
      } catch (e) {
        _showSnack("Unexpected error: $e");
      }
    });
  }

  // ----------------- Phone Login -----------------
  Future<void> _startPhoneLogin() async {
    if (_phoneCtrl.text.trim().isEmpty) {
      _showSnack("Please enter your phone number");
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
            await _navigateHome();
          } catch (e) {
            _showSnack("Auto verification failed: $e");
          }
        },
        verificationFailed: (FirebaseAuthException e) {
          _showSnack(e.message ?? "Phone verification failed");
        },
        codeSent: (String verificationId, int? resendToken) {
          _verificationId = verificationId;
          _resendToken = resendToken;
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
        if (uc.user != null) {
          if (mounted) Navigator.pop(context);
          await _navigateHome();
        }
      } on FirebaseAuthException catch (e) {
        _showSnack(e.message ?? "Invalid code");
      } catch (e) {
        _showSnack("Error verifying code: $e");
      }
    });
  }

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
                    "Verify & Login",
                    style: TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                const SizedBox(height: 8),
                TextButton(
                  onPressed: _isLoading ? null : _startPhoneLogin,
                  child: const Text("Resend code"),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // ----------------- Build -----------------
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
                    Icons.lock,
                    size: 40,
                    color: Colors.blueAccent,
                  ),
                ),
                const SizedBox(height: 12),
                const Text(
                  'Welcome Back',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 6),
                const Text(
                  'Login with Email or Phone (OTP)',
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
                        height: 350,
                        child: TabBarView(
                          children: [
                            // Email login
                            Column(
                              children: [
                                _input(
                                  controller: _emailCtrl,
                                  label: "Email",
                                  icon: Icons.email,
                                  keyboardType: TextInputType.emailAddress,
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
                                      color: Colors.grey,
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
                                        : _signInWithEmail,
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
                                      _isLoading ? 'Signing in...' : 'Sign In',
                                      style: const TextStyle(
                                        color: Colors.white,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ),
                              ],
                            ),

                            // Phone login
                            Column(
                              children: [
                                _input(
                                  controller: _phoneCtrl,
                                  label: "Phone No (e.g. 07xx... or +254...)",
                                  icon: Icons.phone_android,
                                  keyboardType: TextInputType.phone,
                                ),
                                const SizedBox(height: 24),
                                SizedBox(
                                  width: double.infinity,
                                  child: ElevatedButton(
                                    onPressed: _isLoading
                                        ? null
                                        : _startPhoneLogin,
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
                                          ? 'Sending OTP...'
                                          : 'Send OTP & Login',
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
                      "Don’t have an account?",
                      style: TextStyle(color: Colors.black54),
                    ),
                    TextButton(
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => const Registerationscreen(),
                          ),
                        );
                      },
                      child: const Text(
                        'Sign Up',
                        style: TextStyle(fontWeight: FontWeight.bold),
                      ),
                    ),
                  ],
                ),
                TextButton(
                  onPressed: () {
                    // TODO: implement forgot password
                  },
                  child: const Text(
                    'Forgot Password?',
                    style: TextStyle(color: Colors.redAccent),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  // styled input
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


















// import 'package:aquaroot/Authetication/registerationScreen.dart';
// import 'package:aquaroot/widgets/bottom_navbar.dart';
// import 'package:firebase_auth/firebase_auth.dart';
// import 'package:flutter/material.dart';

// class LoginScreen extends StatefulWidget {
//   const LoginScreen({super.key});

//   @override
//   _LoginScreenState createState() => _LoginScreenState();
// }

// class _LoginScreenState extends State<LoginScreen> {
//   final TextEditingController _emailController = TextEditingController();
//   final TextEditingController _passwordController = TextEditingController();
//   final FirebaseAuth _auth = FirebaseAuth.instance;

//   bool _obscurePassword = true;

//   Future<void> _signInWithEmail() async {
//     if (_emailController.text.trim().isEmpty ||
//         _passwordController.text.trim().isEmpty) {
//       ScaffoldMessenger.of(context).showSnackBar(
//         const SnackBar(content: Text("Please fill in all fields")),
//       );
//       return;
//     }

//     try {
//       final UserCredential userCredential = await _auth
//           .signInWithEmailAndPassword(
//             email: _emailController.text.trim(),
//             password: _passwordController.text.trim(),
//           );

//       User? user = userCredential.user;
//       if (user != null) {
//         Navigator.pushReplacement(
//           context,
//           MaterialPageRoute(builder: (context) => const BottomNavBar()),
//         );
//       }
//     } on FirebaseAuthException catch (e) {
//       ScaffoldMessenger.of(
//         context,
//       ).showSnackBar(SnackBar(content: Text(e.message ?? "An error occurred")));
//     }
//   }

//   @override
//   Widget build(BuildContext context) {
//     return Scaffold(
//       backgroundColor: Colors.grey[100],
//       body: Center(
//         child: SingleChildScrollView(
//           padding: const EdgeInsets.all(24),
//           child: Column(
//             crossAxisAlignment: CrossAxisAlignment.center,
//             children: [
//               /// Header Icon
//               CircleAvatar(
//                 radius: 40,
//                 backgroundColor: Colors.blueAccent.withOpacity(0.2),
//                 child: const Icon(
//                   Icons.lock,
//                   size: 40,
//                   color: Colors.blueAccent,
//                 ),
//               ),
//               const SizedBox(height: 16),
//               const Text(
//                 'Welcome Back',
//                 style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
//               ),
//               const SizedBox(height: 6),
//               const Text(
//                 'Sign in to continue managing your farm',
//                 textAlign: TextAlign.center,
//                 style: TextStyle(fontSize: 14, color: Colors.black54),
//               ),
//               const SizedBox(height: 30),

//               /// Email Field
//               _buildTextField(
//                 controller: _emailController,
//                 label: "Email",
//                 icon: Icons.email,
//                 keyboardType: TextInputType.emailAddress,
//               ),
//               const SizedBox(height: 16),

//               /// Password Field with Toggle
//               TextField(
//                 controller: _passwordController,
//                 obscureText: _obscurePassword,
//                 decoration: InputDecoration(
//                   labelText: "Password",
//                   prefixIcon: const Icon(Icons.lock, color: Colors.blueAccent),
//                   suffixIcon: IconButton(
//                     icon: Icon(
//                       _obscurePassword
//                           ? Icons.visibility_off
//                           : Icons.visibility,
//                       color: Colors.grey,
//                     ),
//                     onPressed: () {
//                       setState(() => _obscurePassword = !_obscurePassword);
//                     },
//                   ),
//                   filled: true,
//                   fillColor: Colors.white,
//                   contentPadding: const EdgeInsets.symmetric(
//                     horizontal: 12,
//                     vertical: 14,
//                   ),
//                   border: OutlineInputBorder(
//                     borderRadius: BorderRadius.circular(12),
//                   ),
//                   enabledBorder: OutlineInputBorder(
//                     borderSide: BorderSide(color: Colors.grey.shade300),
//                     borderRadius: BorderRadius.circular(12),
//                   ),
//                   focusedBorder: OutlineInputBorder(
//                     borderSide: const BorderSide(
//                       color: Colors.blueAccent,
//                       width: 2,
//                     ),
//                     borderRadius: BorderRadius.circular(12),
//                   ),
//                 ),
//               ),

//               const SizedBox(height: 30),

//               /// Sign In Button
//               SizedBox(
//                 width: double.infinity,
//                 child: ElevatedButton(
//                   onPressed: _signInWithEmail,
//                   style: ElevatedButton.styleFrom(
//                     backgroundColor: Colors.blueAccent,
//                     padding: const EdgeInsets.symmetric(vertical: 16),
//                     shape: RoundedRectangleBorder(
//                       borderRadius: BorderRadius.circular(12),
//                     ),
//                     elevation: 3,
//                   ),
//                   child: const Text(
//                     'Sign In',
//                     style: TextStyle(
//                       fontSize: 18,
//                       fontWeight: FontWeight.bold,
//                       color: Colors.white,
//                     ),
//                   ),
//                 ),
//               ),

//               const SizedBox(height: 20),

//               /// Links
//               Row(
//                 mainAxisAlignment: MainAxisAlignment.center,
//                 children: [
//                   const Text(
//                     "Don't have an account?",
//                     style: TextStyle(color: Colors.black54),
//                   ),
//                   TextButton(
//                     onPressed: () {
//                       Navigator.push(
//                         context,
//                         MaterialPageRoute(
//                           builder: (context) => const Registerationscreen(),
//                         ),
//                       );
//                     },
//                     child: const Text(
//                       'Sign Up',
//                       style: TextStyle(fontWeight: FontWeight.bold),
//                     ),
//                   ),
//                 ],
//               ),
//               TextButton(
//                 onPressed: () {
//                   // TODO: Add forgot password logic
//                 },
//                 child: const Text(
//                   'Forgot Password?',
//                   style: TextStyle(color: Colors.redAccent),
//                 ),
//               ),
//             ],
//           ),
//         ),
//       ),
//     );
//   }

//   /// --- Reusable Styled Field ---
//   Widget _buildTextField({
//     required TextEditingController controller,
//     required String label,
//     required IconData icon,
//     TextInputType keyboardType = TextInputType.text,
//   }) {
//     return TextField(
//       controller: controller,
//       keyboardType: keyboardType,
//       decoration: InputDecoration(
//         labelText: label,
//         prefixIcon: Icon(icon, color: Colors.blueAccent),
//         filled: true,
//         fillColor: Colors.white,
//         contentPadding: const EdgeInsets.symmetric(
//           horizontal: 12,
//           vertical: 14,
//         ),
//         border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
//         enabledBorder: OutlineInputBorder(
//           borderSide: BorderSide(color: Colors.grey.shade300),
//           borderRadius: BorderRadius.circular(12),
//         ),
//         focusedBorder: OutlineInputBorder(
//           borderSide: const BorderSide(color: Colors.blueAccent, width: 2),
//           borderRadius: BorderRadius.circular(12),
//         ),
//       ),
//     );
//   }
// }