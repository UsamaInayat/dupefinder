import 'package:flutter/material.dart';
import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart' show kIsWeb;
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
    _load();
  }

  Future<void> _load() async {
    final p = await SharedPreferences.getInstance();
    final profile = await _profileService.getProfile();
    final history = await _historyService.getHistory();
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
    try {
      await _communityService.markNotificationRead(n.id);
    } catch (_) {}
    await _load();
    if (!mounted) return;
    final open = widget.onOpenCommunityFromNotification;
    if (open == null) return;
    await open(n.postId, n.replyId, n.id);
  }

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Center(
          child: Container(
            width: 92,
            height: 92,
            decoration: BoxDecoration(
              color: AppColors.bluePrimary.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(46),
              border: Border.all(color: AppColors.borderLightBlue),
            ),
            clipBehavior: Clip.antiAlias,
            child:
                (_profileImageBase64 != null && _profileImageBase64!.isNotEmpty)
                    ? Image.memory(
                        base64Decode(_profileImageBase64!),
                        fit: BoxFit.cover,
                        alignment: Alignment.topCenter,
                      )
                    : Icon(
                        _guest ? Icons.person_outline : Icons.person_rounded,
                        size: 44,
                        color: AppColors.bluePrimary,
                      ),
          ),
        ),
        const SizedBox(height: 16),
        if (!_guest)
          TextButton.icon(
            onPressed: _pickProfileImage,
            icon: const Icon(Icons.photo_camera_outlined),
            label: const Text('Change profile picture'),
          ),
        if (!_guest)
          TextButton.icon(
            onPressed: _editDisplayName,
            icon: const Icon(Icons.edit_outlined),
            label: const Text('Edit name'),
          ),
        Text(
          _guest
              ? 'Guest'
              : (_username.isNotEmpty
                  ? _username
                  : ((_email != null && _email!.contains('@'))
                      ? _email!.split('@').first
                      : 'User')),
          textAlign: TextAlign.center,
          style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: AppColors.purpleDark),
        ),
        if (!_guest && _email != null)
          Text(_email!,
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.greySubtitle)),
        if (!_guest && _joinedAt != null && _joinedAt!.isNotEmpty)
          Text(
            'Joined app: ${_joinedAt!.substring(0, 10)}',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.greySubtitle, fontSize: 12),
          ),
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
          Navigator.push(context,
              MaterialPageRoute(builder: (_) => const InsightsScreen()));
        }),
        _item(Icons.history_rounded, 'Dupe history ($_dupeHistoryCount)', () {
          Navigator.push(context,
              MaterialPageRoute(builder: (_) => const DupeHistoryScreen()));
        }),
        if (!_guest && _notifications.isNotEmpty) ...[
          const SizedBox(height: 8),
          const Text(
            'Recent notifications',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: AppColors.purpleDark,
            ),
          ),
          const SizedBox(height: 8),
          ..._notifications.take(3).map(
                (n) => Card(
                  margin: const EdgeInsets.only(bottom: 8),
                  child: ListTile(
                    title: Text(n.message),
                    subtitle: Text(
                      n.replyPreview.isEmpty
                          ? 'Tap to open your post'
                          : n.replyPreview,
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
          _item(Icons.login_rounded, 'Log in / Sign up', () {
            Navigator.of(context)
                .pushNamedAndRemoveUntil('/welcome', (r) => false);
          }),
        const Divider(height: 32),
        ListTile(
          leading: const Icon(Icons.logout_rounded, color: Colors.redAccent),
          title: const Text('Sign out',
              style: TextStyle(
                  color: Colors.redAccent, fontWeight: FontWeight.w600)),
          onTap: _logout,
        ),
      ],
    );
  }

  Widget _item(IconData icon, String title, VoidCallback onTap) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(AppDecor.cardRadius)),
      child: ListTile(
        leading: Icon(icon, color: AppColors.bluePrimary),
        title: Text(title,
            style: const TextStyle(
                color: AppColors.purpleDark, fontWeight: FontWeight.w500)),
        trailing: const Icon(Icons.chevron_right_rounded,
            color: AppColors.greySubtitle),
        onTap: onTap,
      ),
    );
  }
}
