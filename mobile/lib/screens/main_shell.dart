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
import 'insights_screen.dart';

/// Bottom navigation: Home | Search | Saved | Compare | Community | Me
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  static const _lastTabKey = 'main_shell_last_tab';
  int _index = 0;
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
    WidgetsBinding.instance
        .addPostFrameCallback((_) => _maybeShowReviewPrompt());
    WidgetsBinding.instance
        .addPostFrameCallback((_) => _refreshCommunityNotificationCount());
  }

  Future<void> _restoreState() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getInt(_lastTabKey) ?? 0;
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
    await prefs.setInt(_lastTabKey, _index);
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
    _refreshNavProfile();
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

  void _openInsightsPage() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const InsightsScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final titles = [
      'DupeFinder',
      'Find similar',
      'Wishlist',
      'Compare',
      'Community',
      'Me'
    ];
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
      appBar: AppBar(
        title: Text(titles[_index]),
        actions: [
          if (_index == 0)
            IconButton(
              icon: const Icon(Icons.search_rounded),
              onPressed: () => _openTab(1),
              tooltip: 'Find similar',
            ),
        ],
      ),
      body: IndexedStack(
        index: _index,
        children: [
          lazyTab(
            0,
            HomeTab(
              onOpenSearch: () => _openTab(1),
              onOpenCompare: () => _openTab(3),
              onOpenWishlist: () => _openTab(2),
              onOpenInsights: _openInsightsPage,
            ),
          ),
          lazyTab(1, const ImageSearchScreen(embedded: true)),
          lazyTab(2, const WishlistScreen()),
          lazyTab(3, const CompareScreen()),
          lazyTab(
            4,
            CommunityScreen(
              embedded: true,
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
        selectedIndex: _index,
        onDestinationSelected: (i) {
          _openTab(i);
        },
        indicatorColor: AppColors.bluePrimary.withValues(alpha: 0.2),
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
