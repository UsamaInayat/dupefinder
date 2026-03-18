import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'welcome_screen.dart';
import 'insights_screen.dart';

class MeScreen extends StatefulWidget {
  const MeScreen({super.key});

  @override
  State<MeScreen> createState() => _MeScreenState();
}

class _MeScreenState extends State<MeScreen> {
  final _api = ApiService();
  String? _email;
  bool _guest = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final p = await SharedPreferences.getInstance();
    setState(() {
      _email = p.getString('user_email');
      _guest = p.getBool('guest_mode') == true;
    });
  }

  Future<void> _logout() async {
    await WelcomeScreen.setGuestMode(false);
    await _api.logout();
    if (mounted) {
      Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (r) => false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        CircleAvatar(
          radius: 40,
          backgroundColor: AppColors.bluePrimary.withValues(alpha: 0.15),
          child: Icon(_guest ? Icons.person_outline : Icons.person_rounded,
              size: 44, color: AppColors.bluePrimary),
        ),
        const SizedBox(height: 16),
        Text(
          _guest ? 'Guest' : (_email ?? 'User'),
          textAlign: TextAlign.center,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.purpleDark),
        ),
        if (!_guest && _email != null)
          Text(_email!, textAlign: TextAlign.center, style: TextStyle(color: AppColors.greySubtitle)),
        if (_guest)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Text(
              'Sign in to sync wishlist & history across devices.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppColors.greySubtitle),
            ),
          ),
        const SizedBox(height: 24),
        _item(Icons.insights_outlined, 'Insights & trends', () {
          Navigator.push(context, MaterialPageRoute(builder: (_) => const InsightsScreen()));
        }),
        if (_guest)
          _item(Icons.login_rounded, 'Log in / Sign up', () {
            Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (r) => false);
          }),
        const Divider(height: 32),
        ListTile(
          leading: const Icon(Icons.logout_rounded, color: Colors.redAccent),
          title: const Text('Sign out', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w600)),
          onTap: _logout,
        ),
      ],
    );
  }

  Widget _item(IconData icon, String title, VoidCallback onTap) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(AppDecor.cardRadius)),
      child: ListTile(
        leading: Icon(icon, color: AppColors.bluePrimary),
        title: Text(title, style: const TextStyle(color: AppColors.purpleDark, fontWeight: FontWeight.w500)),
        trailing: const Icon(Icons.chevron_right_rounded, color: AppColors.greySubtitle),
        onTap: onTap,
      ),
    );
  }
}
