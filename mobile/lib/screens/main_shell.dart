import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'home_tab.dart';
import 'search/image_search_screen.dart';
import 'wishlist_screen.dart';
import 'compare_screen.dart';
import 'community_screen.dart';
import 'me_screen.dart';

/// Bottom navigation: Home | Search | Saved | Compare | Community | Me
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;
  int _wishlistRefreshKey = 0;
  int _compareRefreshKey = 0;

  @override
  Widget build(BuildContext context) {
    final titles = ['DupeFinder', 'Find similar', 'Wishlist', 'Compare', 'Community', 'Me'];
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
          HomeTab(onOpenSearch: () => setState(() => _index = 1)),
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
          setState(() {
            _index = i;
            if (i == 2) _wishlistRefreshKey++;
            if (i == 3) _compareRefreshKey++;
          });
        },
        indicatorColor: AppColors.bluePrimary.withValues(alpha: 0.2),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home_rounded), label: 'Home'),
          NavigationDestination(icon: Icon(Icons.image_search_outlined), selectedIcon: Icon(Icons.image_search_rounded), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.favorite_outline), selectedIcon: Icon(Icons.favorite_rounded), label: 'Saved'),
          NavigationDestination(icon: Icon(Icons.compare_arrows_outlined), selectedIcon: Icon(Icons.compare_arrows_rounded), label: 'Compare'),
          NavigationDestination(icon: Icon(Icons.forum_outlined), selectedIcon: Icon(Icons.forum_rounded), label: 'Community'),
          NavigationDestination(icon: Icon(Icons.person_outline_rounded), selectedIcon: Icon(Icons.person_rounded), label: 'Me'),
        ],
      ),
    );
  }
}
