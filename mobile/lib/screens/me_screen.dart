import 'package:flutter/material.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:image_picker/image_picker.dart';
import 'package:image_cropper/image_cropper.dart';
import '../services/api_service.dart';
import '../services/community_service.dart';
import '../services/dupe_history_service.dart';
import '../services/user_profile_service.dart';
import '../theme/app_theme.dart';
import 'welcome_screen.dart';
import 'insights_screen.dart';
import 'dupe_history_screen.dart';

class MeScreen extends StatefulWidget {
  final Future<void> Function(
          String postId, String replyId, String notificationId)?
      onOpenCommunityFromNotification;
  final VoidCallback? onNotificationStateChanged;

  const MeScreen({
    super.key,
    this.onOpenCommunityFromNotification,
    this.onNotificationStateChanged,
  });

  @override
  State<MeScreen> createState() => _MeScreenState();
}

class _MeScreenState extends State<MeScreen> {
  final _api = ApiService();
  final _communityService = CommunityService();
  final _profileService = UserProfileService();
  final _historyService = DupeHistoryService();
  final _picker = ImagePicker();
  String? _email;
  String _username = '';
  String? _joinedAt;
  String? _profileImageBase64;
  int _dupeHistoryCount = 0;
  bool _guest = false;
  Uint8List? _pendingProfileBytes;
  List<CommunityNotification> _notifications = [];
  String? _snackShownNotificationId;

  @override
  void initState() {
    super.initState();
    _loadCachedThenRefresh();
  }

  Future<void> _loadCachedThenRefresh() async {
    final p = await SharedPreferences.getInstance();
    if (!mounted) return;
    setState(() {
      _email = p.getString('user_email');
      _guest = p.getBool('guest_mode') == true;
      _username = (p.getString('user_name') ?? '').trim();
      _joinedAt = p.getString('user_joined_at');
      _profileImageBase64 = p.getString('user_profile_image');
    });
    _load();
  }

  Future<void> _load() async {
    final results = await Future.wait([
      SharedPreferences.getInstance(),
      _profileService.getProfile(),
      _historyService.getHistory(),
    ]);
    final p = results[0] as SharedPreferences;
    final profile = results[1] as Map<String, dynamic>;
    final history = results[2] as List<dynamic>;
    List<CommunityNotification> notifications = [];
    final isGuest = p.getBool('guest_mode') == true;
    if (!isGuest) {
      try {
        notifications = await _communityService.getNotifications(
            limit: 10, unreadOnly: true);
      } catch (_) {}
    }
    setState(() {
      _email = p.getString('user_email');
      _guest = isGuest;
      _username = profile['username'] as String? ?? '';
      _joinedAt = profile['joinedAt'] as String?;
      _profileImageBase64 = profile['profileImage'] as String?;
      _dupeHistoryCount = history.length;
      _notifications = notifications;
    });
    _maybeShowNotificationSnack(notifications);
    widget.onNotificationStateChanged?.call();
  }

  void _maybeShowNotificationSnack(List<CommunityNotification> notifications) {
    if (!mounted || _guest || notifications.isEmpty) return;
    final top = notifications.first;
    if (_snackShownNotificationId == top.id) return;
    _snackShownNotificationId = top.id;
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        SnackBar(
          content: Text(top.message),
          behavior: SnackBarBehavior.floating,
          action: SnackBarAction(
            label: 'Open',
            onPressed: () {
              _openNotification(top);
            },
          ),
        ),
      );
    });
  }

  Future<void> _logout() async {
    await WelcomeScreen.setGuestMode(false);
    await _api.logout();
    if (mounted) {
      Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (r) => false);
    }
  }

  Future<void> _pickProfileImage() async {
    final x =
        await _picker.pickImage(source: ImageSource.gallery, imageQuality: 80);
    if (x == null) return;
    CroppedFile? cropped;
    try {
      cropped = await ImageCropper().cropImage(
        sourcePath: x.path,
        compressFormat: ImageCompressFormat.jpg,
        compressQuality: 90,
        aspectRatio: const CropAspectRatio(ratioX: 1, ratioY: 1),
        uiSettings: [
          if (kIsWeb)
            WebUiSettings(
              context: context,
              presentStyle: WebPresentStyle.dialog,
              size: const CropperSize(width: 420, height: 420),
              dragMode: WebDragMode.move,
              viewwMode: WebViewMode.mode_1,
              initialAspectRatio: 1,
              checkOrientation: true,
            )
          else
            AndroidUiSettings(
              toolbarTitle: 'Crop Profile Photo',
              toolbarColor: Colors.black,
              toolbarWidgetColor: Colors.white,
              lockAspectRatio: true,
              initAspectRatio: CropAspectRatioPreset.square,
              hideBottomControls: false,
            ),
        ],
      );
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Crop failed, using original image. ($e)'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
      cropped = null;
    }
    final bytes =
        cropped != null ? await cropped.readAsBytes() : await x.readAsBytes();
    if (!mounted) return;
    setState(() => _pendingProfileBytes = bytes);
    await _showUploadPreview();
  }

  Future<void> _showUploadPreview() async {
    if (_pendingProfileBytes == null) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Preview profile image'),
        content: ClipRRect(
          borderRadius: BorderRadius.circular(10),
          child: Image.memory(
            _pendingProfileBytes!,
            width: 220,
            height: 220,
            fit: BoxFit.cover,
          ),
        ),
        actions: [
          TextButton(
            onPressed: () {
              Navigator.pop(ctx);
            },
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () async {
              final b = _pendingProfileBytes;
              Navigator.pop(ctx);
              if (b == null) return;
              await _profileService.setProfileImageFromBytes(b);
              if (!mounted) return;
              setState(() => _pendingProfileBytes = null);
              await _load();
              if (!mounted) return;
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Profile image uploaded'),
                  behavior: SnackBarBehavior.floating,
                ),
              );
            },
            child: const Text('Upload'),
          ),
        ],
      ),
    );
    if (!mounted) return;
    setState(() => _pendingProfileBytes = null);
  }

  Future<void> _editDisplayName() async {
    final controller = TextEditingController(text: _username);
    final next = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Edit name'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            labelText: 'Display name',
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, controller.text.trim()),
            child: const Text('Save'),
          ),
        ],
      ),
    );
    if (next == null || next.trim().isEmpty) return;
    await _profileService.setDisplayName(next);
    await _load();
  }

  Future<void> _openNotification(CommunityNotification n) async {
    if (mounted) {
      setState(() => _notifications.removeWhere((x) => x.id == n.id));
    }
    widget.onNotificationStateChanged?.call();

    final open = widget.onOpenCommunityFromNotification;
    if (open != null) {
      await open(n.postId, n.replyId, n.id);
    }

    try {
      await _communityService.markNotificationRead(n.id);
      widget.onNotificationStateChanged?.call();
    } catch (_) {
      if (mounted) {
        await _load();
      }
    }
  }

  String _displayName() {
    if (_guest) return 'Guest';
    if (_username.isNotEmpty) return _username;
    if (_email != null && _email!.contains('@')) {
      return _email!.split('@').first;
    }
    return 'User';
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            DupePalette.pink.withValues(alpha: 0.08),
            DupePalette.teal.withValues(alpha: 0.1),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: ListView(
        padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
        children: [
          ShaderMask(
            blendMode: BlendMode.srcIn,
            shaderCallback: (bounds) => LinearGradient(
              colors: [DupePalette.pink, DupePalette.blue],
            ).createShader(bounds),
            child: Text(
              'Profile',
              style: GoogleFonts.playfairDisplay(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.white,
              ),
            ),
          ),
          const SizedBox(height: 18),
          Container(
            padding: const EdgeInsets.all(18),
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: DupePalette.pink.withValues(alpha: 0.1),
                  blurRadius: 18,
                  offset: const Offset(0, 8),
                ),
              ],
            ),
            child: Column(
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Stack(
                      clipBehavior: Clip.none,
                      children: [
                        CircleAvatar(
                          radius: 40,
                          backgroundColor: DupePalette.pink.withValues(alpha: 0.15),
                          backgroundImage: (_profileImageBase64 != null &&
                                  _profileImageBase64!.isNotEmpty)
                              ? MemoryImage(base64Decode(_profileImageBase64!))
                              : null,
                          child: (_profileImageBase64 == null ||
                                  _profileImageBase64!.isEmpty)
                              ? Icon(
                                  _guest ? Icons.person_outline : Icons.person_rounded,
                                  size: 40,
                                  color: DupePalette.pink,
                                )
                              : null,
                        ),
                        if (!_guest)
                          Positioned(
                            right: -2,
                            bottom: -2,
                            child: Material(
                              color: DupePalette.blue,
                              shape: const CircleBorder(),
                              child: const Icon(Icons.check_rounded, color: Colors.white, size: 16),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            _displayName(),
                            style: GoogleFonts.playfairDisplay(
                              fontSize: 20,
                              fontWeight: FontWeight.bold,
                              color: DupePalette.textPrimary,
                            ),
                          ),
                          if (!_guest && _email != null) ...[
                            const SizedBox(height: 4),
                            Text(
                              _email!,
                              style: GoogleFonts.inter(
                                fontSize: 13,
                                color: DupePalette.greySubtitle,
                              ),
                            ),
                          ],
                          if (!_guest && _joinedAt != null && _joinedAt!.isNotEmpty) ...[
                            const SizedBox(height: 4),
                            Text(
                              'Joined app: ${_joinedAt!.substring(0, _joinedAt!.length >= 10 ? 10 : _joinedAt!.length)}',
                              style: GoogleFonts.inter(fontSize: 11, color: DupePalette.greySubtitle),
                            ),
                          ],
                          if (_guest)
                            Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(
                                'Sign in to sync wishlist & history.',
                                style: GoogleFonts.inter(
                                  fontSize: 12,
                                  color: DupePalette.greySubtitle,
                                ),
                              ),
                            ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 18),
                Row(
                  children: [
                    Expanded(
                      child: _statTile(
                        icon: Icons.favorite_outline_rounded,
                        iconColor: DupePalette.pink,
                        value: '$_dupeHistoryCount',
                        label: 'Dupes',
                      ),
                    ),
                    Expanded(
                      child: _statTile(
                        icon: Icons.insights_outlined,
                        iconColor: DupePalette.teal,
                        value: '$_dupeHistoryCount',
                        label: 'Tracked',
                      ),
                    ),
                    Expanded(
                      child: _statTile(
                        icon: Icons.savings_outlined,
                        iconColor: DupePalette.blue,
                        value: '—',
                        label: 'Savings',
                      ),
                    ),
                  ],
                ),
                if (!_guest) ...[
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      TextButton.icon(
                        onPressed: _pickProfileImage,
                        icon: Icon(Icons.photo_camera_outlined, size: 18, color: DupePalette.pink),
                        label: Text('Photo', style: TextStyle(color: DupePalette.pink)),
                      ),
                      TextButton.icon(
                        onPressed: _editDisplayName,
                        icon: Icon(Icons.edit_outlined, size: 18, color: DupePalette.blue),
                        label: Text('Name', style: TextStyle(color: DupePalette.blue)),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(height: 16),
          Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.circular(24),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.04),
                  blurRadius: 12,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              children: [
                _menuRow(
                  icon: Icons.bookmark_outline_rounded,
                  title: 'Saved Items',
                  badge: _dupeHistoryCount > 0 ? '$_dupeHistoryCount' : null,
                  onTap: () {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const DupeHistoryScreen()));
                  },
                ),
                _divider(),
                _menuRow(
                  icon: Icons.shopping_bag_outlined,
                  title: 'Dupe history',
                  subtitle: '$_dupeHistoryCount items',
                  onTap: () {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const DupeHistoryScreen()));
                  },
                ),
                _divider(),
                _menuRow(
                  icon: Icons.notifications_outlined,
                  title: 'Notifications',
                  badge: _notifications.isNotEmpty ? '${_notifications.length}' : null,
                  onTap: () {
                    if (_notifications.isNotEmpty) {
                      _openNotification(_notifications.first);
                    }
                  },
                ),
                _divider(),
                _menuRow(
                  icon: Icons.insights_outlined,
                  title: 'Insights & trends',
                  onTap: () {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => const InsightsScreen()));
                  },
                ),
              ],
            ),
          ),
          if (!_guest && _notifications.isNotEmpty) ...[
            const SizedBox(height: 16),
            Text(
              'Recent notifications',
              style: GoogleFonts.inter(
                fontWeight: FontWeight.w700,
                color: DupePalette.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            ..._notifications.take(3).map(
                  (n) => Card(
                    margin: const EdgeInsets.only(bottom: 8),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                    child: ListTile(
                      title: Text(n.message),
                      subtitle: Text(
                        n.replyPreview.isEmpty ? 'Tap to open your post' : n.replyPreview,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                      ),
                      trailing: const Icon(Icons.chevron_right_rounded),
                      onTap: () => _openNotification(n),
                    ),
                  ),
                ),
          ],
          if (_guest)
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Material(
                color: Colors.white,
                borderRadius: BorderRadius.circular(20),
                child: _menuRow(
                  icon: Icons.login_rounded,
                  title: 'Log in / Sign up',
                  onTap: () {
                    Navigator.of(context).pushNamedAndRemoveUntil('/welcome', (r) => false);
                  },
                ),
              ),
            ),
          const SizedBox(height: 20),
          SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: _logout,
              icon: const Icon(Icons.logout_rounded, color: Colors.redAccent),
              label: const Text('Log Out', style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w600)),
              style: OutlinedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
                backgroundColor: Colors.white,
                side: BorderSide(color: Colors.redAccent.withValues(alpha: 0.4)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(24)),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _divider() => Divider(height: 1, thickness: 1, color: Colors.grey.withValues(alpha: 0.12));

  Widget _statTile({
    required IconData icon,
    required Color iconColor,
    required String value,
    required String label,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 8),
      margin: const EdgeInsets.symmetric(horizontal: 4),
      decoration: BoxDecoration(
        color: DupePalette.scaffoldLight,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        children: [
          Icon(icon, color: iconColor, size: 22),
          const SizedBox(height: 6),
          Text(value, style: GoogleFonts.inter(fontWeight: FontWeight.bold, fontSize: 16)),
          Text(label, style: GoogleFonts.inter(fontSize: 11, color: DupePalette.greySubtitle)),
        ],
      ),
    );
  }

  Widget _menuRow({
    required IconData icon,
    required String title,
    String? subtitle,
    String? badge,
    required VoidCallback onTap,
  }) {
    return ListTile(
      leading: Container(
        padding: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: DupePalette.pink.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(icon, color: DupePalette.pinkDeep, size: 22),
      ),
      title: Text(title, style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
      subtitle: subtitle != null ? Text(subtitle, style: GoogleFonts.inter(fontSize: 12)) : null,
      trailing: badge != null
          ? CircleAvatar(
              radius: 14,
              backgroundColor: DupePalette.pink,
              child: Text(badge, style: const TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.bold)),
            )
          : const Icon(Icons.chevron_right_rounded, color: DupePalette.greySubtitle),
      onTap: onTap,
    );
  }
}
