import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

String _coerceId(dynamic v) {
  if (v == null) return '';
  if (v is String) return v;
  return v.toString();
}

String? _coerceIdNullable(dynamic v) {
  if (v == null) return null;
  if (v is String) return v;
  return v.toString();
}

/// True when this post belongs to the logged-in user (matches [user_id] first, then name heuristics).
bool _isOwnCommunityPost(Map<String, dynamic> map, SharedPreferences prefs) {
  final myUserId = (prefs.getString('user_id') ?? '').trim();
  final authorUserId =
      (map['authorUserId'] ?? map['author_user_id'] ?? '').toString().trim();
  if (myUserId.isNotEmpty &&
      authorUserId.isNotEmpty &&
      authorUserId == myUserId) {
    return true;
  }
  final author = (map['author'] ?? '').toString().trim().toLowerCase();
  final currentUsername =
      (prefs.getString('user_name') ?? '').trim().toLowerCase();
  final currentEmailPrefix =
      ((prefs.getString('user_email') ?? '').trim().split('@').first)
          .toLowerCase();
  return (currentUsername.isNotEmpty && author == currentUsername) ||
      (currentEmailPrefix.isNotEmpty && author == currentEmailPrefix);
}

/// Backend sends UTC timestamps without a `Z` suffix; treat naive ISO as UTC.
DateTime parseCommunityServerDate(String? s) {
  if (s == null || s.isEmpty) return DateTime.now().toUtc();
  final parsed = DateTime.tryParse(s);
  if (parsed == null) return DateTime.now().toUtc();
  final t = s.trim();
  final hasExplicitTz = t.endsWith('Z') ||
      RegExp(r'[+-]\d{2}:?\d{2}$').hasMatch(t);
  if (hasExplicitTz) return parsed.toUtc();
  return DateTime.utc(
    parsed.year,
    parsed.month,
    parsed.day,
    parsed.hour,
    parsed.minute,
    parsed.second,
    parsed.millisecond,
    parsed.microsecond,
  );
}

class CommunityPost {
  final String id;
  final String description;
  final String author;
  final String? authorUserId;
  final String? authorPfp;
  final String? imageBase64;
  /// True when server stripped image from feed (`lite`) but post has a photo.
  final bool hasImage;
  final DateTime createdAt;
  final List<CommunityReply> replies;
  final int likeCount;
  final bool likedByMe;

  CommunityPost({
    required this.id,
    required this.description,
    this.author = 'You',
    this.authorUserId,
    this.authorPfp,
    this.imageBase64,
    this.hasImage = false,
    required this.createdAt,
    List<CommunityReply>? replies,
    this.likeCount = 0,
    this.likedByMe = false,
  }) : replies = replies ?? [];

  Map<String, dynamic> toJson() => {
        'id': id,
        'description': description,
        'author': author,
        'authorUserId': authorUserId,
        'authorPfp': authorPfp,
        'imageBase64': imageBase64,
        'hasImage': hasImage,
        'createdAt': createdAt.toIso8601String(),
        'likeCount': likeCount,
        'likedByMe': likedByMe,
        'replies': replies.map((r) => r.toJson()).toList(),
      };

  static CommunityPost fromJson(Map<String, dynamic> m) {
    final img = m['imageBase64'] as String?;
    final hasImg = m['hasImage'] == true ||
        (img != null && img.trim().isNotEmpty);
    return CommunityPost(
      id: _coerceId(m['id'] ?? m['_id']),
      description: (m['description'] ?? '').toString(),
      author: (m['author'] ?? 'You').toString(),
      authorUserId: _coerceIdNullable(m['authorUserId']),
      authorPfp: m['authorPfp'] as String?,
      imageBase64: img,
      hasImage: hasImg,
      createdAt: parseCommunityServerDate(m['createdAt'] as String?),
      likeCount: (m['likeCount'] as num?)?.toInt() ??
          (m['like_count'] as num?)?.toInt() ??
          0,
      likedByMe: m['likedByMe'] == true,
      replies: (m['replies'] as List<dynamic>?)
              ?.map((e) =>
                  CommunityReply.fromJson(Map<String, dynamic>.from(e as Map)))
              .toList() ??
          [],
    );
  }
}

class CommunityReply {
  final String id;
  final String body;
  final String author;
  final String? authorPfp;
  final String? authorUserId;
  final String? parentReplyId;
  final DateTime createdAt;

  CommunityReply({
    required this.id,
    required this.body,
    this.author = 'Anonymous',
    this.authorPfp,
    this.authorUserId,
    this.parentReplyId,
    required this.createdAt,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'body': body,
        'author': author,
        'authorPfp': authorPfp,
        'authorUserId': authorUserId,
        'parentReplyId': parentReplyId,
        'createdAt': createdAt.toIso8601String(),
      };

  static CommunityReply fromJson(Map<String, dynamic> m) {
    return CommunityReply(
      id: _coerceId(m['id']),
      body: (m['body'] ?? '').toString(),
      author: (m['author'] ?? 'Anonymous').toString(),
      authorPfp: m['authorPfp'] as String?,
      authorUserId: _coerceIdNullable(m['authorUserId']),
      parentReplyId: _coerceIdNullable(m['parentReplyId']),
      createdAt: parseCommunityServerDate(m['createdAt'] as String?),
    );
  }
}

class CommunityNotification {
  final String id;
  final String postId;
  final String replyId;
  final String message;
  final bool isRead;
  final DateTime createdAt;
  final String actorName;
  final String replyPreview;

  CommunityNotification({
    required this.id,
    required this.postId,
    required this.replyId,
    required this.message,
    required this.isRead,
    required this.createdAt,
    required this.actorName,
    required this.replyPreview,
  });

  static CommunityNotification fromJson(Map<String, dynamic> m) {
    return CommunityNotification(
      id: (m['id'] ?? '').toString(),
      postId: (m['postId'] ?? '').toString(),
      replyId: (m['replyId'] ?? '').toString(),
      message: (m['message'] ?? 'Someone replied to your post').toString(),
      isRead: m['isRead'] == true,
      createdAt: DateTime.tryParse((m['createdAt'] ?? '').toString()) ??
          DateTime.now(),
      actorName: (m['actorName'] ?? 'Someone').toString(),
      replyPreview: (m['replyPreview'] ?? '').toString(),
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
  static const _postsCacheKey = 'community_posts_cache_v1';
  static const _postsCacheAtKey = 'community_posts_cache_at_v1';
  static const Duration _postsCacheTtl = Duration(seconds: 45);
  List<CommunityPost>? _postsCache;
  DateTime? _postsCacheAt;
  /// Last fetch error message (for UI hints). Cleared on success.
  String? lastPostsFetchError;

  Future<List<CommunityPost>> getPosts({bool forceRefresh = false}) async {
    // Always hydrate from disk when memory is empty (even on forceRefresh)
    // so a failed network refresh does not drop previously cached posts.
    if (_postsCache == null) {
      final disk = await _readPostsCacheFromDisk();
      if (disk.isNotEmpty) {
        _postsCache = disk;
        _postsCacheAt = DateTime.now();
      }
    }
    if (!forceRefresh &&
        _postsCache != null &&
        _postsCacheAt != null &&
        DateTime.now().difference(_postsCacheAt!) < _postsCacheTtl) {
      lastPostsFetchError = null;
      return _postsCache!
          .map((e) => CommunityPost.fromJson(e.toJson()))
          .toList();
    }
    try {
      await _migrateLegacyIfNeeded();
      final list = await _api.getCommunityPosts();
      final prefs = await SharedPreferences.getInstance();
      final currentDisplayName = (prefs.getString(_usernameKey) ?? '').trim();
      final currentPfp = prefs.getString(_profileImageKey);
      final parsed = <CommunityPost>[];
      for (final e in list) {
        try {
          final map = Map<String, dynamic>.from(e as Map);
          final isCurrentUserPost = _isOwnCommunityPost(map, prefs);
          if (isCurrentUserPost && currentDisplayName.isNotEmpty) {
            map['author'] = currentDisplayName;
          }
          final hasPfp =
              (map['authorPfp'] as String?)?.trim().isNotEmpty == true;
          if (!hasPfp &&
              currentPfp != null &&
              currentPfp.isNotEmpty &&
              isCurrentUserPost) {
            map['authorPfp'] = currentPfp;
          }
          if (isCurrentUserPost) {
            final eff = (map['authorPfp'] as String?)?.trim();
            if (eff != null &&
                eff.isNotEmpty &&
                (prefs.getString(_profileImageKey) ?? '').trim().isEmpty) {
              await prefs.setString(_profileImageKey, eff);
            }
          }
          parsed.add(CommunityPost.fromJson(map));
        } catch (err, st) {
          debugPrint('CommunityService: skip bad post JSON: $err\n$st');
        }
      }
      _postsCache = parsed;
      _postsCacheAt = DateTime.now();
      lastPostsFetchError = null;
      await _savePostsCacheToDisk(parsed);
      return parsed.map((e) => CommunityPost.fromJson(e.toJson())).toList();
    } catch (e, st) {
      debugPrint('CommunityService.getPosts failed: $e\n$st');
      lastPostsFetchError = e.toString();
      final fromDisk = await _readPostsCacheFromDisk();
      if (fromDisk.isNotEmpty) {
        _postsCache = fromDisk;
        _postsCacheAt = DateTime.now();
        return fromDisk.map((e) => CommunityPost.fromJson(e.toJson())).toList();
      }
      return _postsCache
              ?.map((e) => CommunityPost.fromJson(e.toJson()))
              .toList() ??
          [];
    }
  }

  /// Full post with image (feed list is lite — omit large base64).
  Future<CommunityPost> fetchPostById(String postId) async {
    final map = Map<String, dynamic>.from(await _api.getCommunityPost(postId));
    final prefs = await SharedPreferences.getInstance();
    final currentDisplayName = (prefs.getString(_usernameKey) ?? '').trim();
    final currentPfp = prefs.getString(_profileImageKey);
    final isCurrentUserPost = _isOwnCommunityPost(map, prefs);
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
    if (isCurrentUserPost) {
      final eff = (map['authorPfp'] as String?)?.trim();
      if (eff != null &&
          eff.isNotEmpty &&
          (prefs.getString(_profileImageKey) ?? '').trim().isEmpty) {
        await prefs.setString(_profileImageKey, eff);
      }
    }
    return CommunityPost.fromJson(map);
  }

  Future<List<CommunityPost>> getCachedPostsFast() async {
    if (_postsCache != null && _postsCache!.isNotEmpty) {
      return _postsCache!
          .map((e) => CommunityPost.fromJson(e.toJson()))
          .toList();
    }
    final disk = await _readPostsCacheFromDisk();
    if (disk.isNotEmpty) {
      _postsCache = disk;
      _postsCacheAt = DateTime.now();
    }
    return disk.map((e) => CommunityPost.fromJson(e.toJson())).toList();
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

  Future<CommunityPost> addPost(String description, {String? imageBase64}) async {
    final prefs = await SharedPreferences.getInstance();
    final username = (prefs.getString(_usernameKey) ?? '').trim();
    final email = (prefs.getString(_emailKey) ?? '').trim();
    final author = username.isNotEmpty
        ? username
        : (email.isNotEmpty ? email.split('@').first : 'User');
    final pfp = prefs.getString(_profileImageKey);
    final post = await _api.addCommunityPost(
      description: description,
      author: author,
      authorPfp: pfp,
      imageBase64: imageBase64,
    );
    final parsed = CommunityPost.fromJson(post);
    final existing = _postsCache ?? await _readPostsCacheFromDisk();
    _postsCache = [
      parsed,
      ...existing.where((p) => p.id != parsed.id),
    ];
    _postsCacheAt = DateTime.now();
    await _savePostsCacheToDisk(_postsCache!);
    return parsed;
  }

  Future<CommunityPost> addReply(String postId, String body,
      {String? parentReplyId}) async {
    final prefs = await SharedPreferences.getInstance();
    final username = (prefs.getString(_usernameKey) ?? '').trim();
    final email = (prefs.getString(_emailKey) ?? '').trim();
    final author = username.isNotEmpty
        ? username
        : (email.isNotEmpty ? email.split('@').first : 'User');
    final pfp = prefs.getString(_profileImageKey);
    final post = await _api.addCommunityReply(
      postId: postId,
      body: body,
      author: author,
      authorPfp: pfp,
      parentReplyId: parentReplyId,
    );
    final parsed = CommunityPost.fromJson(post);
    if (_postsCache != null) {
      final idx = _postsCache!.indexWhere((p) => p.id == parsed.id);
      if (idx >= 0) {
        _postsCache![idx] = parsed;
      }
    }
    _postsCacheAt = DateTime.now();
    await _savePostsCacheToDisk(_postsCache ?? [parsed]);
    return parsed;
  }

  Future<void> deleteReply(String postId, String replyId) async {
    await _api.deleteCommunityReply(postId: postId, replyId: replyId);
    _postsCacheAt = null;
  }

  Future<void> deletePost(String postId) async {
    await _api.deleteCommunityPost(postId);
    _postsCacheAt = null;
  }

  Future<void> editPost(String postId, String description) async {
    await _api.editCommunityPost(postId: postId, description: description);
    _postsCacheAt = null;
  }

  Future<CommunityPost> togglePostLike(String postId) async {
    final map = await _api.toggleCommunityPostLike(postId);
    final parsed = CommunityPost.fromJson(map);
    if (_postsCache != null) {
      final idx = _postsCache!.indexWhere((p) => p.id == parsed.id);
      if (idx >= 0) {
        _postsCache![idx] = parsed;
      }
    }
    _postsCacheAt = DateTime.now();
    await _savePostsCacheToDisk(_postsCache ?? [parsed]);
    return parsed;
  }

  Future<void> reportPost(String postId, String reason) async {
    await _api.reportCommunityPost(postId: postId, reason: reason);
  }

  Future<void> reportReply({
    required String postId,
    required String replyId,
    required String reason,
  }) async {
    await _api.reportCommunityReply(
      postId: postId,
      replyId: replyId,
      reason: reason,
    );
  }

  Future<void> blockUser(String targetUserId) async {
    await _api.blockCommunityUser(targetUserId);
    _postsCacheAt = null;
  }

  Future<String?> currentUserId() async {
    final prefs = await SharedPreferences.getInstance();
    final id = prefs.getString(_userIdKey)?.trim();
    if (id == null || id.isEmpty) return null;
    return id;
  }

  Future<List<CommunityNotification>> getNotifications({
    int limit = 20,
    bool unreadOnly = false,
  }) async {
    final body = await _api.getCommunityNotifications(
      limit: limit,
      unreadOnly: unreadOnly,
    );
    final notifications = (body['notifications'] as List<dynamic>? ?? [])
        .map((e) =>
            CommunityNotification.fromJson(Map<String, dynamic>.from(e as Map)))
        .toList();
    return notifications;
  }

  Future<int> unreadNotificationsCount() async {
    final body =
        await _api.getCommunityNotifications(limit: 1, unreadOnly: false);
    return (body['unreadCount'] as num?)?.toInt() ?? 0;
  }

  Future<int> markNotificationRead(String notificationId) async {
    return _api.markCommunityNotificationRead(notificationId);
  }

  Future<void> _savePostsCacheToDisk(List<CommunityPost> posts) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final encoded = jsonEncode(posts.map((e) => e.toJson()).toList());
      await prefs.setString(_postsCacheKey, encoded);
      await prefs.setString(_postsCacheAtKey, DateTime.now().toIso8601String());
    } catch (_) {}
  }

  Future<List<CommunityPost>> _readPostsCacheFromDisk() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final raw = prefs.getString(_postsCacheKey);
      if (raw == null || raw.isEmpty) return [];
      final atRaw = prefs.getString(_postsCacheAtKey);
      final at = DateTime.tryParse(atRaw ?? '');
      if (at != null && DateTime.now().difference(at) > const Duration(hours: 6)) {
        return [];
      }
      final decoded = jsonDecode(raw) as List<dynamic>;
      return decoded
          .map((e) => CommunityPost.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }
}
