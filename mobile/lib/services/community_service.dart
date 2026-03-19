import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class CommunityPost {
  final String id;
  final String description;
  final String author;
  final String? authorUserId;
  final String? authorPfp;
  final String? imageBase64;
  final DateTime createdAt;
  final List<CommunityReply> replies;

  CommunityPost({
    required this.id,
    required this.description,
    this.author = 'You',
    this.authorUserId,
    this.authorPfp,
    this.imageBase64,
    required this.createdAt,
    List<CommunityReply>? replies,
  }) : replies = replies ?? [];

  Map<String, dynamic> toJson() => {
        'id': id,
        'description': description,
        'author': author,
        'authorUserId': authorUserId,
        'authorPfp': authorPfp,
        'imageBase64': imageBase64,
        'createdAt': createdAt.toIso8601String(),
        'replies': replies.map((r) => r.toJson()).toList(),
      };

  static CommunityPost fromJson(Map<String, dynamic> m) {
    return CommunityPost(
      id: m['id'] as String? ?? '',
      description: m['description'] as String? ?? '',
      author: m['author'] as String? ?? 'You',
      authorUserId: m['authorUserId'] as String?,
      authorPfp: m['authorPfp'] as String?,
      imageBase64: m['imageBase64'] as String?,
      createdAt: DateTime.tryParse(m['createdAt'] as String? ?? '') ?? DateTime.now(),
      replies: (m['replies'] as List<dynamic>?)
              ?.map((e) => CommunityReply.fromJson(Map<String, dynamic>.from(e as Map)))
              .toList() ??
          [],
    );
  }
}

class CommunityReply {
  final String body;
  final String author;
  final DateTime createdAt;

  CommunityReply({required this.body, this.author = 'Anonymous', required this.createdAt});

  Map<String, dynamic> toJson() => {
        'body': body,
        'author': author,
        'createdAt': createdAt.toIso8601String(),
      };

  static CommunityReply fromJson(Map<String, dynamic> m) {
    return CommunityReply(
      body: m['body'] as String? ?? '',
      author: m['author'] as String? ?? 'Anonymous',
      createdAt: DateTime.tryParse(m['createdAt'] as String? ?? '') ?? DateTime.now(),
    );
  }
}

class CommunityService {
  final _api = ApiService();
  static const _legacyKey = 'community_posts_db';
  static const _legacyMigratedKey = 'community_posts_db_migrated';
  static const _usernameKey = 'user_name';
  static const _emailKey = 'user_email';
  static const _profileImageKey = 'user_profile_image';
  static const _userIdKey = 'user_id';

  Future<List<CommunityPost>> getPosts() async {
    try {
      await _api.syncUserProfileFromBackend();
      await _migrateLegacyIfNeeded();
      final list = await _api.getCommunityPosts();
      final prefs = await SharedPreferences.getInstance();
      final currentUsername = (prefs.getString(_usernameKey) ?? '').trim().toLowerCase();
      final currentDisplayName = (prefs.getString(_usernameKey) ?? '').trim();
      final currentEmailPrefix = ((prefs.getString(_emailKey) ?? '').trim().split('@').first).toLowerCase();
      final currentPfp = prefs.getString(_profileImageKey);
      return list.map((e) {
        final map = Map<String, dynamic>.from(e);
        final author = (map['author'] as String? ?? '').trim().toLowerCase();
        final isCurrentUserPost = (currentUsername.isNotEmpty && author == currentUsername) ||
            (currentEmailPrefix.isNotEmpty && author == currentEmailPrefix);
        if (isCurrentUserPost && currentDisplayName.isNotEmpty) {
          map['author'] = currentDisplayName;
        }
        final hasPfp = (map['authorPfp'] as String?)?.trim().isNotEmpty == true;
        if (!hasPfp &&
            currentPfp != null &&
            currentPfp.isNotEmpty &&
            isCurrentUserPost) {
          map['authorPfp'] = currentPfp;
        }
        return CommunityPost.fromJson(map);
      }).toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _migrateLegacyIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    final migrated = prefs.getBool(_legacyMigratedKey) == true;
    if (migrated) return;

    final raw = prefs.getString(_legacyKey);
    if (raw == null || raw.isEmpty) {
      await prefs.setBool(_legacyMigratedKey, true);
      return;
    }

    try {
      final decoded = jsonDecode(raw) as List<dynamic>;
      for (final item in decoded) {
        final map = Map<String, dynamic>.from(item as Map);
        final post = CommunityPost.fromJson(map);
        if (post.description.trim().isEmpty) continue;
        await _api.addCommunityPost(
          description: post.description,
          author: post.author,
          authorPfp: post.authorPfp,
          imageBase64: post.imageBase64,
        );
      }
      await prefs.setBool(_legacyMigratedKey, true);
    } catch (_) {
      await prefs.setBool(_legacyMigratedKey, true);
    }
  }

  Future<void> addPost(String description, {String? imageBase64}) async {
    await _api.syncUserProfileFromBackend();
    final prefs = await SharedPreferences.getInstance();
    final username = (prefs.getString(_usernameKey) ?? '').trim();
    final email = (prefs.getString(_emailKey) ?? '').trim();
    final author = username.isNotEmpty
        ? username
        : (email.isNotEmpty ? email.split('@').first : 'User');
    final pfp = prefs.getString(_profileImageKey);
    await _api.addCommunityPost(
      description: description,
      author: author,
      authorPfp: pfp,
      imageBase64: imageBase64,
    );
  }

  Future<void> addReply(String postId, String body) async {
    await _api.syncUserProfileFromBackend();
    final prefs = await SharedPreferences.getInstance();
    final username = (prefs.getString(_usernameKey) ?? '').trim();
    final email = (prefs.getString(_emailKey) ?? '').trim();
    final author = username.isNotEmpty
        ? username
        : (email.isNotEmpty ? email.split('@').first : 'User');
    await _api.addCommunityReply(
      postId: postId,
      body: body,
      author: author,
    );
  }

  Future<void> deletePost(String postId) async {
    await _api.deleteCommunityPost(postId);
  }

  Future<void> editPost(String postId, String description) async {
    await _api.editCommunityPost(postId: postId, description: description);
  }

  Future<void> reportPost(String postId, String reason) async {
    await _api.reportCommunityPost(postId: postId, reason: reason);
  }

  Future<String?> currentUserId() async {
    final prefs = await SharedPreferences.getInstance();
    final id = prefs.getString(_userIdKey)?.trim();
    if (id == null || id.isEmpty) return null;
    return id;
  }
}
