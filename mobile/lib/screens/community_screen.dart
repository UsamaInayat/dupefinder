import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'dart:async';
import 'dart:convert';
import 'package:flutter/gestures.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/community_service.dart';

/// Decode feed photos near on-screen width (avoids decoding full camera resolution).
int _decodeFeedImagePx(BuildContext context) {
  final w = MediaQuery.sizeOf(context).width;
  final dpr = MediaQuery.devicePixelRatioOf(context);
  return ((w - 48) * dpr).round().clamp(200, 1600);
}

int _decodeDetailImagePx(BuildContext context) {
  final w = MediaQuery.sizeOf(context).width;
  final dpr = MediaQuery.devicePixelRatioOf(context);
  return (w * dpr).round().clamp(240, 1600);
}

int _decodeDetailImageHeightPx(BuildContext context) {
  final dpr = MediaQuery.devicePixelRatioOf(context);
  return (280 * dpr).round().clamp(200, 1200);
}

/// When the server returns a lite post (no [imageBase64]) but we still have bytes in memory, keep them.
CommunityPost mergeCommunityPostKeepImage(CommunityPost prev, CommunityPost next) {
  if (next.hasImage &&
      (next.imageBase64 == null || next.imageBase64!.trim().isEmpty) &&
      prev.imageBase64 != null &&
      prev.imageBase64!.trim().isNotEmpty) {
    return CommunityPost(
      id: next.id,
      description: next.description,
      author: next.author,
      authorUserId: next.authorUserId,
      authorPfp: next.authorPfp,
      imageBase64: prev.imageBase64,
      hasImage: true,
      createdAt: next.createdAt,
      replies: next.replies,
      likeCount: next.likeCount,
      likedByMe: next.likedByMe,
    );
  }
  return next;
}

/// Community: local posts and replies. Ask for dupes, others can reply with store links.
class CommunityScreen extends StatefulWidget {
  final bool embedded;
  /// When embedded in a tab shell, set false for inactive tabs to avoid background polling.
  final bool feedPollActive;
  final String? focusPostId;
  final String? focusReplyId;

  const CommunityScreen({
    super.key,
    this.embedded = false,
    this.feedPollActive = true,
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
  Timer? _feedTimeTicker;
  bool _loadBusy = false;

  @override
  void initState() {
    super.initState();
    _feedTimeTicker = Timer.periodic(const Duration(seconds: 10), (_) {
      if (!mounted) return;
      if (widget.embedded && !widget.feedPollActive) return;
      setState(() {});
      unawaited(_load(forceRefresh: true, showErrorSnack: false));
    });
    _loadCachedThenRefresh();
  }

  @override
  void dispose() {
    _feedTimeTicker?.cancel();
    super.dispose();
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
    if (!oldWidget.feedPollActive &&
        widget.feedPollActive &&
        widget.embedded) {
      unawaited(_load(forceRefresh: true, showErrorSnack: false));
    }
  }

  Future<void> _load({bool forceRefresh = false, bool showErrorSnack = true}) async {
    if (_loadBusy && !forceRefresh) return;
    while (_loadBusy) {
      await Future<void>.delayed(const Duration(milliseconds: 16));
      if (!mounted) return;
    }
    _loadBusy = true;
    try {
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
        if (list.isEmpty &&
            _service.lastPostsFetchError != null &&
            forceRefresh &&
            showErrorSnack) {
          final msg = _service.lastPostsFetchError!;
          WidgetsBinding.instance.addPostFrameCallback((_) {
            if (!context.mounted) return;
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text(
                  'Feed could not refresh ($msg). '
                  'On web, ensure the backend runs at http://localhost:8000.',
                  style: const TextStyle(fontSize: 13),
                ),
                behavior: SnackBarBehavior.floating,
                duration: const Duration(seconds: 5),
              ),
            );
          });
        }
      }
      _openFocusedPostIfNeeded();
    } finally {
      _loadBusy = false;
    }
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

  String _compactCount(int n) {
    if (n >= 1000000) return '${(n / 1000000).toStringAsFixed(1)}M';
    if (n >= 1000) return '${(n / 1000).toStringAsFixed(1)}k';
    return '$n';
  }

  Future<void> _toggleLikeForPost(CommunityPost post) async {
    try {
      final updated = await _service.togglePostLike(post.id);
      if (!mounted) return;
      setState(() {
        final i = _posts.indexWhere((p) => p.id == post.id);
        if (i >= 0) {
          final prev = _posts[i];
          _posts[i] = mergeCommunityPostKeepImage(prev, updated);
        }
      });
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Could not update like: $e'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  Future<void> _sharePost(CommunityPost post) async {
    final text =
        '${post.author}: ${post.description}\n— DupeFinder Community';
    await Clipboard.setData(ClipboardData(text: text));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Post copied — paste anywhere to share'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Widget _buildFeedPostCard(CommunityPost post) {
    final decodePx = _decodeFeedImagePx(context);
    final hasImageBytes =
        post.imageBase64 != null && post.imageBase64!.isNotEmpty;
    final showImagePlaceholder = post.hasImage && !hasImageBytes;
    final liked = post.likedByMe;
    final captionStyle = GoogleFonts.inter(
      fontSize: 14,
      color: DupePalette.textPrimary,
      height: 1.35,
      fontWeight: FontWeight.w400,
    );
    final authorStyle = GoogleFonts.inter(
      fontSize: 14,
      fontWeight: FontWeight.w700,
      color: DupePalette.textPrimary,
      height: 1.35,
    );

    return RepaintBoundary(
      child: Container(
        margin: const EdgeInsets.only(bottom: 18),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(22),
          boxShadow: [
            BoxShadow(
              color: DupePalette.teal.withValues(alpha: 0.12),
              blurRadius: 18,
              offset: const Offset(0, 6),
            ),
            BoxShadow(
              color: DupePalette.pink.withValues(alpha: 0.06),
              blurRadius: 12,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        clipBehavior: Clip.antiAlias,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 14, 6, 0),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  radius: 18,
                  backgroundColor: DupePalette.pink.withValues(alpha: 0.2),
                  backgroundImage: (post.authorPfp != null &&
                          post.authorPfp!.isNotEmpty)
                      ? ResizeImage(
                          MemoryImage(base64Decode(post.authorPfp!)),
                          width: 128,
                          height: 128,
                        )
                      : null,
                  child: (post.authorPfp == null || post.authorPfp!.isEmpty)
                      ? Icon(Icons.person_outline_rounded,
                          size: 18, color: DupePalette.pinkDeep)
                      : null,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        post.author,
                        style: GoogleFonts.inter(
                          fontWeight: FontWeight.w700,
                          fontSize: 15,
                          color: DupePalette.textPrimary,
                        ),
                      ),
                      Text(
                        _timeAgo(post.createdAt),
                        style: GoogleFonts.inter(
                          fontSize: 12,
                          color: DupePalette.greySubtitle,
                        ),
                      ),
                    ],
                  ),
                ),
                PopupMenuButton<String>(
                  icon: Icon(Icons.more_vert_rounded,
                      color: DupePalette.textPrimary, size: 22),
                  padding: EdgeInsets.zero,
                  onSelected: (v) async {
                    try {
                      if (v == 'delete') {
                        await _service.deletePost(post.id);
                        await _load();
                        if (!mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Post deleted'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      }
                      if (v == 'edit') {
                        final c =
                            TextEditingController(text: post.description);
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
                                child: const Text('Save'),
                              ),
                            ],
                          ),
                        );
                        if (updated == null || updated.isEmpty) return;
                        await _service.editPost(post.id, updated);
                        await _load();
                        if (!mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Post updated'),
                            behavior: SnackBarBehavior.floating,
                          ),
                        );
                      }
                      if (v == 'report') {
                        final reason = await _askReportReason();
                        if (reason == null || reason.isEmpty) return;
                        await _service.reportPost(post.id, reason);
                        if (!mounted) return;
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text('Report submitted to admin'),
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
                    if (_isMyPost(post))
                      const PopupMenuItem(
                          value: 'edit', child: Text('Edit my post')),
                    if (_isMyPost(post))
                      const PopupMenuItem(
                          value: 'delete', child: Text('Delete my post')),
                    if (!_isMyPost(post))
                      const PopupMenuItem(
                          value: 'report', child: Text('Report post')),
                  ],
                ),
              ],
            ),
          ),
          if (hasImageBytes) ...[
            const SizedBox(height: 12),
            GestureDetector(
              onTap: () => _showPostDetail(post),
              child: AspectRatio(
                aspectRatio: 1,
                child: Image.memory(
                  base64Decode(post.imageBase64!),
                  fit: BoxFit.cover,
                  gaplessPlayback: true,
                  cacheWidth: decodePx,
                  cacheHeight: decodePx,
                  filterQuality: FilterQuality.medium,
                ),
              ),
            ),
          ] else if (showImagePlaceholder) ...[
            const SizedBox(height: 12),
            GestureDetector(
              onTap: () => _showPostDetail(post),
              child: AspectRatio(
                aspectRatio: 1,
                child: DecoratedBox(
                  decoration: BoxDecoration(
                    color: DupePalette.teal.withValues(alpha: 0.08),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.photo_outlined,
                        size: 40,
                        color: DupePalette.teal.withValues(alpha: 0.55),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Photo — tap to load',
                        style: GoogleFonts.inter(
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                          color: DupePalette.greySubtitle,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ],
          GestureDetector(
            onTap: () => _showPostDetail(post),
            behavior: HitTestBehavior.opaque,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(14, 0, 14, 10),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(post.author, style: authorStyle),
                  Text(' ', style: authorStyle),
                  Expanded(
                    child: post.description.isEmpty
                        ? Text(
                            'No description.',
                            style: captionStyle.copyWith(
                              color: DupePalette.greySubtitle,
                            ),
                          )
                        : _LinkText(post.description, style: captionStyle),
                  ),
                ],
              ),
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(10, 0, 10, 12),
            child: Row(
              children: [
                InkWell(
                  onTap: () => _toggleLikeForPost(post),
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    child: Row(
                      children: [
                        Icon(
                          liked
                              ? Icons.favorite_rounded
                              : Icons.favorite_border_rounded,
                          color: DupePalette.pinkDeep,
                          size: 26,
                        ),
                        const SizedBox(width: 6),
                        Text(
                          _compactCount(post.likeCount),
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: DupePalette.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                InkWell(
                  onTap: () => _showPostDetail(post),
                  borderRadius: BorderRadius.circular(8),
                  child: Padding(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 6, vertical: 4),
                    child: Row(
                      children: [
                        Icon(Icons.chat_bubble_outline_rounded,
                            color: DupePalette.textPrimary, size: 24),
                        const SizedBox(width: 6),
                        Text(
                          _compactCount(post.replies.length),
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            fontWeight: FontWeight.w500,
                            color: DupePalette.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const Spacer(),
                IconButton(
                  onPressed: () => _sharePost(post),
                  icon: Icon(Icons.share_outlined,
                      color: DupePalette.textPrimary, size: 24),
                  padding: EdgeInsets.zero,
                  constraints:
                      const BoxConstraints(minWidth: 40, minHeight: 40),
                ),
              ],
            ),
          ),
        ],
      ),
    ),
    );
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
    final rootMessenger = ScaffoldMessenger.of(context);
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
                final previewDecode = (MediaQuery.sizeOf(ctx).width *
                        MediaQuery.devicePixelRatioOf(ctx))
                    .round()
                    .clamp(200, 720);
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    OutlinedButton.icon(
                      onPressed: () async {
                        final x = await _picker.pickImage(
                          source: ImageSource.gallery,
                          maxWidth: 1600,
                          maxHeight: 1600,
                          imageQuality: 82,
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
                          cacheWidth: previewDecode,
                          cacheHeight: (120 * MediaQuery.devicePixelRatioOf(ctx))
                              .round()
                              .clamp(120, 900),
                          filterQuality: FilterQuality.medium,
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
                  final body =
                      desc.isNotEmpty ? desc : 'No description.';
                  final imageB64 = selectedImageBase64;
                  Navigator.pop(ctx);
                  if (!mounted) return;
                  try {
                    final created = await _service.addPost(
                      body,
                      imageBase64: imageB64,
                    );
                    if (!mounted) return;
                    setState(() {
                      _posts = [
                        created,
                        ..._posts.where((p) => p.id != created.id),
                      ];
                    });
                    rootMessenger.showSnackBar(
                      const SnackBar(
                        content: Text('Post added'),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
                  } catch (e) {
                    if (!mounted) return;
                    rootMessenger.showSnackBar(
                      SnackBar(
                        content: Text(
                          'Post failed: ${e.toString().replaceFirst('Exception: ', '')}',
                        ),
                        behavior: SnackBarBehavior.floating,
                      ),
                    );
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
      useRootNavigator: true,
      useSafeArea: true,
      backgroundColor: Colors.transparent,
      barrierColor: Colors.black.withValues(alpha: 0.32),
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
              final prev = _posts[idx];
              _posts[idx] = mergeCommunityPostKeepImage(prev, updatedPost);
            }
          });
        },
        onPostDeleted: () {
          if (!mounted) return;
          setState(() => _posts.removeWhere((p) => p.id == post.id));
        },
      ),
    );
    if (mounted) {
      // Refresh in background so returning from detail feels instant.
      unawaited(_load(forceRefresh: true));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DupePalette.scaffoldLight,
      appBar: widget.embedded
          ? null
          : AppBar(
              title: const Text('Community'),
              backgroundColor: Colors.white,
              foregroundColor: DupePalette.textPrimary,
              surfaceTintColor: Colors.transparent,
            ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: DupePalette.pink))
          : Container(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFFEEF9F6),
                    DupePalette.blueSoft.withValues(alpha: 0.12),
                    DupePalette.teal.withValues(alpha: 0.08),
                  ],
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (widget.embedded) ...[
                    Padding(
                      padding: const EdgeInsets.fromLTRB(20, 12, 20, 4),
                      child: Text(
                        'Community',
                        style: GoogleFonts.playfairDisplay(
                          fontSize: 26,
                          fontWeight: FontWeight.w700,
                          color: DupePalette.textPrimary,
                          height: 1.1,
                        ),
                      ),
                    ),
                  ],
                  Expanded(
                    child: _posts.isEmpty
                        ? Center(
                            child: Text(
                              'No posts yet. Tap New post to ask for a dupe.',
                              textAlign: TextAlign.center,
                              style: GoogleFonts.inter(
                                color: DupePalette.greySubtitle,
                                fontSize: 15,
                              ),
                            ),
                          )
                        : ListView.builder(
                            padding: EdgeInsets.fromLTRB(
                              16,
                              widget.embedded ? 4 : 12,
                              16,
                              100,
                            ),
                            itemCount: _posts.length,
                            itemBuilder: (_, i) =>
                                _buildFeedPostCard(_posts[i]),
                          ),
                  ),
                ],
              ),
            ),
      floatingActionButton: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [DupePalette.pink, DupePalette.blue],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(28),
          boxShadow: [
            BoxShadow(
              color: DupePalette.pink.withValues(alpha: 0.38),
              blurRadius: 14,
              offset: const Offset(0, 5),
            ),
          ],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: () => _showAddPost(context),
            borderRadius: BorderRadius.circular(28),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(Icons.add_rounded, color: Colors.white, size: 22),
                  const SizedBox(width: 8),
                  Text(
                    'New post',
                    style: GoogleFonts.inter(
                      color: Colors.white,
                      fontWeight: FontWeight.w700,
                      fontSize: 15,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
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
  bool _hydratingImage = false;
  String? _pendingReplyTempId;
  String? _highlightReplyId;
  String? _replyingToName;
  String? _replyingToReplyId;
  final Set<String> _expandedThreadParents = <String>{};
  static const int _maxVisibleDepth = 2;
  Timer? _detailTimeTicker;

  @override
  void initState() {
    super.initState();
    _post = widget.initialPost;
    if (_post.hasImage &&
        (_post.imageBase64 == null || _post.imageBase64!.trim().isEmpty)) {
      _hydratingImage = true;
      unawaited(_loadFullPostForImage());
    }
    _highlightReplyId = widget.initialHighlightReplyId;
    _detailTimeTicker = Timer.periodic(const Duration(seconds: 30), (_) {
      if (mounted) setState(() {});
    });
    if (_highlightReplyId != null && _highlightReplyId!.isNotEmpty) {
      Future.delayed(const Duration(seconds: 4), () {
        if (!mounted) return;
        setState(() => _highlightReplyId = null);
      });
    }
  }

  @override
  void dispose() {
    _detailTimeTicker?.cancel();
    _replyController.dispose();
    super.dispose();
  }

  Future<void> _loadFullPostForImage() async {
    try {
      final full = await widget.service.fetchPostById(_post.id);
      if (!mounted) return;
      setState(() {
        _post = full;
        _hydratingImage = false;
      });
      widget.onPostChanged(full);
    } catch (_) {
      if (mounted) setState(() => _hydratingImage = false);
    }
  }

  CommunityPost _mergeFeedWithHydratedImage(CommunityPost next) {
    if (next.hasImage &&
        (next.imageBase64 == null || next.imageBase64!.trim().isEmpty) &&
        _post.imageBase64 != null &&
        _post.imageBase64!.trim().isNotEmpty) {
      return CommunityPost(
        id: next.id,
        description: next.description,
        author: next.author,
        authorUserId: next.authorUserId,
        authorPfp: next.authorPfp,
        imageBase64: _post.imageBase64,
        hasImage: true,
        createdAt: next.createdAt,
        replies: next.replies,
        likeCount: next.likeCount,
        likedByMe: next.likedByMe,
      );
    }
    return next;
  }

  Future<void> _refreshPost() async {
    final list = await widget.service.getPosts(forceRefresh: true);
    CommunityPost? next;
    try {
      next = list.firstWhere((p) => p.id == _post.id);
    } catch (_) {}
    if (next != null && mounted) {
      final merged = _mergeFeedWithHydratedImage(next);
      setState(() => _post = merged);
      widget.onPostChanged(merged);
    }
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
        hasImage: _post.hasImage,
        createdAt: _post.createdAt,
        replies: [..._post.replies, optimistic],
        likeCount: _post.likeCount,
        likedByMe: _post.likedByMe,
      );
    });
    try {
      final updated = await widget.service.addReply(
        _post.id,
        pendingBody,
        parentReplyId: pendingParentReplyId,
      );
      _replyController.clear();
      final merged = _mergeFeedWithHydratedImage(updated);
      setState(() {
        _replyingToName = null;
        _replyingToReplyId = null;
        _pendingReplyTempId = null;
        _post = merged;
      });
      widget.onPostChanged(merged);
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
            hasImage: _post.hasImage,
            createdAt: _post.createdAt,
            replies:
                _post.replies.where((r) => r.id != _pendingReplyTempId).toList(),
            likeCount: _post.likeCount,
            likedByMe: _post.likedByMe,
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
    // Lift the whole sheet above the keyboard; insets are not always applied
    // correctly to children of DraggableScrollableSheet alone.
    final keyboardBottom = MediaQuery.of(context).viewInsets.bottom;
    final detailDecodeW = _decodeDetailImagePx(context);
    final detailDecodeH = _decodeDetailImageHeightPx(context);
    return Padding(
      padding: EdgeInsets.only(bottom: keyboardBottom),
      child: DraggableScrollableSheet(
      initialChildSize: 0.58,
      minChildSize: 0.38,
      maxChildSize: 0.86,
      expand: false,
      builder: (_, scrollController) => Container(
        decoration: BoxDecoration(
          color: DupePalette.cardSurface,
          borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.12),
              blurRadius: 20,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      CircleAvatar(
                        radius: 15,
                        backgroundColor: DupePalette.pink.withValues(alpha: 0.18),
                        backgroundImage: (_post.authorPfp != null &&
                                _post.authorPfp!.isNotEmpty)
                            ? ResizeImage(
                                MemoryImage(base64Decode(_post.authorPfp!)),
                                width: 120,
                                height: 120,
                              )
                            : null,
                        child: (_post.authorPfp == null ||
                                _post.authorPfp!.isEmpty)
                            ? Icon(Icons.person_outline_rounded,
                                size: 15, color: DupePalette.pinkDeep)
                            : null,
                      ),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              _post.author,
                              style: const TextStyle(
                                  fontWeight: FontWeight.w600,
                                  color: AppColors.purpleDark),
                            ),
                            Text(
                              _timeAgo(_post.createdAt),
                              style: TextStyle(
                                fontSize: 12,
                                color: DupePalette.greySubtitle,
                              ),
                            ),
                          ],
                        ),
                      ),
                      PopupMenuButton<String>(
                        icon: Icon(Icons.more_vert_rounded,
                            color: DupePalette.textPrimary),
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
                  if (_hydratingImage) ...[
                    const SizedBox(height: 10),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 24),
                      child: Center(
                        child: CircularProgressIndicator(
                          color: DupePalette.pink,
                        ),
                      ),
                    ),
                  ] else if (_post.imageBase64 != null &&
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
                            cacheWidth: detailDecodeW,
                            cacheHeight: detailDecodeH,
                            filterQuality: FilterQuality.medium,
                          ),
                        ),
                      ),
                    ),
                  ] else if (_post.hasImage) ...[
                    const SizedBox(height: 10),
                    Text(
                      'Photo could not be loaded.',
                      style: GoogleFonts.inter(
                        fontSize: 13,
                        color: DupePalette.greySubtitle,
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  _LinkText(
                    _post.description,
                    style: TextStyle(
                        fontSize: 14,
                        color: DupePalette.textPrimary,
                        height: 1.4),
                  ),
                ],
              ),
            ),
            Divider(
                height: 1,
                thickness: 1,
                color: DupePalette.pink.withValues(alpha: 0.22)),
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
                            ? DupePalette.pink.withValues(alpha: 0.14)
                            : Colors.transparent,
                        borderRadius: BorderRadius.circular(8),
                        border: isHighlighted
                            ? Border.all(
                                color:
                                    DupePalette.teal.withValues(alpha: 0.45),
                                width: 1,
                              )
                            : null,
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              CircleAvatar(
                                radius: 12,
                                backgroundColor:
                                    DupePalette.teal.withValues(alpha: 0.15),
                                backgroundImage: (r.authorPfp != null &&
                                        r.authorPfp!.isNotEmpty)
                                    ? ResizeImage(
                                        MemoryImage(
                                            base64Decode(r.authorPfp!)),
                                        width: 96,
                                        height: 96,
                                      )
                                    : null,
                                child: (r.authorPfp == null ||
                                        r.authorPfp!.isEmpty)
                                    ? Icon(Icons.person_outline_rounded,
                                        size: 13, color: DupePalette.tealWall)
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
                                      _timeAgo(r.createdAt),
                                      style: TextStyle(
                                          fontSize: 11,
                                          color: DupePalette.greySubtitle),
                                    ),
                                  ],
                                ),
                              ),
                              PopupMenuButton<String>(
                                icon: Icon(Icons.more_vert_rounded,
                                    size: 20, color: DupePalette.textPrimary),
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
                                    ? Border(
                                        left: BorderSide(
                                          color: DupePalette.teal
                                              .withValues(alpha: 0.55),
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
                                        gradient: LinearGradient(
                                          colors: [
                                            DupePalette.pink
                                                .withValues(alpha: 0.14),
                                            DupePalette.teal
                                                .withValues(alpha: 0.1),
                                          ],
                                        ),
                                        borderRadius:
                                            BorderRadius.circular(999),
                                        border: Border.all(
                                          color: DupePalette.pink
                                              .withValues(alpha: 0.35),
                                          width: 1,
                                        ),
                                      ),
                                      child: Text(
                                        'Replying to @${parentReply.author}',
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600,
                                          color: DupePalette.pinkDeep,
                                        ),
                                      ),
                                    ),
                                  _LinkText(
                                    r.body,
                                    style: const TextStyle(
                                        fontSize: 14,
                                        color: AppColors.purpleDark,
                                        height: 1.35),
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
                                style: TextButton.styleFrom(
                                  foregroundColor: DupePalette.pinkDeep,
                                ),
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
                                style: TextButton.styleFrom(
                                  foregroundColor: DupePalette.tealWall,
                                ),
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
                12 + MediaQuery.of(context).viewPadding.bottom,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _replyController,
                      enabled: !_sendingReply,
                      scrollPadding: const EdgeInsets.fromLTRB(16, 80, 16, 120),
                      style: const TextStyle(
                        color: AppColors.purpleDark,
                        fontSize: 15,
                        fontWeight: FontWeight.w500,
                      ),
                      cursorColor: DupePalette.pinkDeep,
                      decoration: InputDecoration(
                        filled: true,
                        fillColor: DupePalette.scaffoldLight,
                        hintText: _replyingToName != null &&
                                _replyingToName!.isNotEmpty
                            ? 'Replying to $_replyingToName...'
                            : 'Reply with a store link or suggestion...',
                        hintStyle: TextStyle(
                          color: DupePalette.greyGuest,
                          fontSize: 14,
                        ),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(
                            color:
                                DupePalette.pink.withValues(alpha: 0.35),
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(
                            color:
                                DupePalette.teal.withValues(alpha: 0.4),
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(14),
                          borderSide: BorderSide(
                              color: DupePalette.pinkDeep, width: 2),
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                            horizontal: 12, vertical: 10),
                      ),
                      maxLines: 1,
                      onSubmitted: (_) => _sendingReply ? null : _sendReply(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: _sendingReply ? null : _sendReply,
                      customBorder: const CircleBorder(),
                      child: Ink(
                        height: 48,
                        width: 48,
                        decoration: BoxDecoration(
                          gradient: _sendingReply
                              ? null
                              : DupePalette.ctaGradient,
                          color: _sendingReply
                              ? DupePalette.greyGuest
                              : null,
                          shape: BoxShape.circle,
                          boxShadow: _sendingReply
                              ? null
                              : [
                                  BoxShadow(
                                    color: DupePalette.pink
                                        .withValues(alpha: 0.35),
                                    blurRadius: 10,
                                    offset: const Offset(0, 3),
                                  ),
                                ],
                        ),
                        child: Center(
                          child: _sendingReply
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                )
                              : const Icon(Icons.send_rounded,
                                  color: Colors.white, size: 22),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
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
  static final RegExp _hashtagRegex = RegExp(r'(#[^\s#]+)');

  Future<void> _open(String raw) async {
    final normalized = raw.startsWith('http://') || raw.startsWith('https://')
        ? raw
        : 'https://$raw';
    final uri = Uri.tryParse(normalized);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.platformDefault);
  }

  void _addPlainWithHashtags(
    String segment,
    TextStyle base,
    TextStyle hashtagStyle,
    List<InlineSpan> spans,
  ) {
    if (segment.isEmpty) return;
    var hStart = 0;
    for (final m in _hashtagRegex.allMatches(segment)) {
      if (m.start > hStart) {
        spans.add(TextSpan(text: segment.substring(hStart, m.start), style: base));
      }
      spans.add(TextSpan(text: m.group(0)!, style: hashtagStyle));
      hStart = m.end;
    }
    if (hStart < segment.length) {
      spans.add(TextSpan(text: segment.substring(hStart), style: base));
    }
  }

  @override
  Widget build(BuildContext context) {
    final base =
        style ?? TextStyle(fontSize: 14, color: DupePalette.textPrimary, height: 1.4);
    final linkStyle = base.copyWith(
      color: DupePalette.teal,
      decoration: TextDecoration.underline,
      fontWeight: FontWeight.w600,
    );
    final hashtagStyle = base.copyWith(
      color: DupePalette.pinkDeep,
      fontWeight: FontWeight.w700,
      decoration: TextDecoration.none,
    );
    final spans = <InlineSpan>[];
    var start = 0;
    for (final m in _urlRegex.allMatches(text)) {
      if (m.start > start) {
        _addPlainWithHashtags(text.substring(start, m.start), base, hashtagStyle, spans);
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
      _addPlainWithHashtags(text.substring(start), base, hashtagStyle, spans);
    }

    return SelectableText.rich(
      TextSpan(children: spans),
      textAlign: TextAlign.left,
    );
  }
}

String _timeAgo(DateTime dtUtc) {
  final diff = DateTime.now().toUtc().difference(dtUtc);
  if (diff.inSeconds < 45) return 'Just now';
  if (diff.inMinutes < 60) return '${diff.inMinutes}m ago';
  if (diff.inHours < 24) return '${diff.inHours}h ago';
  return '${diff.inDays}d ago';
}
