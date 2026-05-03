import 'package:flutter/foundation.dart';

/// Signals [MeScreen] (and similar) to reload stats. Bumped after dupe outbound
/// clicks and similarity searches so IndexedStack-hidden Me stays current.
class ProfileStatsRefresh {
  ProfileStatsRefresh._();
  static final ProfileStatsRefresh instance = ProfileStatsRefresh._();

  final ValueNotifier<int> tick = ValueNotifier(0);

  void notify() {
    tick.value++;
  }
}
