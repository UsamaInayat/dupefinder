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

  const CommunityScreen({super.key, this.embedded = false});

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

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final list = await _service.getPosts();
    final me = await _service.currentUserId();
    final prefs = await SharedPreferences.getInstance();
    final myName = (prefs.getString('user_name') ?? '').trim();
    final email = (prefs.getString('user_email') ?? '').trim();
    final emailPrefix = email.contains('@') ? email.split('@').first.trim() : '';
    if (mounted) setState(() {
      _posts = list;
      _myUserId = me;
      _myName = myName.toLowerCase();
      _myEmailPrefix = emailPrefix.toLowerCase();
      _loading = false;
    });
  }

  bool _isMyPost(CommunityPost post) {
    if (_myUserId != null && _myUserId!.isNotEmpty && post.authorUserId == _myUserId) {
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
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
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
              const Text('Create post', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.purpleDark)),
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
                        setInnerState(() => selectedImageBase64 = base64Encode(bytes));
                      },
                      icon: const Icon(Icons.image_outlined),
                      label: Text(selectedImageBase64 == null ? 'Add image' : 'Image selected'),
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
                    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Post added'), behavior: SnackBarBehavior.floating));
                  }
                },
                child: const Text('Post'),
                style: FilledButton.styleFrom(backgroundColor: AppColors.bluePrimary),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _showPostDetail(CommunityPost post) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _PostDetailSheet(
        initialPost: post,
        service: _service,
        myUserId: _myUserId,
        myNameLower: _myName,
        myEmailPrefixLower: _myEmailPrefix,
      ),
    );
    if (mounted) {
      await _load();
    }
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
                      colors: [AppColors.bluePrimary.withValues(alpha: 0.12), Colors.white],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.borderLightBlue),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Community feed',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.purpleDark),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'Share dupes like a social feed. Add image + description and get replies.',
                        style: TextStyle(color: AppColors.greySubtitle, height: 1.4),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: _posts.isEmpty
                      ? Center(
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
                              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
                              child: InkWell(
                                onTap: () async => _showPostDetail(post),
                                borderRadius: BorderRadius.circular(16),
                                child: Padding(
                                  padding: const EdgeInsets.all(12),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          CircleAvatar(
                                            radius: 16,
                                            backgroundImage: (post.authorPfp != null && post.authorPfp!.isNotEmpty)
                                                ? MemoryImage(base64Decode(post.authorPfp!))
                                                : null,
                                            child: (post.authorPfp == null || post.authorPfp!.isEmpty)
                                                ? const Icon(Icons.person_outline_rounded, size: 16)
                                                : null,
                                          ),
                                          const SizedBox(width: 8),
                                          Expanded(
                                            child: Column(
                                              crossAxisAlignment: CrossAxisAlignment.start,
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
                                                  style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                                ),
                                              ],
                                            ),
                                          ),
                                          Text(
                                            '${post.replies.length} replies',
                                            style: TextStyle(fontSize: 12, color: Colors.grey[700]),
                                          ),
                                          PopupMenuButton<String>(
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
                                                  final c = TextEditingController(text: post.description);
                                                  final updated = await showDialog<String>(
                                                    context: context,
                                                    builder: (ctx) => AlertDialog(
                                                      title: const Text('Edit post'),
                                                      content: TextField(
                                                        controller: c,
                                                        maxLines: 4,
                                                        decoration: const InputDecoration(hintText: 'Update message'),
                                                      ),
                                                      actions: [
                                                        TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                                                        FilledButton(
                                                          onPressed: () => Navigator.pop(ctx, c.text.trim()),
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
                                                const PopupMenuItem(value: 'edit', child: Text('Edit my post')),
                                              if (_isMyPost(post))
                                                const PopupMenuItem(value: 'delete', child: Text('Delete my post')),
                                              if (!_isMyPost(post))
                                                const PopupMenuItem(value: 'report', child: Text('Report post')),
                                            ],
                                          ),
                                        ],
                                      ),
                                      if (post.imageBase64 != null && post.imageBase64!.isNotEmpty) ...[
                                        const SizedBox(height: 10),
                                        ClipRRect(
                                          borderRadius: BorderRadius.circular(12),
                                          child: Container(
                                            width: double.infinity,
                                            color: Colors.black12,
                                            child: Image.memory(
                                              base64Decode(post.imageBase64!),
                                              width: double.infinity,
                                              fit: BoxFit.contain,
                                            ),
                                          ),
                                        ),
                                      ],
                                      if (post.description.isNotEmpty) ...[
                                        const SizedBox(height: 10),
                                        _LinkText(
                                          post.description,
                                          style: TextStyle(
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

  const _PostDetailSheet({
    required this.initialPost,
    required this.service,
    this.myUserId,
    this.myNameLower = '',
    this.myEmailPrefixLower = '',
  });

  @override
  State<_PostDetailSheet> createState() => _PostDetailSheetState();
}

class _PostDetailSheetState extends State<_PostDetailSheet> {
  late CommunityPost _post;
  final _replyController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _post = widget.initialPost;
  }

  @override
  void dispose() {
    _replyController.dispose();
    super.dispose();
  }

  Future<void> _refreshPost() async {
    final list = await widget.service.getPosts();
    CommunityPost? next;
    try {
      next = list.firstWhere((p) => p.id == _post.id);
    } catch (_) {}
    if (next != null && mounted) setState(() => _post = next!);
  }

  Future<void> _sendReply() async {
    final body = _replyController.text.trim();
    if (body.isEmpty) return;
    await widget.service.addReply(_post.id, body);
    _replyController.clear();
    await _refreshPost();
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Reply added'), behavior: SnackBarBehavior.floating));
  }

  @override
  Widget build(BuildContext context) {
    final keyboardInset = MediaQuery.of(context).viewInsets.bottom;
    return DraggableScrollableSheet(
      initialChildSize: 0.6,
      minChildSize: 0.3,
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
                        backgroundImage: (_post.authorPfp != null && _post.authorPfp!.isNotEmpty)
                            ? MemoryImage(base64Decode(_post.authorPfp!))
                            : null,
                        child: (_post.authorPfp == null || _post.authorPfp!.isEmpty)
                            ? const Icon(Icons.person_outline_rounded, size: 15)
                            : null,
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _post.author,
                        style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.purpleDark),
                      ),
                      const Spacer(),
                      PopupMenuButton<String>(
                        onSelected: (v) async {
                          try {
                            if (v == 'delete') {
                              await widget.service.deletePost(_post.id);
                              if (!mounted) return;
                              Navigator.pop(context);
                            }
                            if (v == 'edit') {
                              final c = TextEditingController(text: _post.description);
                              final updated = await showDialog<String>(
                                context: context,
                                builder: (ctx) => AlertDialog(
                                  title: const Text('Edit post'),
                                  content: TextField(
                                    controller: c,
                                    maxLines: 4,
                                    decoration: const InputDecoration(hintText: 'Update message'),
                                  ),
                                  actions: [
                                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                                    FilledButton(onPressed: () => Navigator.pop(ctx, c.text.trim()), child: const Text('Save')),
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
                                    decoration: const InputDecoration(hintText: 'Reason'),
                                  ),
                                  actions: [
                                    TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
                                    FilledButton(onPressed: () => Navigator.pop(ctx, c.text.trim()), child: const Text('Report')),
                                  ],
                                ),
                              );
                              if (reason == null || reason.isEmpty) return;
                              await widget.service.reportPost(_post.id, reason);
                              if (!mounted) return;
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(content: Text('Report sent to admin'), behavior: SnackBarBehavior.floating),
                              );
                            }
                          } catch (e) {
                            if (!mounted) return;
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Action failed: $e'), behavior: SnackBarBehavior.floating),
                            );
                          }
                        },
                        itemBuilder: (_) => [
                          if ((widget.myUserId != null && widget.myUserId == _post.authorUserId) ||
                              (_post.author.trim().toLowerCase() == widget.myNameLower) ||
                              (_post.author.trim().toLowerCase() == widget.myEmailPrefixLower))
                            const PopupMenuItem(value: 'edit', child: Text('Edit my post')),
                          if ((widget.myUserId != null && widget.myUserId == _post.authorUserId) ||
                              (_post.author.trim().toLowerCase() == widget.myNameLower) ||
                              (_post.author.trim().toLowerCase() == widget.myEmailPrefixLower))
                            const PopupMenuItem(value: 'delete', child: Text('Delete my post')),
                          if (!((widget.myUserId != null && widget.myUserId == _post.authorUserId) ||
                              (_post.author.trim().toLowerCase() == widget.myNameLower) ||
                              (_post.author.trim().toLowerCase() == widget.myEmailPrefixLower)))
                            const PopupMenuItem(value: 'report', child: Text('Report post')),
                        ],
                      ),
                    ],
                  ),
                  if (_post.imageBase64 != null && _post.imageBase64!.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Container(
                        width: double.infinity,
                        color: Colors.black12,
                        child: Image.memory(
                          base64Decode(_post.imageBase64!),
                          width: double.infinity,
                          fit: BoxFit.contain,
                        ),
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),
                  _LinkText(
                    _post.description,
                    style: TextStyle(color: AppColors.greySubtitle, height: 1.4),
                  ),
                  const SizedBox(height: 8),
                  Text(DateFormat.yMMMd().add_Hm().format(_post.createdAt), style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                ],
              ),
            ),
            const Divider(height: 1),
            Expanded(
              child: ListView.builder(
                controller: scrollController,
                padding: const EdgeInsets.all(16),
                itemCount: _post.replies.length,
                itemBuilder: (_, i) {
                  final r = _post.replies[i];
                  return Padding(
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Icon(Icons.reply_rounded, size: 18, color: AppColors.bluePrimary),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              _LinkText(
                                r.body,
                                style: const TextStyle(fontSize: 14, color: AppColors.purpleDark),
                              ),
                              Text(DateFormat.yMMMd().format(r.createdAt), style: TextStyle(fontSize: 11, color: Colors.grey[600])),
                            ],
                          ),
                        ),
                      ],
                    ),
                  );
                },
              ),
            ),
            AnimatedPadding(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              padding: EdgeInsets.fromLTRB(
                16,
                8,
                16,
                8 + MediaQuery.of(context).padding.bottom + keyboardInset,
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _replyController,
                      style: const TextStyle(color: AppColors.purpleDark),
                      cursorColor: AppColors.bluePrimary,
                      decoration: const InputDecoration(
                        hintText: 'Reply with a store link or suggestion...',
                        border: OutlineInputBorder(),
                        contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      ),
                      maxLines: 1,
                      onSubmitted: (_) => _sendReply(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filled(
                    onPressed: _sendReply,
                    icon: const Icon(Icons.send_rounded),
                    style: IconButton.styleFrom(backgroundColor: AppColors.bluePrimary),
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
    final normalized = raw.startsWith('http://') || raw.startsWith('https://') ? raw : 'https://$raw';
    final uri = Uri.tryParse(normalized);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.platformDefault);
  }

  @override
  Widget build(BuildContext context) {
    final base = style ?? const TextStyle(fontSize: 14, color: AppColors.greySubtitle);
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
