import 'package:flutter/material.dart';
import 'dart:convert';
import '../theme/app_theme.dart';
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
  int _wishlistRefreshKey = 0;
  int _compareRefreshKey = 0;
  final _dupeHistoryService = DupeHistoryService();
  String? _navProfileImage;

  @override
  void initState() {
    super.initState();
    _restoreState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeShowReviewPrompt());
  }

  Future<void> _restoreState() async {
    final prefs = await SharedPreferences.getInstance();
    final saved = prefs.getInt(_lastTabKey) ?? 0;
    final pfp = prefs.getString('user_profile_image');
    if (!mounted) return;
    setState(() {
      _index = (saved >= 0 && saved <= 5) ? saved : 0;
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
      if (targetIndex == 2) _wishlistRefreshKey++;
      if (targetIndex == 3) _compareRefreshKey++;
    });
    _saveCurrentTab();
    _refreshNavProfile();
  }

  void _openInsightsPage() {
    Navigator.push(
      context,
      MaterialPageRoute(builder: (_) => const InsightsScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    final titles = ['DupeFinder', 'Find similar', 'Wishlist', 'Compare', 'Community', 'Me'];
    final Widget meIcon = (_navProfileImage != null)
        ? CircleAvatar(
            radius: 12,
            backgroundImage: MemoryImage(base64Decode(_navProfileImage!)),
          )
        : const Icon(Icons.person_outline_rounded);
    final Widget meSelectedIcon = (_navProfileImage != null)
        ? CircleAvatar(
            radius: 12,
            backgroundImage: MemoryImage(base64Decode(_navProfileImage!)),
          )
        : const Icon(Icons.person_rounded);
    return Scaffold(
      appBar: AppBar(
        title: Text(titles[_index]),
        actions: [
          if (_index == 0)
            IconButton(
              icon: const Icon(Icons.search_rounded),
              onPressed: () => setState(() => _index = 1),
              tooltip: 'Find similar',
            ),
        ],
      ),
      body: IndexedStack(
        index: _index,
        children: [
          HomeTab(
            onOpenSearch: () => _openTab(1),
            onOpenCompare: () => _openTab(3),
            onOpenWishlist: () => _openTab(2),
            onOpenInsights: _openInsightsPage,
          ),
          const ImageSearchScreen(embedded: true),
          WishlistScreen(refreshKey: _wishlistRefreshKey),
          CompareScreen(refreshKey: _compareRefreshKey),
          const CommunityScreen(embedded: true),
          const MeScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) {
          _openTab(i);
        },
        indicatorColor: AppColors.bluePrimary.withValues(alpha: 0.2),
        destinations: [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.image_search_outlined), selectedIcon: Icon(Icons.image_search_rounded), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.favorite_outline), selectedIcon: Icon(Icons.favorite_rounded), label: 'Saved'),
          NavigationDestination(icon: Icon(Icons.compare_arrows_outlined), selectedIcon: Icon(Icons.compare_arrows_rounded), label: 'Compare'),
          NavigationDestination(icon: Icon(Icons.forum_outlined), selectedIcon: Icon(Icons.forum_rounded), label: 'Community'),
          NavigationDestination(icon: meIcon, selectedIcon: meSelectedIcon, label: 'Me'),
        ],
      ),
    );
  }
}
