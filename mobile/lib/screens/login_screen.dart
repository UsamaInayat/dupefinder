import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../services/user_profile_service.dart';
import '../theme/app_theme.dart';
import 'main_shell.dart';
import 'welcome_screen.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _apiService = ApiService();
  final _profileService = UserProfileService();
  bool _isLoading = false;
  bool _obscurePassword = true;

  static bool _validEmail(String v) {
    return RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(v.trim());
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _isLoading = true);
    try {
      await WelcomeScreen.setGuestMode(false);
      await _apiService.login(
        _emailController.text.trim(),
        _passwordController.text,
      );
      // Profile sync already runs inside login() (unawaited). Do not await getMe here —
      // it has no timeout and can block the button forever on slow/hung /auth/me.
      await _profileService.ensureDefaultsForLogin(_emailController.text.trim());
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(MainShell.lastTabPreferenceKey);
      if (mounted) {
        Navigator.of(context).pushNamedAndRemoveUntil('/home', (r) => false);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString().replaceFirst('Exception: ', '')),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  static final TextStyle _inputValueStyle = GoogleFonts.inter(
    color: Colors.white,
    fontSize: 16,
    fontWeight: FontWeight.w800,
  );

  InputDecoration _glassField(String label, String hint, {Widget? prefix, Widget? suffix}) {
    return InputDecoration(
      labelText: label,
      hintText: hint,
      labelStyle: GoogleFonts.inter(
        color: Colors.white,
        fontSize: 14,
        fontWeight: FontWeight.w900,
        height: 1.1,
      ),
      floatingLabelStyle: GoogleFonts.inter(
        color: Colors.white,
        fontSize: 13,
        fontWeight: FontWeight.w900,
      ),
      hintStyle: GoogleFonts.inter(
        color: Colors.white.withValues(alpha: 0.64),
        fontSize: 15,
        fontWeight: FontWeight.w800,
      ),
      prefixIcon: prefix,
      suffixIcon: suffix,
      filled: true,
      fillColor: Colors.white.withValues(alpha: 0.18),
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.55)),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: BorderSide(color: Colors.white.withValues(alpha: 0.55)),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: Colors.white, width: 1.5),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(18),
        borderSide: const BorderSide(color: Colors.redAccent, width: 1),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: BoxDecoration(
          gradient: DupePalette.loginBackgroundGradient,
        ),
        child: SafeArea(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Align(
                  alignment: Alignment.centerLeft,
                  child: IconButton(
                    icon: Icon(Icons.arrow_back_ios_new_rounded, color: Colors.white.withValues(alpha: 0.95)),
                    onPressed: () => Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (r) => false),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  'Welcome Back',
                  textAlign: TextAlign.center,
                  style: DupePalette.serifHeading(32, w: FontWeight.w900, color: Colors.white),
                ),
                const SizedBox(height: 10),
                Text(
                  'Sign in to continue your journey',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                    fontSize: 15,
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 28),
                Container(
                  padding: const EdgeInsets.fromLTRB(20, 26, 20, 26),
                  decoration: AppDecor.glassCard(),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        TextFormField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          style: _inputValueStyle,
                          cursorColor: Colors.white,
                          decoration: _glassField(
                            'Email',
                            'Enter your email',
                            prefix: Icon(Icons.email_outlined, color: Colors.white.withValues(alpha: 0.85)),
                          ),
                          validator: (v) {
                            if (v == null || v.trim().isEmpty) return 'Enter your email';
                            if (!_validEmail(v)) return 'Enter a valid email';
                            return null;
                          },
                        ),
                        const SizedBox(height: 18),
                        TextFormField(
                          controller: _passwordController,
                          obscureText: _obscurePassword,
                          style: _inputValueStyle,
                          cursorColor: Colors.white,
                          decoration: _glassField(
                            'Password',
                            'Enter your password',
                            prefix: Icon(Icons.lock_outline_rounded, color: Colors.white.withValues(alpha: 0.85)),
                            suffix: IconButton(
                              icon: Icon(
                                _obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                                color: Colors.white.withValues(alpha: 0.8),
                              ),
                              onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                            ),
                          ),
                          validator: (v) {
                            if (v == null || v.isEmpty) return 'Enter your password';
                            if (v.length < 8) return 'At least 8 characters';
                            if (v.length > 20) return 'At most 20 characters';
                            return null;
                          },
                        ),
                        const SizedBox(height: 28),
                        SizedBox(
                          height: 54,
                          child: DecoratedBox(
                            decoration: AppTheme.loginGradientButton,
                            child: Material(
                              color: Colors.transparent,
                              child: InkWell(
                                onTap: _isLoading ? null : _handleLogin,
                                borderRadius: BorderRadius.circular(32),
                                child: Center(
                                  child: _isLoading
                                      ? const SizedBox(
                                          width: 24,
                                          height: 24,
                                          child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                        )
                                      : Row(
                                          mainAxisAlignment: MainAxisAlignment.center,
                                          children: [
                                            Text(
                                              'Sign In',
                                              style: GoogleFonts.inter(
                                                color: Colors.white,
                                                fontSize: 17,
                                                fontWeight: FontWeight.w900,
                                              ),
                                            ),
                                            const SizedBox(width: 8),
                                            const Icon(Icons.arrow_forward_rounded, color: Colors.white, size: 22),
                                          ],
                                        ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                TextButton(
                  onPressed: () => Navigator.of(context).pushReplacementNamed('/register'),
                  child: Text.rich(
                    TextSpan(
                      style: GoogleFonts.inter(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                      children: [
                        const TextSpan(text: "Don't have an account? "),
                        TextSpan(
                          text: 'Sign Up',
                          style: GoogleFonts.inter(
                            decoration: TextDecoration.underline,
                            fontWeight: FontWeight.w900,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
                    textAlign: TextAlign.center,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
