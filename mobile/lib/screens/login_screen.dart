import 'package:flutter/material.dart';
import '../services/api_service.dart';

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
  bool _isLoading = false;
  bool _obscurePassword = true;
  
  // Real-time error messages for each field
  String? _emailError;
  String? _passwordError;
  
  // Password validation states
  bool _hasUppercase = false;
  bool _hasLowercase = false;
  bool _hasDigit = false;
  bool _hasSpecialChar = false;
  bool _hasMinLength = false;

  @override
  void initState() {
    super.initState();
    _passwordController.addListener(_validatePassword);
  }

  @override
  void dispose() {
    _passwordController.removeListener(_validatePassword);
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }
  
  // Real-time email validation with strict domain check
  void _validateEmailRealTime(String value) {
    setState(() {
      if (value.isEmpty) {
        _emailError = null;
        return;
      }
      
      // Basic email format check
      final emailRegex = RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');
      if (!emailRegex.hasMatch(value)) {
        _emailError = 'Please enter a valid email address';
        return;
      }
      
      // Split email into local and domain parts
      final parts = value.split('@');
      if (parts.length != 2) {
        _emailError = 'Please enter a valid email address';
        return;
      }
      
      final localPart = parts[0];
      final domain = parts[1].toLowerCase();
      
      // Check local part (before @)
      if (localPart.isEmpty) {
        _emailError = 'Email must have text before @ symbol';
        return;
      }
      
      if (localPart.length > 64) {
        _emailError = 'Email username is too long';
        return;
      }
      
      // Check domain part (after @)
      if (domain.isEmpty) {
        _emailError = 'Email must have a domain (e.g., @gmail.com)';
        return;
      }
      
      // Check if domain has dot
      if (!domain.contains('.')) {
        _emailError = 'Email domain must include extension (e.g., @gmail.com)';
        return;
      }
      
      final domainParts = domain.split('.');
      
      // Check domain name (before last dot)
      if (domainParts.length < 2) {
        _emailError = 'Email must have a valid domain (e.g., @gmail.com)';
        return;
      }
      
      final domainName = domainParts[0];
      final domainExtension = domainParts.last;
      
      // Check domain name is not empty
      if (domainName.isEmpty) {
        _emailError = 'Email domain name cannot be empty (e.g., @gmail.com)';
        return;
      }
      
      // Check domain extension (TLD)
      if (domainExtension.isEmpty) {
        _emailError = 'Email must have domain extension (e.g., .com, .org)';
        return;
      }
      
      if (domainExtension.length < 2) {
        _emailError = 'Email domain extension must be at least 2 characters (e.g., .com)';
        return;
      }
      
      // STRICT CHECK: Must be @gmail.com exactly
      if (domain != 'gmail.com') {
        _emailError = 'Only @gmail.com email addresses are allowed';
        return;
      }
      
      // All checks passed
      _emailError = null;
    });
  }
  
  // Real-time password validation
  void _validatePassword() {
    final password = _passwordController.text;
    setState(() {
      _hasUppercase = password.contains(RegExp(r'[A-Z]'));
      _hasLowercase = password.contains(RegExp(r'[a-z]'));
      _hasDigit = password.contains(RegExp(r'[0-9]'));
      _hasSpecialChar = password.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'));
      _hasMinLength = password.length >= 8;
      
      // Set password error message
      if (password.isEmpty) {
        _passwordError = null;
      } else if (!_hasMinLength) {
        _passwordError = 'Password must be at least 8 characters';
      } else if (!_hasUppercase) {
        _passwordError = 'Password must contain at least one uppercase letter';
      } else if (!_hasLowercase) {
        _passwordError = 'Password must contain at least one lowercase letter';
      } else if (!_hasDigit) {
        _passwordError = 'Password must contain at least one digit';
      } else if (!_hasSpecialChar) {
        _passwordError = 'Password must contain at least one special character';
      } else {
        _passwordError = null; // All requirements met
      }
    });
  }
  
  // Validate email with proper format and domain (for form submission)
  String? _validateEmail(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter your email';
    }
    
    // Basic email format check
    final emailRegex = RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');
    if (!emailRegex.hasMatch(value)) {
      return 'Please enter a valid email address';
    }
    
    // Split email into local and domain parts
    final parts = value.split('@');
    if (parts.length != 2) {
      return 'Please enter a valid email address';
    }
    
    final localPart = parts[0];
    final domain = parts[1].toLowerCase();
    
    // Check local part
    if (localPart.isEmpty) {
      return 'Email must have text before @ symbol';
    }
    
    // Check domain
    if (domain.isEmpty || !domain.contains('.')) {
      return 'Email must have a valid domain (e.g., @gmail.com)';
    }
    
    final domainParts = domain.split('.');
    if (domainParts.length < 2) {
      return 'Email must have a valid domain (e.g., @gmail.com)';
    }
    
    final domainExtension = domainParts.last;
    if (domainExtension.length < 2) {
      return 'Email domain extension must be at least 2 characters';
    }
    
    // STRICT CHECK: Must be @gmail.com exactly
    if (domain != 'gmail.com') {
      return 'Only @gmail.com email addresses are allowed';
    }
    
    return null;
  }
  
  // Validate password with all requirements (for form submission)
  String? _validatePasswordField(String? value) {
    if (value == null || value.isEmpty) {
      return 'Please enter your password';
    }
    // For form submission, check all requirements
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!value.contains(RegExp(r'[A-Z]'))) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!value.contains(RegExp(r'[a-z]'))) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!value.contains(RegExp(r'[0-9]'))) {
      return 'Password must contain at least one digit';
    }
    if (!value.contains(RegExp(r'[!@#$%^&*(),.?":{}|<>]'))) {
      return 'Password must contain at least one special character';
    }
    return null;
  }

  Future<void> _handleLogin() async {
    // First validate form fields
    if (!_formKey.currentState!.validate()) {
      return;
    }
    
    // Also check for real-time validation errors
    if (_emailError != null || _passwordError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please fix all errors before submitting'),
          backgroundColor: Colors.red,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    
    // Double-check email is @gmail.com
    final email = _emailController.text.trim().toLowerCase();
    if (!email.endsWith('@gmail.com')) {
      setState(() {
        _emailError = 'Only @gmail.com email addresses are allowed';
      });
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Only @gmail.com email addresses are allowed'),
          backgroundColor: Colors.red,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    
    // Double-check password meets all requirements
    if (!_hasUppercase || !_hasLowercase || !_hasDigit || !_hasSpecialChar || !_hasMinLength) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Password must meet all requirements'),
          backgroundColor: Colors.red,
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      await _apiService.login(
        _emailController.text.trim(),
        _passwordController.text,
      );

      if (mounted) {
        // Navigate to home screen
        Navigator.of(context).pushReplacementNamed('/home');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(e.toString().replaceFirst('Exception: ', '')),
            backgroundColor: Colors.black87,
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(
                    Icons.shopping_bag,
                    size: 80,
                    color: Colors.black,
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'DupeFinder',
                    style: TextStyle(
                      fontSize: 32,
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Login to continue',
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 40),
                  // Email Field
                  TextFormField(
                    controller: _emailController,
                    keyboardType: TextInputType.emailAddress,
                    onChanged: _validateEmailRealTime,
                    decoration: const InputDecoration(
                      labelText: 'Email',
                      prefixIcon: Icon(Icons.email),
                      border: OutlineInputBorder(),
                      hintText: 'example@gmail.com',
                      errorText: null, // Disable default validator error
                    ),
                    validator: _validateEmail,
                  ),
                  // Real-time error message below email field
                  if (_emailError != null) ...[
                    const SizedBox(height: 4),
                    Padding(
                      padding: const EdgeInsets.only(left: 16),
                      child: Text(
                        _emailError!,
                        style: const TextStyle(
                          color: Colors.red,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 16),
                  
                  // Password Field with Real-time Validation
                  TextFormField(
                    controller: _passwordController,
                    obscureText: _obscurePassword,
                    onChanged: (value) {
                      _validatePassword(); // Update validation in real-time
                    },
                    decoration: InputDecoration(
                      labelText: 'Password',
                      prefixIcon: const Icon(Icons.lock),
                      suffixIcon: IconButton(
                        icon: Icon(
                          _obscurePassword
                              ? Icons.visibility
                              : Icons.visibility_off,
                        ),
                        onPressed: () {
                          setState(() {
                            _obscurePassword = !_obscurePassword;
                          });
                        },
                      ),
                      border: const OutlineInputBorder(),
                      hintText: 'At least 8 characters',
                      errorText: null, // Disable default validator error
                    ),
                    validator: _validatePasswordField,
                  ),
                  // Real-time error message below password field
                  if (_passwordError != null) ...[
                    const SizedBox(height: 4),
                    Padding(
                      padding: const EdgeInsets.only(left: 16),
                      child: Text(
                        _passwordError!,
                        style: const TextStyle(
                          color: Colors.red,
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                  // Password Requirements Display - Always show when typing
                  if (_passwordController.text.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.grey[300]!),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Password Requirements:',
                            style: TextStyle(
                              fontSize: 12,
                              fontWeight: FontWeight.bold,
                              color: Colors.black87,
                            ),
                          ),
                          const SizedBox(height: 4),
                          _buildRequirementRow('At least 8 characters', _hasMinLength),
                          _buildRequirementRow('One uppercase letter (A-Z)', _hasUppercase),
                          _buildRequirementRow('One lowercase letter (a-z)', _hasLowercase),
                          _buildRequirementRow('One digit (0-9)', _hasDigit),
                          _buildRequirementRow('One special character (!@#\$%...)', _hasSpecialChar),
                        ],
                      ),
                    ),
                  ],
                  const SizedBox(height: 24),
                  ElevatedButton(
                    onPressed: _isLoading ? null : _handleLogin,
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: Colors.black,
                      foregroundColor: Colors.white,
                    ),
                    child: _isLoading
                        ? const SizedBox(
                            height: 20,
                            width: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor:
                                  AlwaysStoppedAnimation<Color>(Colors.white),
                            ),
                          )
                        : const Text(
                            'Login',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                  ),
                  const SizedBox(height: 16),
                  TextButton(
                    onPressed: () {
                      Navigator.of(context).pushNamed('/register');
                    },
                    child: const Text('Don\'t have an account? Register'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
  
  // Helper widget to build requirement row with checkmark
  Widget _buildRequirementRow(String text, bool isValid) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        children: [
          Icon(
            isValid ? Icons.check_circle : Icons.circle_outlined,
            size: 16,
            color: isValid ? Colors.green : Colors.grey,
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 12,
                color: isValid ? Colors.green[700] : Colors.grey[600],
                decoration: isValid ? null : TextDecoration.none,
              ),
            ),
          ),
        ],
      ),
    );
  }
}

