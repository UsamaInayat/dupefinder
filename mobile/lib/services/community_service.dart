import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class CommunityPost {
  final String id;
  final String title;
  final String body;
  final String author;
  final DateTime createdAt;
  final List<CommunityReply> replies;

  CommunityPost({
    required this.id,
    required this.title,
    required this.body,
    this.author = 'You',
    required this.createdAt,
    List<CommunityReply>? replies,
  }) : replies = replies ?? [];

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'body': body,
        'author': author,
        'createdAt': createdAt.toIso8601String(),
        'replies': replies.map((r) => r.toJson()).toList(),
      };

  static CommunityPost fromJson(Map<String, dynamic> m) {
    return CommunityPost(
      id: m['id'] as String? ?? '',
      title: m['title'] as String? ?? '',
      body: m['body'] as String? ?? '',
      author: m['author'] as String? ?? 'You',
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
  static const _key = 'community_posts';

  Future<List<CommunityPost>> getPosts() async {
    final prefs = await SharedPreferences.getInstance();
    final json = prefs.getString(_key);
    if (json == null || json.isEmpty) return [];
    try {
      final list = jsonDecode(json) as List<dynamic>?;
      return list?.map((e) => CommunityPost.fromJson(Map<String, dynamic>.from(e as Map))).toList() ?? [];
    } catch (_) {
      return [];
    }
  }

  Future<void> _save(List<CommunityPost> posts) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(posts.map((p) => p.toJson()).toList()));
  }

  Future<void> addPost(String title, String body) async {
    final list = await getPosts();
    list.insert(
      0,
      CommunityPost(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        title: title,
        body: body,
        createdAt: DateTime.now(),
      ),
    );
    await _save(list);
  }

  Future<void> addReply(String postId, String body) async {
    final list = await getPosts();
    final i = list.indexWhere((p) => p.id == postId);
    if (i < 0) return;
    final post = list[i];
    final updated = CommunityPost(
      id: post.id,
      title: post.title,
      body: post.body,
      author: post.author,
      createdAt: post.createdAt,
      replies: [...post.replies, CommunityReply(body: body, createdAt: DateTime.now())],
    );
    list[i] = updated;
    await _save(list);
  }
}
