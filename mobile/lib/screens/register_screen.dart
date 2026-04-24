import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import '../services/user_profile_service.dart';
import '../theme/app_theme.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _otpController = TextEditingController();
  final _apiService = ApiService();
  final _profileService = UserProfileService();
  bool _isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirm = true;
  bool _otpSent = false;
  String? _userEmail;
  bool _showPasswordRequirements = false;

  bool _hasUppercase = false;
  bool _hasLowercase = false;
  bool _hasDigit = false;
  bool _hasSpecial = false;
  bool _hasMinLength = false;

  static bool _validEmail(String v) {
    return RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$').hasMatch(v.trim());
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _otpController.dispose();
    super.dispose();
  }

  void _validatePassword() {
    final p = _passwordController.text;
    setState(() {
      _hasUppercase = p.contains(RegExp(r'[A-Z]'));
      _hasLowercase = p.contains(RegExp(r'[a-z]'));
      _hasDigit = p.contains(RegExp(r'[0-9]'));
      _hasSpecial = p.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'));
      _hasMinLength = p.length >= 8;
    });
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

  Future<void> _register() async {
    if (!_formKey.currentState!.validate()) return;
    if (!_hasUppercase || !_hasLowercase || !_hasDigit || !_hasSpecial || !_hasMinLength) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password must meet all requirements below')),
      );
      return;
    }
    if (_passwordController.text != _confirmPasswordController.text) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Passwords do not match')),
      );
      return;
    }
    setState(() => _isLoading = true);
    try {
      await _apiService.register(
        _emailController.text.trim(),
        _passwordController.text,
        fullName: _nameController.text.trim(),
      );
      await _profileService.initializeAfterSignup(
        username: _nameController.text.trim(),
      );
      setState(() {
        _otpSent = true;
        _userEmail = _emailController.text.trim();
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Check your email for the verification code.')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _verifyOtp() async {
    if (_otpController.text.trim().isEmpty) return;
    setState(() => _isLoading = true);
    try {
      await _apiService.verifyOTP(_userEmail!, _otpController.text.trim());
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Verified! You can log in now.')),
        );
        Navigator.of(context).pushNamedAndRemoveUntil('/login', (r) => false);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString().replaceFirst('Exception: ', ''))),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: BoxDecoration(gradient: DupePalette.loginBackgroundGradient),
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
                    onPressed: () {
                      if (_otpSent) {
                        setState(() {
                          _otpSent = false;
                          _otpController.clear();
                        });
                      } else {
                        Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (r) => false);
                      }
                    },
                  ),
                ),
                Text(
                  _otpSent ? 'Verify email' : 'Create account',
                  textAlign: TextAlign.center,
                  style: DupePalette.serifHeading(30, w: FontWeight.w900, color: Colors.white),
                ),
                const SizedBox(height: 10),
                Text(
                  _otpSent
                      ? 'Enter the code we sent you'
                      : 'Join DupeFinder to save favorites and track savings.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                    fontSize: 15,
                    color: Colors.white,
                    fontWeight: FontWeight.w900,
                    height: 1.35,
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  padding: const EdgeInsets.fromLTRB(20, 26, 20, 26),
                  decoration: AppDecor.glassCard(),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        if (!_otpSent) ...[
                          TextFormField(
                            controller: _nameController,
                            textCapitalization: TextCapitalization.words,
                            style: _inputValueStyle,
                            cursorColor: Colors.white,
                            decoration: _glassField(
                              'Full name',
                              'Your name',
                              prefix: Icon(Icons.person_outline_rounded, color: Colors.white.withValues(alpha: 0.85)),
                            ),
                            validator: (v) {
                              if (v == null || v.trim().length < 2) return 'Enter your name';
                              return null;
                            },
                          ),
                          const SizedBox(height: 16),
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
                              if (v == null || v.trim().isEmpty) return 'Enter email';
                              if (!_validEmail(v)) return 'Invalid email';
                              return null;
                            },
                          ),
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _passwordController,
                            obscureText: _obscurePassword,
                            style: _inputValueStyle,
                            cursorColor: Colors.white,
                            onChanged: (_) {
                              _validatePassword();
                              final hasText = _passwordController.text.isNotEmpty;
                              if (_showPasswordRequirements != hasText) {
                                setState(() => _showPasswordRequirements = hasText);
                              }
                            },
                            onTap: () {
                              if (!_showPasswordRequirements && _passwordController.text.isNotEmpty) {
                                setState(() => _showPasswordRequirements = true);
                              }
                            },
                            decoration: _glassField(
                              'Password',
                              'Create a password',
                              prefix: Icon(Icons.lock_outline_rounded, color: Colors.white.withValues(alpha: 0.85)),
                              suffix: IconButton(
                                icon: Icon(
                                  _obscurePassword ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                                  color: Colors.white.withValues(alpha: 0.8),
                                ),
                                onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                              ),
                            ),
                          ),
                          if (_showPasswordRequirements) ...[
                            const SizedBox(height: 12),
                            _passwordChecksGlass(),
                          ],
                          const SizedBox(height: 16),
                          TextFormField(
                            controller: _confirmPasswordController,
                            obscureText: _obscureConfirm,
                            style: _inputValueStyle,
                            cursorColor: Colors.white,
                            decoration: _glassField(
                              'Confirm password',
                              'Repeat password',
                              prefix: Icon(Icons.lock_outline_rounded, color: Colors.white.withValues(alpha: 0.85)),
                              suffix: IconButton(
                                icon: Icon(
                                  _obscureConfirm ? Icons.visibility_outlined : Icons.visibility_off_outlined,
                                  color: Colors.white.withValues(alpha: 0.8),
                                ),
                                onPressed: () => setState(() => _obscureConfirm = !_obscureConfirm),
                              ),
                            ),
                            validator: (v) {
                              if (v == null || v.isEmpty) return 'Confirm your password';
                              if (v != _passwordController.text) return 'Passwords must match';
                              return null;
                            },
                          ),
                          const SizedBox(height: 26),
                          SizedBox(
                            height: 54,
                            child: DecoratedBox(
                              decoration: AppTheme.loginGradientButton,
                              child: Material(
                                color: Colors.transparent,
                                child: InkWell(
                                  onTap: _isLoading ? null : _register,
                                  borderRadius: BorderRadius.circular(32),
                                  child: Center(
                                    child: _isLoading
                                        ? const SizedBox(
                                            width: 24,
                                            height: 24,
                                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                          )
                                        : Text(
                                            'Sign Up',
                                            style: GoogleFonts.inter(
                                              color: Colors.white,
                                              fontSize: 17,
                                              fontWeight: FontWeight.w900,
                                            ),
                                          ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ] else ...[
                          Text(
                            'Enter the code sent to\n$_userEmail',
                            textAlign: TextAlign.center,
                            style: GoogleFonts.inter(
                              fontSize: 15,
                              color: Colors.white,
                              fontWeight: FontWeight.w900,
                              height: 1.45,
                            ),
                          ),
                          const SizedBox(height: 20),
                          TextFormField(
                            controller: _otpController,
                            keyboardType: TextInputType.number,
                            style: _inputValueStyle,
                            cursorColor: Colors.white,
                            decoration: _glassField(
                              'Verification code',
                              '6-digit code',
                              prefix: Icon(Icons.pin_outlined, color: Colors.white.withValues(alpha: 0.85)),
                            ),
                          ),
                          const SizedBox(height: 26),
                          SizedBox(
                            height: 54,
                            child: DecoratedBox(
                              decoration: AppTheme.loginGradientButton,
                              child: Material(
                                color: Colors.transparent,
                                child: InkWell(
                                  onTap: _isLoading ? null : _verifyOtp,
                                  borderRadius: BorderRadius.circular(32),
                                  child: Center(
                                    child: _isLoading
                                        ? const SizedBox(
                                            width: 24,
                                            height: 24,
                                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                          )
                                        : Text(
                                            'Verify',
                                            style: GoogleFonts.inter(
                                              color: Colors.white,
                                              fontSize: 17,
                                              fontWeight: FontWeight.w900,
                                            ),
                                          ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ],
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                TextButton(
                  onPressed: () => Navigator.of(context).pushReplacementNamed('/login'),
                  child: Text.rich(
                    TextSpan(
                      style: GoogleFonts.inter(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.w900,
                      ),
                      children: [
                        const TextSpan(text: 'Already have an account? '),
                        TextSpan(
                          text: 'Log In',
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

  Widget _passwordChecksGlass() {
    Widget row(bool ok, String label) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(
          children: [
            Icon(
              ok ? Icons.check_circle_rounded : Icons.radio_button_unchecked_rounded,
              size: 18,
              color: ok ? DupePalette.teal : Colors.white.withValues(alpha: 0.55),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                label,
                style: GoogleFonts.inter(
                  fontSize: 12,
                  fontWeight: FontWeight.w900,
                  color: Colors.white,
                ),
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.white.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Password requirements',
            style: GoogleFonts.inter(
              fontWeight: FontWeight.w900,
              color: Colors.white,
              fontSize: 13,
            ),
          ),
          const SizedBox(height: 8),
          row(_hasMinLength, 'At least 8 characters'),
          row(_hasUppercase, 'At least 1 uppercase letter'),
          row(_hasLowercase, 'At least 1 lowercase letter'),
          row(_hasDigit, 'At least 1 number'),
          row(_hasSpecial, 'At least 1 special character'),
        ],
      ),
    );
  }
}
