import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:flutter/gestures.dart';
import 'package:intl/intl.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/community_service.dart';

/// Community: local posts and replies. Ask for dupes, others can reply with store links.
class CommunityScreen extends StatefulWidget {
  final bool embedded;
  final String? focusPostId;
  final String? focusReplyId;

  const CommunityScreen({
    super.key,
    this.embedded = false,
    this.focusPostId,
    this.focusReplyId,
  });

  @override
  State<CommunityScreen> createState() => _CommunityScreenState();
}

class _CommunityScreenState extends State<CommunityScreen> {
  final _service = CommunityService();
  final _picker = ImagePicker();
  List<CommunityPost> _posts = [];
  bool _loading = true;
  String? _myUserId;
  String _myName = '';
  String _myEmailPrefix = '';
  bool _openedFocusedPost = false;

  @override
  void initState() {
    super.initState();
    _loadCachedThenRefresh();
  }

  Future<void> _loadCachedThenRefresh() async {
    final cached = await _service.getCachedPostsFast();
    if (cached.isNotEmpty && mounted) {
      final me = await _service.currentUserId();
      final prefs = await SharedPreferences.getInstance();
      final myName = (prefs.getString('user_name') ?? '').trim();
      final email = (prefs.getString('user_email') ?? '').trim();
      final emailPrefix =
          email.contains('@') ? email.split('@').first.trim() : '';
      setState(() {
        _posts = cached;
        _myUserId = me;
        _myName = myName.toLowerCase();
        _myEmailPrefix = emailPrefix.toLowerCase();
        _loading = false;
      });
    }
    await _load(forceRefresh: true);
  }

  @override
  void didUpdateWidget(covariant CommunityScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    final postChanged = oldWidget.focusPostId != widget.focusPostId;
    final replyChanged = oldWidget.focusReplyId != widget.focusReplyId;
    if (postChanged || replyChanged) {
      _openedFocusedPost = false;
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (!mounted) return;
        _openFocusedPostIfNeeded();
      });
    }
  }

  Future<void> _load({bool forceRefresh = false}) async {
    if (_posts.isEmpty) {
      setState(() => _loading = true);
    }
    final list = await _service.getPosts(forceRefresh: forceRefresh);
    final me = await _service.currentUserId();
    final prefs = await SharedPreferences.getInstance();
    final myName = (prefs.getString('user_name') ?? '').trim();
    final email = (prefs.getString('user_email') ?? '').trim();
    final emailPrefix =
        email.contains('@') ? email.split('@').first.trim() : '';
    if (mounted) {
      setState(() {
        _posts = list;
        _myUserId = me;
        _myName = myName.toLowerCase();
        _myEmailPrefix = emailPrefix.toLowerCase();
        _loading = false;
      });
    }
    _openFocusedPostIfNeeded();
  }

  Future<void> _openFocusedPostIfNeeded() async {
    if (_openedFocusedPost) return;
    if (_loading) return;
    final postId = (widget.focusPostId ?? '').trim();
    if (postId.isEmpty) return;
    CommunityPost? target;
    try {
      target = _posts.firstWhere((p) => p.id == postId);
    } catch (_) {}
    if (target == null) return;
    _openedFocusedPost = true;
    await _showPostDetail(target, highlightReplyId: widget.focusReplyId);
  }

  bool _isMyPost(CommunityPost post) {
    if (_myUserId != null &&
        _myUserId!.isNotEmpty &&
        post.authorUserId == _myUserId) {
      return true;
    }
    final author = post.author.trim().toLowerCase();
    if (_myName.isNotEmpty && author == _myName) return true;
    if (_myEmailPrefix.isNotEmpty && author == _myEmailPrefix) return true;
    return false;
  }

  Future<String?> _askReportReason() async {
    final c = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Report post'),
        content: TextField(
          controller: c,
          maxLines: 3,
          decoration: const InputDecoration(
            hintText: 'Reason (e.g. abuse/spam/inappropriate)',
          ),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, c.text.trim()),
            child: const Text('Report'),
          ),
        ],
      ),
    );
  }

  void _showAddPost(BuildContext context) {
    final descController = TextEditingController();
    String? selectedImageBase64;
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(ctx).viewInsets.bottom),
        child: Container(
          padding: const EdgeInsets.all(24),
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('Create post',
                  style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppColors.purpleDark)),
              const SizedBox(height: 8),
              StatefulBuilder(builder: (ctx, setInnerState) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    OutlinedButton.icon(
                      onPressed: () async {
                        final x = await _picker.pickImage(
                          source: ImageSource.gallery,
                          imageQuality: 80,
                        );
                        if (x == null) return;
                        final bytes = await x.readAsBytes();
                        setInnerState(
                            () => selectedImageBase64 = base64Encode(bytes));
                      },
                      icon: const Icon(Icons.image_outlined),
                      label: Text(selectedImageBase64 == null
                          ? 'Add image'
                          : 'Image selected'),
                    ),
                    if (selectedImageBase64 != null) ...[
                      const SizedBox(height: 10),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(10),
                        child: Image.memory(
                          base64Decode(selectedImageBase64!),
                          height: 120,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ],
                    const SizedBox(height: 12),
                    TextField(
                      controller: descController,
                      decoration: const InputDecoration(
                        labelText: 'Description',
                        hintText: 'Write caption/description...',
                      ),
                      maxLines: 3,
                    ),
                  ],
                );
              }),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () async {
                  final desc = descController.text.trim();
                  if (desc.isEmpty && selectedImageBase64 == null) return;
                  await _service.addPost(
                    desc.isNotEmpty ? desc : 'No description.',
                    imageBase64: selectedImageBase64,
                  );
                  if (mounted) {
                    Navigator.pop(ctx);
                    await _load();
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(
                        content: Text('Post added'),
                        behavior: SnackBarBehavior.floating));
                  }
                },
                style: FilledButton.styleFrom(
                    backgroundColor: AppColors.bluePrimary),
                child: const Text('Post'),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showPostDetail(CommunityPost post,
      {String? highlightReplyId}) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _PostDetailSheet(
        initialPost: post,
        service: _service,
        myUserId: _myUserId,
        myNameLower: _myName,
        myEmailPrefixLower: _myEmailPrefix,
        initialHighlightReplyId: highlightReplyId,
        onPostChanged: (updatedPost) {
          if (!mounted) return;
          setState(() {
            final idx = _posts.indexWhere((p) => p.id == updatedPost.id);
            if (idx >= 0) {
              _posts[idx] = updatedPost;
            }
          });
        },
        onPostDeleted: () {
          if (!mounted) return;
          setState(() => _posts.removeWhere((p) => p.id == post.id));
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: widget.embedded
          ? null
          : AppBar(
              title: const Text('Community'),
              backgroundColor: AppColors.cardSurface,
              foregroundColor: AppColors.purpleDark,
            ),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Container(
                  margin: const EdgeInsets.all(16),
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    gradient: LinearGradient(
                      colors: [
                        AppColors.bluePrimary.withValues(alpha: 0.12),
                        Colors.white
                      ],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.borderLightBlue),
                  ),
                  child: const Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Community feed',
                        style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: AppColors.purpleDark),
                      ),
                      SizedBox(height: 8),
                      Text(
                        'Share dupes like a social feed. Add image + description and get replies.',
                        style: TextStyle(
                            color: AppColors.greySubtitle, height: 1.4),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: _posts.isEmpty
                      ? const Center(
                          child: Text(
                            'No posts yet. Tap + to ask for a dupe.',
                            style: TextStyle(color: AppColors.greySubtitle),
                          ),
                        )
                      : ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                          itemCount: _posts.length,
                          itemBuilder: (_, i) {
                            final post = _posts[i];
                            return Card(
                              margin: const EdgeInsets.only(bottom: 12),
                              shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(16)),
                              child: InkWell(
                                onTap: () async => _showPostDetail(post),
                                borderRadius: BorderRadius.circular(16),
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          CircleAvatar(
                                            radius: 16,
                                            backgroundImage: (post.authorPfp !=
                                                        null &&
                                                    post.authorPfp!.isNotEmpty)
                                                ? MemoryImage(base64Decode(
                                                    post.authorPfp!))
                                                : null,
                                            child: (post.authorPfp == null ||
                                                    post.authorPfp!.isEmpty)
                                                ? const Icon(
                                                    Icons
                                                        .person_outline_rounded,
                                                    size: 16)
                                                : null,
                                          ),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment:
                                                  CrossAxisAlignment.start,
                                              children: [
                                                Text(
                                                  post.author,
                                                  style: const TextStyle(
                                                    fontWeight: FontWeight.w600,
                                                    color: AppColors.purpleDark,
                                                  ),
                                                ),
                                                Text(
                                                  _timeAgo(post.createdAt),
                                                  style: TextStyle(
                                                      fontSize: 12,
                                                      color: Colors.grey[600]),
                                                ),
                                              ],
                                            ),
                                          ),
                                          Text(
                                            '${post.replies.length} replies',
                                            style: TextStyle(
                                                fontSize: 12,
                                                color: Colors.grey[700]),
                                          ),
                                          PopupMenuButton<String>(
                                            onSelected: (v) async {
                                              try {
                                                if (v == 'delete') {
                                                  await _service
                                                      .deletePost(post.id);
                                                  await _load();
                                                  if (!mounted) return;
                                                  ScaffoldMessenger.of(context)
                                                      .showSnackBar(
                                                    const SnackBar(
                                                      content:
                                                          Text('Post deleted'),
                                                      behavior: SnackBarBehavior
                                                          .floating,
                                                    ),
                                                  );
                                                }
                                                if (v == 'edit') {
                                                  final c =
                                                      TextEditingController(
                                                          text:
                                                              post.description);
                                                  final updated =
                                                      await showDialog<String>(
                                                    context: context,
                                                    builder: (ctx) =>
                                                        AlertDialog(
                                                      title: const Text(
                                                          'Edit post'),
                                                      content: TextField(
                                                        controller: c,
                                                        maxLines: 4,
                                                        decoration:
                                                            const InputDecoration(
                                                                hintText:
                                                                    'Update message'),
                                                      ),
                                                      actions: [
                                                        TextButton(
                                                            onPressed: () =>
                                                                Navigator.pop(
                                                                    ctx),
                                                            child: const Text(
                                                                'Cancel')),
                                                        FilledButton(
                                                          onPressed: () =>
                                                              Navigator.pop(
                                                                  ctx,
                                                                  c.text
                                                                      .trim()),
                                                          child: const Text(
                                                              'Save'),
                                                        ),
                                                      ],
                                                    ),
                                                  );
                                                  if (updated == null ||
                                                      updated.isEmpty) {
                                                    return;
                                                  }
                                                  await _service.editPost(
                                                      post.id, updated);
                                                  await _load();
                                                  if (!mounted) return;
                                                  ScaffoldMessenger.of(context)
                                                      .showSnackBar(
                                                    const SnackBar(
                                                      content:
                                                          Text('Post updated'),
                                                      behavior: SnackBarBehavior
                                                          .floating,
                                                    ),
                                                  );
                                                }
                                                if (v == 'report') {
                                                  final reason =
                                                      await _askReportReason();
                                                  if (reason == null ||
                                                      reason.isEmpty) {
                                                    return;
                                                  }
                                                  await _service.reportPost(
                                                      post.id, reason);
                                                  if (!mounted) return;
                                                  ScaffoldMessenger.of(context)
                                                      .showSnackBar(
                                                    const SnackBar(
                                                      content: Text(
                                                          'Report submitted to admin'),
                                                      behavior: SnackBarBehavior
                                                          .floating,
                                                    ),
                                                  );
                                                }
                                              } catch (e) {
                                                if (!mounted) return;
                                                ScaffoldMessenger.of(context)
                                                    .showSnackBar(
                                                  SnackBar(
                                                    content: Text(
                                                        'Action failed: $e'),
                                                    behavior: SnackBarBehavior
                                                        .floating,
                                                  ),
                                                );
                                              }
                                            },
                                            itemBuilder: (_) => [
                                              if (_isMyPost(post))
                                                const PopupMenuItem(
                                                    value: 'edit',
                                                    child:
                                                        Text('Edit my post')),
                                              if (_isMyPost(post))
                                                const PopupMenuItem(
                                                    value: 'delete',
                                                    child:
                                                        Text('Delete my post')),
                                              if (!_isMyPost(post))
                                                const PopupMenuItem(
                                                    value: 'report',
                                                    child: Text('Report post')),
                                            ],
                                          ),
                                        ],
                                      ),
                                      if (post.imageBase64 != null &&
                                          post.imageBase64!.isNotEmpty) ...[
                                        const SizedBox(height: 10),
                                        ClipRRect(
                                          borderRadius:
                                              BorderRadius.circular(12),
                                          child: ConstrainedBox(
                                            constraints: const BoxConstraints(
                                                maxHeight: 260),
                                            child: Center(
                                              child: Image.memory(
                                                base64Decode(post.imageBase64!),
                                                fit: BoxFit.contain,
                                              ),
                                            ),
                                          ),
                                        ),
                                      ],
                                      if (post.description.isNotEmpty) ...[
                                        const SizedBox(height: 10),
                                        _LinkText(
                                          post.description,
                                          style: const TextStyle(
                                            color: AppColors.greySubtitle,
                                            height: 1.4,
                                          ),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              ),
                            );
                          },
                        ),
                ),
              ],
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddPost(context),
        icon: const Icon(Icons.add_rounded),
        label: const Text('New post'),
        backgroundColor: AppColors.bluePrimary,
      ),
    );
  }
}

class _PostDetailSheet extends StatefulWidget {
  final CommunityPost initialPost;
  final CommunityService service;
  final String? myUserId;
  final String myNameLower;
  final String myEmailPrefixLower;
  final String? initialHighlightReplyId;
  final ValueChanged<CommunityPost> onPostChanged;
  final VoidCallback onPostDeleted;

  const _PostDetailSheet({
    required this.initialPost,
    required this.service,
    this.myUserId,
    this.myNameLower = '',
    this.myEmailPrefixLower = '',
    this.initialHighlightReplyId,
    required this.onPostChanged,
    required this.onPostDeleted,
  });

  @override
  State<_PostDetailSheet> createState() => _PostDetailSheetState();
}

class _PostDetailSheetState extends State<_PostDetailSheet> {
  late CommunityPost _post;
  final _replyController = TextEditingController();
  bool _sendingReply = false;
  String? _pendingReplyTempId;
  String? _highlightReplyId;
  String? _replyingToName;
  String? _replyingToReplyId;
  final Set<String> _expandedThreadParents = <String>{};
  static const int _maxVisibleDepth = 2;

  @override
  void initState() {
    super.initState();
    _post = widget.initialPost;
    _highlightReplyId = widget.initialHighlightReplyId;
    if (_highlightReplyId != null && _highlightReplyId!.isNotEmpty) {
      Future.delayed(const Duration(seconds: 4), () {
        if (!mounted) return;
        setState(() => _highlightReplyId = null);
      });
    }
  }

  @override
  void dispose() {
    _replyController.dispose();
    super.dispose();
  }

  Future<void> _refreshPost() async {
    final list = await widget.service.getPosts(forceRefresh: true);
    CommunityPost? next;
    try {
      next = list.firstWhere((p) => p.id == _post.id);
    } catch (_) {}
    if (next != null && mounted) setState(() => _post = next!);
    if (next != null) widget.onPostChanged(next);
  }

  Future<void> _sendReply() async {
    if (_sendingReply) return;
    final body = _replyController.text.trim();
    if (body.isEmpty) return;
    final pendingBody = body;
    final pendingParentReplyId = _replyingToReplyId;
    final tempId = 'temp_${DateTime.now().microsecondsSinceEpoch}';
    setState(() => _sendingReply = true);
    final optimistic = CommunityReply(
      id: tempId,
      body: pendingBody,
      author: widget.myNameLower.isNotEmpty ? widget.myNameLower : 'You',
      authorUserId: widget.myUserId,
      parentReplyId: pendingParentReplyId,
      createdAt: DateTime.now(),
    );
    setState(() {
      _pendingReplyTempId = tempId;
      _post = CommunityPost(
        id: _post.id,
        description: _post.description,
        author: _post.author,
        authorUserId: _post.authorUserId,
        authorPfp: _post.authorPfp,
        imageBase64: _post.imageBase64,
        createdAt: _post.createdAt,
        replies: [..._post.replies, optimistic],
      );
    });
    try {
      final updated = await widget.service.addReply(
        _post.id,
        pendingBody,
        parentReplyId: pendingParentReplyId,
      );
      _replyController.clear();
      setState(() {
        _replyingToName = null;
        _replyingToReplyId = null;
        _pendingReplyTempId = null;
        _post = updated;
      });
      widget.onPostChanged(updated);
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
              content: Text('Reply added'),
              behavior: SnackBarBehavior.floating),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _post = CommunityPost(
            id: _post.id,
            description: _post.description,
            author: _post.author,
            authorUserId: _post.authorUserId,
            authorPfp: _post.authorPfp,
            imageBase64: _post.imageBase64,
            createdAt: _post.createdAt,
            replies:
                _post.replies.where((r) => r.id != _pendingReplyTempId).toList(),
          );
          _pendingReplyTempId = null;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Reply failed: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _sendingReply = false);
    }
  }

  bool _isMyReply(CommunityReply r) {
    if (widget.myUserId != null &&
        widget.myUserId!.isNotEmpty &&
        r.authorUserId == widget.myUserId) {
      return true;
    }
    final author = r.author.trim().toLowerCase();
    if (widget.myNameLower.isNotEmpty && author == widget.myNameLower) {
      return true;
    }
    if (widget.myEmailPrefixLower.isNotEmpty &&
        author == widget.myEmailPrefixLower) {
      return true;
    }
    return false;
  }

  Future<String?> _askReason({
    String title = 'Report reply',
    String hint = 'Reason (abuse/spam/inappropriate)',
  }) async {
    final c = TextEditingController();
    return showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: c,
          maxLines: 3,
          decoration: InputDecoration(hintText: hint),
        ),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
          FilledButton(
              onPressed: () => Navigator.pop(ctx, c.text.trim()),
              child: const Text('Submit')),
        ],
      ),
    );
  }

  List<Map<String, dynamic>> _threadedReplies() {
    final replies = List<CommunityReply>.from(_post.replies);
    final byParent = <String, List<CommunityReply>>{};
    final ids = replies.map((e) => e.id).where((e) => e.isNotEmpty).toSet();
    final roots = <CommunityReply>[];
    for (final r in replies) {
      final p = (r.parentReplyId ?? '').trim();
      if (p.isEmpty || !ids.contains(p)) {
        roots.add(r);
      } else {
        byParent.putIfAbsent(p, () => []).add(r);
      }
    }
    int byTime(CommunityReply a, CommunityReply b) =>
        a.createdAt.compareTo(b.createdAt);
    roots.sort(byTime);
    for (final list in byParent.values) {
      list.sort(byTime);
    }
    final out = <Map<String, dynamic>>[];
    void addNode(CommunityReply r, int depth, {required bool forceShow}) {
      final children = byParent[r.id] ?? const <CommunityReply>[];
      final expanded = r.id.isNotEmpty && _expandedThreadParents.contains(r.id);
      final visible = forceShow || depth <= _maxVisibleDepth;
      out.add({
        'reply': r,
        'depth': depth,
        'visible': visible,
        'expanded': expanded,
        'hasHiddenChildren': children.isNotEmpty &&
            depth >= _maxVisibleDepth &&
            !expanded &&
            !forceShow,
        'hiddenChildrenCount': children.length,
      });
      final nextForceShow =
          forceShow || (depth >= _maxVisibleDepth && expanded);
      for (final child in children) {
        addNode(child, depth + 1, forceShow: nextForceShow);
      }
    }

    for (final root in roots) {
      addNode(root, 0, forceShow: false);
    }
    return out;
  }

  @override
  Widget build(BuildContext context) {
    return DraggableScrollableSheet(
      initialChildSize: 0.82,
      minChildSize: 0.45,
      maxChildSize: 0.95,
      expand: false,
      builder: (_, scrollController) => Container(
        decoration: const BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 15,
                        backgroundImage: (_post.authorPfp != null &&
                                _post.authorPfp!.isNotEmpty)
                            ? MemoryImage(base64Decode(_post.authorPfp!))
                            : null,
                        child: (_post.authorPfp == null ||
                                _post.authorPfp!.isEmpty)
                            ? const Icon(Icons.person_outline_rounded, size: 15)
                            : null,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _post.author,
                        style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            color: AppColors.purpleDark),
                      ),
                      const Spacer(),
                      PopupMenuButton<String>(
                        onSelected: (v) async {
                          try {
                            if (v == 'delete') {
                              await widget.service.deletePost(_post.id);
                              widget.onPostDeleted();
                              if (!mounted) return;
                              Navigator.pop(context, true);
                            }
                            if (v == 'edit') {
                              final c = TextEditingController(
                                  text: _post.description);
                              final updated = await showDialog<String>(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('Edit post'),
                                  content: TextField(
                                    controller: c,
                                    maxLines: 4,
                                    decoration: const InputDecoration(
                                        hintText: 'Update message'),
                                  ),
                                  actions: [
                                    TextButton(
                                        onPressed: () => Navigator.pop(ctx),
                                        child: const Text('Cancel')),
                                    FilledButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, c.text.trim()),
                                        child: const Text('Save')),
                                  ],
                                ),
                              );
                              if (updated == null || updated.isEmpty) return;
                              await widget.service.editPost(_post.id, updated);
                              await _refreshPost();
                            }
                            if (v == 'report') {
                              final c = TextEditingController();
                              final reason = await showDialog<String>(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('Report post'),
                                  content: TextField(
                                    controller: c,
                                    maxLines: 3,
                                    decoration: const InputDecoration(
                                        hintText: 'Reason'),
                                  ),
                                  actions: [
                                    TextButton(
                                        onPressed: () => Navigator.pop(ctx),
                                        child: const Text('Cancel')),
                                    FilledButton(
                                        onPressed: () =>
                                            Navigator.pop(ctx, c.text.trim()),
                                        child: const Text('Report')),
                                  ],
                                ),
                              );
                              if (reason == null || reason.isEmpty) return;
                              await widget.service.reportPost(_post.id, reason);
                              if (!mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                    content: Text('Report sent to admin'),
                                    behavior: SnackBarBehavior.floating),
                              );
                            }
                          } catch (e) {
                            if (!mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(
                                  content: Text('Action failed: $e'),
                                  behavior: SnackBarBehavior.floating),
                            );
                          }
                        },
                        itemBuilder: (_) => [
                          if ((widget.myUserId != null &&
                                  widget.myUserId == _post.authorUserId) ||
                              (_post.author.trim().toLowerCase() ==
                                  widget.myNameLower) ||
                              (_post.author.trim().toLowerCase() ==
                                  widget.myEmailPrefixLower))
                            const PopupMenuItem(
                                value: 'edit', child: Text('Edit my post')),
                          if ((widget.myUserId != null &&
                                  widget.myUserId == _post.authorUserId) ||
                              (_post.author.trim().toLowerCase() ==
                                  widget.myNameLower) ||
                              (_post.author.trim().toLowerCase() ==
                                  widget.myEmailPrefixLower))
                            const PopupMenuItem(
                                value: 'delete', child: Text('Delete my post')),
                          if (!((widget.myUserId != null &&
                                  widget.myUserId == _post.authorUserId) ||
                              (_post.author.trim().toLowerCase() ==
                                  widget.myNameLower) ||
                              (_post.author.trim().toLowerCase() ==
                                  widget.myEmailPrefixLower)))
                            const PopupMenuItem(
                                value: 'report', child: Text('Report post')),
                        ],
                      ),
                    ],
                  ),
                  if (_post.imageBase64 != null &&
                      _post.imageBase64!.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxHeight: 280),
                        child: Center(
                          child: Image.memory(
                            base64Decode(_post.imageBase64!),
                            fit: BoxFit.contain,
                          ),
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  _LinkText(
                    _post.description,
                    style:
                        const TextStyle(color: AppColors.greySubtitle, height: 1.4),
                  ),
                  const SizedBox(height: 8),
                  Text(DateFormat.yMMMd().add_Hm().format(_post.createdAt),
                      style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: Builder(builder: (context) {
                final threaded = _threadedReplies();
                final visibleNodes =
                    threaded.where((x) => x['visible'] == true).toList();
                final replyById = <String, CommunityReply>{
                  for (final r in _post.replies)
                    if (r.id.isNotEmpty) r.id: r
                };
                return ListView.builder(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  itemCount: visibleNodes.length,
                  itemBuilder: (_, i) {
                    final node = visibleNodes[i];
                    final r = node['reply'] as CommunityReply;
                    final depth = (node['depth'] as int?) ?? 0;
                    final indent =
                        depth <= 0 ? 0.0 : 22.0 * (depth > 4 ? 4 : depth);
                    final parentReplyId = (r.parentReplyId ?? '').trim();
                    final parentReply =
                        parentReplyId.isEmpty ? null : replyById[parentReplyId];
                    final hasHiddenChildren = node['hasHiddenChildren'] == true;
                    final hiddenChildrenCount =
                        (node['hiddenChildrenCount'] as int?) ?? 0;
                    final isHighlighted =
                        _highlightReplyId != null && _highlightReplyId == r.id;
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 250),
                      margin: const EdgeInsets.only(bottom: 12),
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: isHighlighted
                            ? AppColors.bluePrimary.withValues(alpha: 0.16)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              CircleAvatar(
                                radius: 12,
                                backgroundImage: (r.authorPfp != null &&
                                        r.authorPfp!.isNotEmpty)
                                    ? MemoryImage(base64Decode(r.authorPfp!))
                                    : null,
                                child: (r.authorPfp == null ||
                                        r.authorPfp!.isEmpty)
                                    ? const Icon(Icons.person_outline_rounded,
                                        size: 13)
                                    : null,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      r.author,
                                      style: const TextStyle(
                                        fontSize: 12,
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.purpleDark,
                                      ),
                                    ),
                                    Text(
                                      DateFormat.yMMMd().format(r.createdAt),
                                      style: TextStyle(
                                          fontSize: 11,
                                          color: Colors.grey[600]),
                                    ),
                                  ],
                                ),
                              ),
                              PopupMenuButton<String>(
                                onSelected: (v) async {
                                  try {
                                    if (v == 'reply_back') {
                                      final mention = '@${r.author} ';
                                      final current =
                                          _replyController.text.trim();
                                      final next = current.isEmpty
                                          ? mention
                                          : '$mention$current';
                                      setState(() {
                                        _replyingToName = r.author;
                                        _replyingToReplyId =
                                            r.id.isNotEmpty ? r.id : null;
                                      });
                                      _replyController
                                        ..text = next
                                        ..selection = TextSelection.collapsed(
                                            offset: next.length);
                                      return;
                                    }
                                    if (v == 'delete_reply') {
                                      await widget.service
                                          .deleteReply(_post.id, r.id);
                                      await _refreshPost();
                                      if (!mounted) return;
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(
                                        const SnackBar(
                                          content: Text('Reply deleted'),
                                          behavior: SnackBarBehavior.floating,
                                        ),
                                      );
                                      return;
                                    }
                                    if (v == 'report_reply') {
                                      if (r.id.isEmpty) return;
                                      final reason = await _askReason();
                                      if (reason == null || reason.isEmpty) {
                                        return;
                                      }
                                      await widget.service.reportReply(
                                        postId: _post.id,
                                        replyId: r.id,
                                        reason: reason,
                                      );
                                      if (!mounted) return;
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(
                                        const SnackBar(
                                          content: Text('Reply reported'),
                                          behavior: SnackBarBehavior.floating,
                                        ),
                                      );
                                      return;
                                    }
                                    if (v == 'block_user') {
                                      final targetId =
                                          (r.authorUserId ?? '').trim();
                                      if (targetId.isEmpty) {
                                        if (!mounted) return;
                                        ScaffoldMessenger.of(context)
                                            .showSnackBar(
                                          const SnackBar(
                                            content: Text(
                                                'Cannot block this legacy user'),
                                            behavior: SnackBarBehavior.floating,
                                          ),
                                        );
                                        return;
                                      }
                                      await widget.service.blockUser(targetId);
                                      await _refreshPost();
                                      if (!mounted) return;
                                      ScaffoldMessenger.of(context)
                                          .showSnackBar(
                                        SnackBar(
                                          content: Text('${r.author} blocked'),
                                          behavior: SnackBarBehavior.floating,
                                        ),
                                      );
                                    }
                                  } catch (e) {
                                    if (!mounted) return;
                                    ScaffoldMessenger.of(context).showSnackBar(
                                      SnackBar(
                                        content: Text('Action failed: $e'),
                                        behavior: SnackBarBehavior.floating,
                                      ),
                                    );
                                  }
                                },
                                itemBuilder: (_) => [
                                  const PopupMenuItem(
                                    value: 'reply_back',
                                    child: Text('Reply back'),
                                  ),
                                  if (_isMyReply(r) && r.id.isNotEmpty)
                                    const PopupMenuItem(
                                      value: 'delete_reply',
                                      child: Text('Delete my reply'),
                                    ),
                                  if (!_isMyReply(r) && r.id.isNotEmpty)
                                    const PopupMenuItem(
                                      value: 'report_reply',
                                      child: Text('Report reply'),
                                    ),
                                  if (!_isMyReply(r))
                                    const PopupMenuItem(
                                      value: 'block_user',
                                      child: Text('Block user'),
                                    ),
                                ],
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          Padding(
                            padding: EdgeInsets.only(left: 26 + indent),
                            child: Container(
                              decoration: BoxDecoration(
                                border: depth > 0
                                    ? const Border(
                                        left: BorderSide(
                                          color: AppColors.borderLightBlue,
                                          width: 1.2,
                                        ),
                                      )
                                    : null,
                              ),
                              padding: EdgeInsets.only(
                                left: depth > 0 ? 8 : 0,
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  if (parentReply != null)
                                    Container(
                                      margin: const EdgeInsets.only(bottom: 4),
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 8, vertical: 3),
                                      decoration: BoxDecoration(
                                        color: AppColors.bluePrimary
                                            .withValues(alpha: 0.12),
                                        borderRadius:
                                            BorderRadius.circular(999),
                                      ),
                                      child: Text(
                                        'Replying to @${parentReply.author}',
                                        style: const TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                          color: AppColors.purpleDark,
                                        ),
                                      ),
                                    ),
                                  _LinkText(
                                    r.body,
                                    style: const TextStyle(
                                        fontSize: 14,
                                        color: AppColors.purpleDark),
                                  ),
                                ],
                              ),
                            ),
                          ),
                          if (hasHiddenChildren)
                            Padding(
                              padding: EdgeInsets.only(
                                  left: 26 + indent + 6, top: 4),
                              child: TextButton(
                                onPressed: () {
                                  if (!mounted || r.id.isEmpty) return;
                                  setState(
                                      () => _expandedThreadParents.add(r.id));
                                },
                                child: Text(
                                  hiddenChildrenCount > 0
                                      ? 'View more replies ($hiddenChildrenCount)'
                                      : 'View more replies',
                                ),
                              ),
                            ),
                          if (depth >= _maxVisibleDepth &&
                              r.id.isNotEmpty &&
                              _expandedThreadParents.contains(r.id))
                            Padding(
                              padding: EdgeInsets.only(left: 26 + indent + 6),
                              child: TextButton(
                                onPressed: () {
                                  if (!mounted) return;
                                  setState(() =>
                                      _expandedThreadParents.remove(r.id));
                                },
                                child: const Text('Hide nested replies'),
                              ),
                            ),
                        ],
                      ),
                    );
                  },
                );
              }),
            ),
            AnimatedPadding(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              padding: EdgeInsets.fromLTRB(
                16,
                8,
                16,
                8 +
                    MediaQuery.of(context).padding.bottom +
                    MediaQuery.of(context).viewInsets.bottom,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _replyController,
                      enabled: !_sendingReply,
                      style: const TextStyle(
                        color: AppColors.purpleDark,
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                      ),
                      cursorColor: AppColors.bluePrimary,
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: Colors.white,
                        hintText: _replyingToName != null &&
                                _replyingToName!.isNotEmpty
                            ? 'Replying to $_replyingToName...'
                            : 'Reply with a store link or suggestion...',
                        hintStyle: TextStyle(
                          color: Colors.grey[600],
                          fontSize: 14,
                        ),
                        border: const OutlineInputBorder(),
                        enabledBorder: OutlineInputBorder(
                          borderSide: BorderSide(color: Colors.grey[350]!),
                        ),
                        focusedBorder: const OutlineInputBorder(
                          borderSide: BorderSide(
                              color: AppColors.bluePrimary, width: 1.5),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                      ),
                      maxLines: 1,
                      onSubmitted: (_) => _sendingReply ? null : _sendReply(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _sendingReply ? null : _sendReply,
                    icon: _sendingReply
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.send_rounded),
                    style: IconButton.styleFrom(
                        backgroundColor: AppColors.bluePrimary),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _LinkText extends StatelessWidget {
  final String text;
  final TextStyle? style;

  const _LinkText(this.text, {this.style});

  static final RegExp _urlRegex = RegExp(
    r'((https?:\/\/|www\.)[^\s]+)',
    caseSensitive: false,
  );

  Future<void> _open(String raw) async {
    final normalized = raw.startsWith('http://') || raw.startsWith('https://')
        ? raw
        : 'https://$raw';
    final uri = Uri.tryParse(normalized);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.platformDefault);
  }

  @override
  Widget build(BuildContext context) {
    final base =
        style ?? const TextStyle(fontSize: 14, color: AppColors.greySubtitle);
    final linkStyle = base.copyWith(
      color: AppColors.bluePrimary,
      decoration: TextDecoration.underline,
      fontWeight: FontWeight.w600,
    );
    final spans = <InlineSpan>[];
    int start = 0;
    for (final m in _urlRegex.allMatches(text)) {
      if (m.start > start) {
        spans.add(TextSpan(text: text.substring(start, m.start), style: base));
      }
      final link = m.group(0)!;
      spans.add(
        TextSpan(
          text: link,
          style: linkStyle,
          recognizer: TapGestureRecognizer()..onTap = () => _open(link),
        ),
      );
      start = m.end;
    }
    if (start < text.length) {
      spans.add(TextSpan(text: text.substring(start), style: base));
    }

    return SelectableText.rich(
      TextSpan(children: spans),
      textAlign: TextAlign.left,
    );
  }
}

String _timeAgo(DateTime dt) {
  final diff = DateTime.now().difference(dt);
  if (diff.inMinutes < 1) return 'Just now';
  if (diff.inHours < 1) return '${diff.inMinutes}m ago';
  if (diff.inDays < 1) return '${diff.inHours}h ago';
  return '${diff.inDays}d ago';
}
