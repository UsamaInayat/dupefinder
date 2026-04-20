import 'package:flutter/material.dart';
import 'dart:convert';
import '../theme/app_theme.dart';
import '../services/community_service.dart';
import '../services/dupe_history_service.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'home_tab.dart';
import 'search/image_search_screen.dart';
import 'wishlist_screen.dart';
import 'compare_screen.dart';
import 'community_screen.dart';
import 'me_screen.dart';
import 'dupe_history_screen.dart';

/// Bottom navigation: Home | Search | Saved | Compare | Community | Me
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  /// SharedPreferences key for last selected tab; clear on login so Home opens first.
  static const String lastTabPreferenceKey = 'main_shell_last_tab';

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;
  /// Build only visited tabs to keep startup responsive on physical devices.
  final Set<int> _loadedTabs = {0};
  final _dupeHistoryService = DupeHistoryService();
  final _communityService = CommunityService();
  String? _navProfileImage;
  int _unreadCommunityNotifications = 0;
  String? _focusCommunityPostId;
  String? _focusCommunityReplyId;

  @override
  void initState() {
    super.initState();
    _restoreState();
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      // Defer non-critical IO so first frame and first interactions stay snappy.
      await Future<void>.delayed(const Duration(milliseconds: 700));
      if (!mounted) return;
      await _maybeShowReviewPrompt();
      _refreshCommunityNotificationCount();
    });
  }

  Future<void> _restoreState() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getInt(MainShell.lastTabPreferenceKey) ?? 0;
    final pfp = prefs.getString('user_profile_image');
    if (!mounted) return;
    setState(() {
      _index = (saved >= 0 && saved <= 5) ? saved : 0;
      _loadedTabs.add(_index);
      _navProfileImage = (pfp != null && pfp.isNotEmpty) ? pfp : null;
    });
  }

  Future<void> _saveCurrentTab() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt(MainShell.lastTabPreferenceKey, _index);
  }

  Future<void> _refreshNavProfile() async {
    final prefs = await SharedPreferences.getInstance();
    final pfp = prefs.getString('user_profile_image');
    if (!mounted) return;
    setState(() {
      _navProfileImage = (pfp != null && pfp.isNotEmpty) ? pfp : null;
    });
  }

  Future<void> _refreshCommunityNotificationCount() async {
    try {
      final count = await _communityService.unreadNotificationsCount();
      if (!mounted) return;
      setState(() => _unreadCommunityNotifications = count);
    } catch (_) {}
  }

  Future<void> _maybeShowReviewPrompt() async {
    if (!mounted) return;
    final pending = await _dupeHistoryService.nextPendingPrompt();
    if (pending == null || !mounted) return;
    final name = pending.product['name']?.toString() ?? 'this item';
    final brand = pending.product['brand']?.toString() ?? 'store';
    await _dupeHistoryService.markPromptShown(pending.id);
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Quick review'),
        content: Text(
          'Hey, did you like "$name" from $brand? '
          'If yes, you can review it with stars.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Later'),
          ),
          FilledButton(
            onPressed: () {
              Navigator.pop(ctx);
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const DupeHistoryScreen()),
              );
            },
            child: const Text('Review now'),
          ),
        ],
      ),
    );
  }

  void _openTab(int targetIndex) {
    setState(() {
      _index = targetIndex;
      _loadedTabs.add(targetIndex);
    });
    _saveCurrentTab();
    if (targetIndex == 5) {
      _refreshNavProfile();
    }
    if (targetIndex == 4 || targetIndex == 5) {
      _refreshCommunityNotificationCount();
    }
  }

  Future<void> _openCommunityFromNotification(
    String postId,
    String replyId,
    String notificationId,
  ) async {
    if (notificationId.isEmpty) {
      // Keep signature consistent; id can be used for future analytics/debugging.
    }
    if (!mounted) return;
    setState(() {
      _focusCommunityPostId = postId;
      _focusCommunityReplyId = replyId;
      _index = 4;
      _loadedTabs.add(4);
    });
    await _saveCurrentTab();
    // Fire and forget to keep navigation snappy.
    _refreshCommunityNotificationCount();
  }

  @override
  Widget build(BuildContext context) {
    Widget baseMeIcon(bool selected) {
      if (_navProfileImage != null) {
        return CircleAvatar(
          radius: 12,
          backgroundImage: MemoryImage(base64Decode(_navProfileImage!)),
        );
      }
      return Icon(
          selected ? Icons.person_rounded : Icons.person_outline_rounded);
    }

    Widget badgeWrap(Widget icon) {
      if (_unreadCommunityNotifications <= 0) return icon;
      return Stack(
        clipBehavior: Clip.none,
        children: [
          icon,
          Positioned(
            right: -2,
            top: -2,
            child: Container(
              width: 8,
              height: 8,
              decoration: const BoxDecoration(
                color: Colors.redAccent,
                shape: BoxShape.circle,
              ),
            ),
          ),
        ],
      );
    }

    Widget lazyTab(int tabIndex, Widget child) {
      if (_loadedTabs.contains(tabIndex)) return child;
      return const SizedBox.shrink();
    }

    return Scaffold(
      body: IndexedStack(
        index: _index,
        children: [
          lazyTab(
            0,
            HomeTab(
              onOpenSearch: () => _openTab(1),
            ),
          ),
          lazyTab(1, const ImageSearchScreen(embedded: true)),
          lazyTab(2, const WishlistScreen()),
          lazyTab(3, const CompareScreen()),
          lazyTab(
            4,
            CommunityScreen(
              embedded: true,
              feedPollActive: _index == 4,
              focusPostId: _focusCommunityPostId,
              focusReplyId: _focusCommunityReplyId,
            ),
          ),
          lazyTab(
            5,
            MeScreen(
              onOpenCommunityFromNotification: _openCommunityFromNotification,
              onNotificationStateChanged: _refreshCommunityNotificationCount,
            ),
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        backgroundColor: Colors.white,
        surfaceTintColor: Colors.transparent,
        shadowColor: Colors.transparent,
        elevation: 0,
        selectedIndex: _index,
        onDestinationSelected: (i) {
          _openTab(i);
        },
        indicatorColor: DupePalette.pink.withValues(alpha: 0.22),
        labelBehavior: NavigationDestinationLabelBehavior.alwaysShow,
        destinations: [
          const NavigationDestination(
              icon: Icon(Icons.home_outlined),
              selectedIcon: Icon(Icons.home_rounded),
              label: 'Home'),
          const NavigationDestination(
              icon: Icon(Icons.image_search_outlined),
              selectedIcon: Icon(Icons.image_search_rounded),
              label: 'Search'),
          const NavigationDestination(
              icon: Icon(Icons.favorite_outline),
              selectedIcon: Icon(Icons.favorite_rounded),
              label: 'Saved'),
          const NavigationDestination(
              icon: Icon(Icons.compare_arrows_outlined),
              selectedIcon: Icon(Icons.compare_arrows_rounded),
              label: 'Compare'),
          const NavigationDestination(
              icon: Icon(Icons.forum_outlined),
              selectedIcon: Icon(Icons.forum_rounded),
              label: 'Community'),
          NavigationDestination(
            icon: badgeWrap(baseMeIcon(false)),
            selectedIcon: badgeWrap(baseMeIcon(true)),
            label: 'Me',
          ),
        ],
      ),
    );
  }
}
