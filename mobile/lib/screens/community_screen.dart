import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
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
  List<CommunityPost> _posts = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    final list = await _service.getPosts();
    if (mounted) setState(() {
      _posts = list;
      _loading = false;
    });
  }

  void _showAddPost(BuildContext context) {
    final titleController = TextEditingController();
    final bodyController = TextEditingController();
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
              const Text('Ask the community', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.purpleDark)),
              const SizedBox(height: 8),
              TextField(
                controller: titleController,
                decoration: const InputDecoration(labelText: 'Title', hintText: 'e.g. Looking for a dupe of this kurta'),
                maxLines: 1,
              ),
              const SizedBox(height: 12),
              TextField(
                controller: bodyController,
                decoration: const InputDecoration(labelText: 'Description', hintText: 'Describe the item or paste image link'),
                maxLines: 3,
              ),
              const SizedBox(height: 20),
              FilledButton(
                onPressed: () async {
                  final title = titleController.text.trim();
                  final body = bodyController.text.trim();
                  if (title.isEmpty) return;
                  await _service.addPost(title, body.isNotEmpty ? body : 'No description.');
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

  void _showPostDetail(CommunityPost post) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _PostDetailSheet(initialPost: post, service: _service),
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
                      colors: [AppColors.bluePrimary.withValues(alpha: 0.12), Colors.white],
                    ),
                    borderRadius: BorderRadius.circular(16),
                    border: Border.all(color: AppColors.borderLightBlue),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Ask the community',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.purpleDark),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        "Post when you can't find a dupe in our catalogue. Others can reply with links to local stores.",
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
                              child: ListTile(
                                contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                                title: Text(post.title, style: const TextStyle(fontWeight: FontWeight.w600, color: AppColors.purpleDark)),
                                subtitle: Padding(
                                  padding: const EdgeInsets.only(top: 6),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(post.body, maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(color: AppColors.greySubtitle)),
                                      const SizedBox(height: 6),
                                      Row(
                                        children: [
                                          Icon(Icons.chat_bubble_outline, size: 14, color: Colors.grey[600]),
                                          const SizedBox(width: 4),
                                          Text('${post.replies.length} reply${post.replies.length == 1 ? '' : 's'}', style: TextStyle(fontSize: 12, color: Colors.grey[600])),
                                        ],
                                      ),
                                    ],
                                  ),
                                ),
                                trailing: const Icon(Icons.chevron_right_rounded),
                                onTap: () => _showPostDetail(post),
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

  const _PostDetailSheet({required this.initialPost, required this.service});

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
                  Text(_post.title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: AppColors.purpleDark)),
                  const SizedBox(height: 6),
                  Text(_post.body, style: TextStyle(color: AppColors.greySubtitle, height: 1.4)),
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
                              Text(r.body, style: const TextStyle(fontSize: 14)),
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
            Padding(
              padding: EdgeInsets.fromLTRB(16, 8, 16, 8 + MediaQuery.of(context).padding.bottom),
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _replyController,
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
