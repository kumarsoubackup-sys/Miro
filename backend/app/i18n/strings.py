"""
Internationalised user-facing strings for MiroFish backend services.

Supports: English (en), Chinese (zh), Malay (ms).
The active language is read from Config.OUTPUT_LANGUAGE at call time.
"""

from ..config import Config

# ---------------------------------------------------------------------------
# Master translation table
# Keys are grouped by originating service for readability.
# Each key maps to {'en': ..., 'zh': ..., 'ms': ...}.
# Placeholders use {name} syntax compatible with str.format(**kwargs).
# ---------------------------------------------------------------------------

STRINGS: dict[str, dict[str, str]] = {

    # ===================================================================
    # graph_builder.py  --  progress / status messages
    # ===================================================================

    'building_graph': {
        'en': 'Building graph...',
        'zh': '开始构建图谱...',
        'ms': 'Membina graf...',
    },
    'graph_created': {
        'en': 'Graph created: {graph_id}',
        'zh': '图谱已创建: {graph_id}',
        'ms': 'Graf telah dicipta: {graph_id}',
    },
    'ontology_set': {
        'en': 'Ontology configured',
        'zh': '本体已设置',
        'ms': 'Ontologi telah ditetapkan',
    },
    'text_split_into_chunks': {
        'en': 'Text split into {total_chunks} chunks',
        'zh': '文本已分割为 {total_chunks} 个块',
        'ms': 'Teks telah dibahagikan kepada {total_chunks} bahagian',
    },
    'sending_batch': {
        'en': 'Sending batch {batch_num}/{total_batches} ({chunk_count} chunks)...',
        'zh': '发送第 {batch_num}/{total_batches} 批数据 ({chunk_count} 块)...',
        'ms': 'Menghantar kelompok {batch_num}/{total_batches} ({chunk_count} bahagian)...',
    },
    'batch_failed': {
        'en': 'Batch {batch_num} failed: {error}',
        'zh': '批次 {batch_num} 发送失败: {error}',
        'ms': 'Kelompok {batch_num} gagal dihantar: {error}',
    },
    'waiting_zep_processing': {
        'en': 'Waiting for Zep to process data...',
        'zh': '等待Zep处理数据...',
        'ms': 'Menunggu Zep memproses data...',
    },
    'no_episodes_to_wait': {
        'en': 'No episodes to wait for',
        'zh': '无需等待（没有 episode）',
        'ms': 'Tiada episod untuk ditunggu',
    },
    'waiting_episodes_processing': {
        'en': 'Waiting for {total_episodes} text chunks to be processed...',
        'zh': '开始等待 {total_episodes} 个文本块处理...',
        'ms': 'Menunggu {total_episodes} bahagian teks diproses...',
    },
    'episodes_processing_timeout': {
        'en': 'Some text chunks timed out, completed {completed_count}/{total_episodes}',
        'zh': '部分文本块超时，已完成 {completed_count}/{total_episodes}',
        'ms': 'Sebahagian bahagian teks tamat masa, selesai {completed_count}/{total_episodes}',
    },
    'zep_processing_progress': {
        'en': 'Zep processing... {completed_count}/{total_episodes} done, {pending_count} pending ({elapsed}s)',
        'zh': 'Zep处理中... {completed_count}/{total_episodes} 完成, {pending_count} 待处理 ({elapsed}秒)',
        'ms': 'Zep sedang memproses... {completed_count}/{total_episodes} selesai, {pending_count} belum selesai ({elapsed}s)',
    },
    'processing_complete': {
        'en': 'Processing complete: {completed_count}/{total_episodes}',
        'zh': '处理完成: {completed_count}/{total_episodes}',
        'ms': 'Pemprosesan selesai: {completed_count}/{total_episodes}',
    },
    'fetching_graph_info': {
        'en': 'Fetching graph information...',
        'zh': '获取图谱信息...',
        'ms': 'Mendapatkan maklumat graf...',
    },

    # ===================================================================
    # simulation_runner.py  --  error / status messages
    # ===================================================================

    'simulation_already_running': {
        'en': 'Simulation is already running: {simulation_id}',
        'zh': '模拟已在运行中: {simulation_id}',
        'ms': 'Simulasi sudah sedang berjalan: {simulation_id}',
    },
    'simulation_config_missing': {
        'en': 'Simulation config does not exist. Please call /prepare first.',
        'zh': '模拟配置不存在，请先调用 /prepare 接口',
        'ms': 'Konfigurasi simulasi tidak wujud. Sila panggil /prepare terlebih dahulu.',
    },
    'simulation_not_found': {
        'en': 'Simulation not found: {simulation_id}',
        'zh': '模拟不存在: {simulation_id}',
        'ms': 'Simulasi tidak ditemui: {simulation_id}',
    },
    'simulation_not_running': {
        'en': 'Simulation is not running: {simulation_id}, status={status}',
        'zh': '模拟未在运行: {simulation_id}, status={status}',
        'ms': 'Simulasi tidak sedang berjalan: {simulation_id}, status={status}',
    },
    'graph_id_required': {
        'en': 'graph_id is required when enabling graph memory update',
        'zh': '启用图谱记忆更新时必须提供 graph_id',
        'ms': 'graph_id diperlukan apabila kemas kini memori graf diaktifkan',
    },
    'script_not_found': {
        'en': 'Script not found: {script_path}',
        'zh': '脚本不存在: {script_path}',
        'ms': 'Skrip tidak ditemui: {script_path}',
    },
    'simulation_env_not_running': {
        'en': 'Simulation environment is not running or has been closed, cannot perform interview: {simulation_id}',
        'zh': '模拟环境未运行或已关闭，无法执行Interview: {simulation_id}',
        'ms': 'Persekitaran simulasi tidak berjalan atau telah ditutup, tidak dapat menjalankan temu bual: {simulation_id}',
    },
    'simulation_dir_not_exists': {
        'en': 'Simulation directory does not exist, no cleanup needed',
        'zh': '模拟目录不存在，无需清理',
        'ms': 'Direktori simulasi tidak wujud, tiada pembersihan diperlukan',
    },
    'server_shutdown_terminated': {
        'en': 'Server shutdown, simulation terminated',
        'zh': '服务器关闭，模拟被终止',
        'ms': 'Pelayan ditutup, simulasi ditamatkan',
    },
    'simulation_no_agents': {
        'en': 'No agents in simulation config: {simulation_id}',
        'zh': '模拟配置中没有Agent: {simulation_id}',
        'ms': 'Tiada ejen dalam konfigurasi simulasi: {simulation_id}',
    },
    'env_already_closed': {
        'en': 'Environment is already closed',
        'zh': '环境已经关闭',
        'ms': 'Persekitaran sudah ditutup',
    },
    'env_close_command_sent': {
        'en': 'Environment close command sent',
        'zh': '环境关闭命令已发送',
        'ms': 'Arahan penutupan persekitaran telah dihantar',
    },
    'env_close_timeout': {
        'en': 'Environment close command sent (response timed out, environment may be shutting down)',
        'zh': '环境关闭命令已发送（等待响应超时，环境可能正在关闭）',
        'ms': 'Arahan penutupan persekitaran telah dihantar (masa menunggu respons tamat, persekitaran mungkin sedang ditutup)',
    },

    # ===================================================================
    # simulation_config_generator.py  --  progress messages
    # ===================================================================

    'generating_time_config': {
        'en': 'Generating time configuration...',
        'zh': '生成时间配置...',
        'ms': 'Menjana konfigurasi masa...',
    },
    'generating_event_config': {
        'en': 'Generating event configuration and trending topics...',
        'zh': '生成事件配置和热点话题...',
        'ms': 'Menjana konfigurasi acara dan topik hangat...',
    },
    'generating_agent_config': {
        'en': 'Generating agent configuration ({start}-{end}/{total})...',
        'zh': '生成Agent配置 ({start}-{end}/{total})...',
        'ms': 'Menjana konfigurasi ejen ({start}-{end}/{total})...',
    },
    'generating_platform_config': {
        'en': 'Generating platform configuration...',
        'zh': '生成平台配置...',
        'ms': 'Menjana konfigurasi platform...',
    },

    # ===================================================================
    # zep_graph_memory_updater.py  --  agent action descriptions
    # ===================================================================

    # -- CREATE_POST --
    'posted_content': {
        'en': 'posted: "{content}"',
        'zh': '发布了一条帖子：「{content}」',
        'ms': 'menyiarkan: "{content}"',
    },
    'posted': {
        'en': 'made a post',
        'zh': '发布了一条帖子',
        'ms': 'membuat siaran',
    },

    # -- LIKE_POST --
    'liked_post_by_with_content': {
        'en': 'liked a post by {post_author}: "{post_content}"',
        'zh': '点赞了{post_author}的帖子：「{post_content}」',
        'ms': 'menyukai siaran oleh {post_author}: "{post_content}"',
    },
    'liked_post_with_content': {
        'en': 'liked a post: "{post_content}"',
        'zh': '点赞了一条帖子：「{post_content}」',
        'ms': 'menyukai siaran: "{post_content}"',
    },
    'liked_post_by': {
        'en': 'liked a post by {post_author}',
        'zh': '点赞了{post_author}的一条帖子',
        'ms': 'menyukai siaran oleh {post_author}',
    },
    'liked_post': {
        'en': 'liked a post',
        'zh': '点赞了一条帖子',
        'ms': 'menyukai satu siaran',
    },

    # -- DISLIKE_POST --
    'disliked_post_by_with_content': {
        'en': 'disliked a post by {post_author}: "{post_content}"',
        'zh': '踩了{post_author}的帖子：「{post_content}」',
        'ms': 'tidak menyukai siaran oleh {post_author}: "{post_content}"',
    },
    'disliked_post_with_content': {
        'en': 'disliked a post: "{post_content}"',
        'zh': '踩了一条帖子：「{post_content}」',
        'ms': 'tidak menyukai siaran: "{post_content}"',
    },
    'disliked_post_by': {
        'en': 'disliked a post by {post_author}',
        'zh': '踩了{post_author}的一条帖子',
        'ms': 'tidak menyukai siaran oleh {post_author}',
    },
    'disliked_post': {
        'en': 'disliked a post',
        'zh': '踩了一条帖子',
        'ms': 'tidak menyukai satu siaran',
    },

    # -- REPOST --
    'reposted_by_with_content': {
        'en': 'reposted from {original_author}: "{original_content}"',
        'zh': '转发了{original_author}的帖子：「{original_content}」',
        'ms': 'menyiarkan semula daripada {original_author}: "{original_content}"',
    },
    'reposted_with_content': {
        'en': 'reposted: "{original_content}"',
        'zh': '转发了一条帖子：「{original_content}」',
        'ms': 'menyiarkan semula: "{original_content}"',
    },
    'reposted_by': {
        'en': 'reposted from {original_author}',
        'zh': '转发了{original_author}的一条帖子',
        'ms': 'menyiarkan semula daripada {original_author}',
    },
    'reposted': {
        'en': 'reposted a post',
        'zh': '转发了一条帖子',
        'ms': 'menyiarkan semula satu siaran',
    },

    # -- QUOTE_POST --
    'quoted_by_with_content': {
        'en': 'quoted a post by {original_author}: "{original_content}"',
        'zh': '引用了{original_author}的帖子「{original_content}」',
        'ms': 'memetik siaran oleh {original_author}: "{original_content}"',
    },
    'quoted_with_content': {
        'en': 'quoted a post: "{original_content}"',
        'zh': '引用了一条帖子「{original_content}」',
        'ms': 'memetik siaran: "{original_content}"',
    },
    'quoted_by': {
        'en': 'quoted a post by {original_author}',
        'zh': '引用了{original_author}的一条帖子',
        'ms': 'memetik siaran oleh {original_author}',
    },
    'quoted': {
        'en': 'quoted a post',
        'zh': '引用了一条帖子',
        'ms': 'memetik satu siaran',
    },
    'quoted_and_commented': {
        'en': ', and commented: "{quote_content}"',
        'zh': '，并评论道：「{quote_content}」',
        'ms': ', dan mengulas: "{quote_content}"',
    },

    # -- FOLLOW --
    'followed_user': {
        'en': 'followed user "{target_user_name}"',
        'zh': '关注了用户「{target_user_name}」',
        'ms': 'mengikuti pengguna "{target_user_name}"',
    },
    'followed_a_user': {
        'en': 'followed a user',
        'zh': '关注了一个用户',
        'ms': 'mengikuti seorang pengguna',
    },

    # -- CREATE_COMMENT --
    'commented_on_post_by_with_content': {
        'en': 'commented on a post by {post_author} ("{post_content}"): "{content}"',
        'zh': '在{post_author}的帖子「{post_content}」下评论道：「{content}」',
        'ms': 'mengulas siaran oleh {post_author} ("{post_content}"): "{content}"',
    },
    'commented_on_post_with_content': {
        'en': 'commented on a post ("{post_content}"): "{content}"',
        'zh': '在帖子「{post_content}」下评论道：「{content}」',
        'ms': 'mengulas siaran ("{post_content}"): "{content}"',
    },
    'commented_on_post_by': {
        'en': 'commented on a post by {post_author}: "{content}"',
        'zh': '在{post_author}的帖子下评论道：「{content}」',
        'ms': 'mengulas siaran oleh {post_author}: "{content}"',
    },
    'commented': {
        'en': 'commented: "{content}"',
        'zh': '评论道：「{content}」',
        'ms': 'mengulas: "{content}"',
    },
    'made_comment': {
        'en': 'made a comment',
        'zh': '发表了评论',
        'ms': 'membuat ulasan',
    },

    # -- LIKE_COMMENT --
    'liked_comment_by_with_content': {
        'en': 'liked a comment by {comment_author}: "{comment_content}"',
        'zh': '点赞了{comment_author}的评论：「{comment_content}」',
        'ms': 'menyukai ulasan oleh {comment_author}: "{comment_content}"',
    },
    'liked_comment_with_content': {
        'en': 'liked a comment: "{comment_content}"',
        'zh': '点赞了一条评论：「{comment_content}」',
        'ms': 'menyukai ulasan: "{comment_content}"',
    },
    'liked_comment_by': {
        'en': 'liked a comment by {comment_author}',
        'zh': '点赞了{comment_author}的一条评论',
        'ms': 'menyukai ulasan oleh {comment_author}',
    },
    'liked_comment': {
        'en': 'liked a comment',
        'zh': '点赞了一条评论',
        'ms': 'menyukai satu ulasan',
    },

    # -- DISLIKE_COMMENT --
    'disliked_comment_by_with_content': {
        'en': 'disliked a comment by {comment_author}: "{comment_content}"',
        'zh': '踩了{comment_author}的评论：「{comment_content}」',
        'ms': 'tidak menyukai ulasan oleh {comment_author}: "{comment_content}"',
    },
    'disliked_comment_with_content': {
        'en': 'disliked a comment: "{comment_content}"',
        'zh': '踩了一条评论：「{comment_content}」',
        'ms': 'tidak menyukai ulasan: "{comment_content}"',
    },
    'disliked_comment_by': {
        'en': 'disliked a comment by {comment_author}',
        'zh': '踩了{comment_author}的一条评论',
        'ms': 'tidak menyukai ulasan oleh {comment_author}',
    },
    'disliked_comment': {
        'en': 'disliked a comment',
        'zh': '踩了一条评论',
        'ms': 'tidak menyukai satu ulasan',
    },

    # -- SEARCH_POSTS --
    'searched_query': {
        'en': 'searched for "{query}"',
        'zh': '搜索了「{query}」',
        'ms': 'mencari "{query}"',
    },
    'searched': {
        'en': 'performed a search',
        'zh': '进行了搜索',
        'ms': 'melakukan carian',
    },

    # -- SEARCH_USER --
    'searched_user_query': {
        'en': 'searched for user "{query}"',
        'zh': '搜索了用户「{query}」',
        'ms': 'mencari pengguna "{query}"',
    },
    'searched_user': {
        'en': 'searched for a user',
        'zh': '搜索了用户',
        'ms': 'mencari pengguna',
    },

    # -- MUTE --
    'muted_user': {
        'en': 'muted user "{target_user_name}"',
        'zh': '屏蔽了用户「{target_user_name}」',
        'ms': 'membisukan pengguna "{target_user_name}"',
    },
    'muted_a_user': {
        'en': 'muted a user',
        'zh': '屏蔽了一个用户',
        'ms': 'membisukan seorang pengguna',
    },

    # -- Generic / unknown action --
    'performed_action': {
        'en': 'performed {action_type}',
        'zh': '执行了{action_type}操作',
        'ms': 'melaksanakan {action_type}',
    },

    # -- Platform display names --
    'platform_world1': {
        'en': 'World 1',
        'zh': '世界1',
        'ms': 'Dunia 1',
    },
    'platform_world2': {
        'en': 'World 2',
        'zh': '世界2',
        'ms': 'Dunia 2',
    },

    # ===================================================================
    # zep_tools.py  --  to_text() display strings
    # ===================================================================

    # -- SearchResult --
    'search_query_label': {
        'en': 'Search query: {query}',
        'zh': '搜索查询: {query}',
        'ms': 'Pertanyaan carian: {query}',
    },
    'found_count': {
        'en': 'Found {total_count} relevant items',
        'zh': '找到 {total_count} 条相关信息',
        'ms': 'Ditemui {total_count} maklumat berkaitan',
    },
    'related_facts_header': {
        'en': '\n### Related facts:',
        'zh': '\n### 相关事实:',
        'ms': '\n### Fakta berkaitan:',
    },

    # -- NodeInfo --
    'unknown_type': {
        'en': 'Unknown type',
        'zh': '未知类型',
        'ms': 'Jenis tidak diketahui',
    },
    'entity_label': {
        'en': 'Entity: {name} (Type: {entity_type})\nSummary: {summary}',
        'zh': '实体: {name} (类型: {entity_type})\n摘要: {summary}',
        'ms': 'Entiti: {name} (Jenis: {entity_type})\nRingkasan: {summary}',
    },

    # -- EdgeInfo --
    'relationship_label': {
        'en': 'Relationship: {source} --[{name}]--> {target}\nFact: {fact}',
        'zh': '关系: {source} --[{name}]--> {target}\n事实: {fact}',
        'ms': 'Hubungan: {source} --[{name}]--> {target}\nFakta: {fact}',
    },
    'time_validity': {
        'en': '\nValidity: {valid_at} - {invalid_at}',
        'zh': '\n时效: {valid_at} - {invalid_at}',
        'ms': '\nKesahan: {valid_at} - {invalid_at}',
    },
    'expired_label': {
        'en': ' (Expired: {expired_at})',
        'zh': ' (已过期: {expired_at})',
        'ms': ' (Tamat tempoh: {expired_at})',
    },
    'unknown_time': {
        'en': 'Unknown',
        'zh': '未知',
        'ms': 'Tidak diketahui',
    },
    'until_now': {
        'en': 'Present',
        'zh': '至今',
        'ms': 'Sekarang',
    },

    # -- InsightForgeResult --
    'insight_forge_title': {
        'en': '## Deep Prediction Analysis',
        'zh': '## 未来预测深度分析',
        'ms': '## Analisis Ramalan Mendalam',
    },
    'analysis_question': {
        'en': 'Analysis question: {query}',
        'zh': '分析问题: {query}',
        'ms': 'Soalan analisis: {query}',
    },
    'prediction_scenario': {
        'en': 'Prediction scenario: {simulation_requirement}',
        'zh': '预测场景: {simulation_requirement}',
        'ms': 'Senario ramalan: {simulation_requirement}',
    },
    'prediction_stats_header': {
        'en': '\n### Prediction Data Statistics',
        'zh': '\n### 预测数据统计',
        'ms': '\n### Statistik Data Ramalan',
    },
    'related_prediction_facts': {
        'en': '- Related prediction facts: {count} items',
        'zh': '- 相关预测事实: {count}条',
        'ms': '- Fakta ramalan berkaitan: {count} item',
    },
    'involved_entities': {
        'en': '- Involved entities: {count} items',
        'zh': '- 涉及实体: {count}个',
        'ms': '- Entiti terlibat: {count} item',
    },
    'relationship_chains': {
        'en': '- Relationship chains: {count} items',
        'zh': '- 关系链: {count}条',
        'ms': '- Rantaian hubungan: {count} item',
    },
    'sub_questions_header': {
        'en': '\n### Analysed Sub-questions',
        'zh': '\n### 分析的子问题',
        'ms': '\n### Soalan Kecil yang Dianalisis',
    },
    'key_facts_header': {
        'en': '\n### [Key Facts] (Please cite these in the report)',
        'zh': '\n### 【关键事实】(请在报告中引用这些原文)',
        'ms': '\n### [Fakta Utama] (Sila petik ini dalam laporan)',
    },
    'core_entities_header': {
        'en': '\n### [Core Entities]',
        'zh': '\n### 【核心实体】',
        'ms': '\n### [Entiti Teras]',
    },
    'entity_type_label': {
        'en': 'Entity',
        'zh': '实体',
        'ms': 'Entiti',
    },
    'summary_label': {
        'en': '  Summary: "{summary}"',
        'zh': '  摘要: "{summary}"',
        'ms': '  Ringkasan: "{summary}"',
    },
    'related_facts_count': {
        'en': '  Related facts: {count} items',
        'zh': '  相关事实: {count}条',
        'ms': '  Fakta berkaitan: {count} item',
    },
    'relationship_chains_header': {
        'en': '\n### [Relationship Chains]',
        'zh': '\n### 【关系链】',
        'ms': '\n### [Rantaian Hubungan]',
    },

    # -- PanoramaResult --
    'panorama_title': {
        'en': '## Broad Search Results (Future Panoramic View)',
        'zh': '## 广度搜索结果（未来全景视图）',
        'ms': '## Hasil Carian Luas (Paparan Panorama Masa Depan)',
    },
    'panorama_query': {
        'en': 'Query: {query}',
        'zh': '查询: {query}',
        'ms': 'Pertanyaan: {query}',
    },
    'statistics_header': {
        'en': '\n### Statistics',
        'zh': '\n### 统计信息',
        'ms': '\n### Statistik',
    },
    'total_nodes': {
        'en': '- Total nodes: {count}',
        'zh': '- 总节点数: {count}',
        'ms': '- Jumlah nod: {count}',
    },
    'total_edges': {
        'en': '- Total edges: {count}',
        'zh': '- 总边数: {count}',
        'ms': '- Jumlah tepi: {count}',
    },
    'active_facts_count': {
        'en': '- Currently valid facts: {count} items',
        'zh': '- 当前有效事实: {count}条',
        'ms': '- Fakta sah semasa: {count} item',
    },
    'historical_facts_count': {
        'en': '- Historical/expired facts: {count} items',
        'zh': '- 历史/过期事实: {count}条',
        'ms': '- Fakta sejarah/tamat tempoh: {count} item',
    },
    'active_facts_header': {
        'en': '\n### [Currently Valid Facts] (Simulation results)',
        'zh': '\n### 【当前有效事实】(模拟结果原文)',
        'ms': '\n### [Fakta Sah Semasa] (Hasil simulasi)',
    },
    'historical_facts_header': {
        'en': '\n### [Historical/Expired Facts] (Evolution record)',
        'zh': '\n### 【历史/过期事实】(演变过程记录)',
        'ms': '\n### [Fakta Sejarah/Tamat Tempoh] (Rekod evolusi)',
    },
    'involved_entities_header': {
        'en': '\n### [Involved Entities]',
        'zh': '\n### 【涉及实体】',
        'ms': '\n### [Entiti Terlibat]',
    },

    # -- AgentInterview / InterviewResult --
    'bio_label': {
        'en': '_Bio: {bio}_',
        'zh': '_简介: {bio}_',
        'ms': '_Biodata: {bio}_',
    },
    'key_quotes_header': {
        'en': '\n**Key quotes:**',
        'zh': '\n**关键引言:**',
        'ms': '\n**Petikan utama:**',
    },
    'interview_report_title': {
        'en': '## In-depth Interview Report',
        'zh': '## 深度采访报告',
        'ms': '## Laporan Temu Bual Mendalam',
    },
    'interview_topic': {
        'en': '**Interview topic:** {topic}',
        'zh': '**采访主题:** {topic}',
        'ms': '**Topik temu bual:** {topic}',
    },
    'interview_count': {
        'en': '**Interviewees:** {interviewed_count} / {total_agents} simulated agents',
        'zh': '**采访人数:** {interviewed_count} / {total_agents} 位模拟Agent',
        'ms': '**Bilangan ditemu bual:** {interviewed_count} / {total_agents} ejen simulasi',
    },
    'selection_reasoning_header': {
        'en': '\n### Selection Reasoning',
        'zh': '\n### 采访对象选择理由',
        'ms': '\n### Alasan Pemilihan',
    },
    'auto_selected': {
        'en': '(Auto-selected)',
        'zh': '（自动选择）',
        'ms': '(Dipilih secara automatik)',
    },
    'interview_transcript_header': {
        'en': '\n### Interview Transcript',
        'zh': '\n### 采访实录',
        'ms': '\n### Transkrip Temu Bual',
    },
    'interview_number': {
        'en': '\n#### Interview #{num}: {agent_name}',
        'zh': '\n#### 采访 #{num}: {agent_name}',
        'ms': '\n#### Temu bual #{num}: {agent_name}',
    },
    'no_interviews': {
        'en': '(No interview records)',
        'zh': '（无采访记录）',
        'ms': '(Tiada rekod temu bual)',
    },
    'interview_summary_header': {
        'en': '\n### Interview Summary and Key Insights',
        'zh': '\n### 采访摘要与核心观点',
        'ms': '\n### Ringkasan Temu Bual dan Pandangan Utama',
    },
    'no_summary': {
        'en': '(No summary)',
        'zh': '（无摘要）',
        'ms': '(Tiada ringkasan)',
    },

    # ===================================================================
    # zep_tools.py  --  misc fallback / error strings
    # ===================================================================

    'unknown_error': {
        'en': 'Unknown error',
        'zh': '未知错误',
        'ms': 'Ralat tidak diketahui',
    },
    'unknown_profession': {
        'en': 'Unknown',
        'zh': '未知',
        'ms': 'Tidak diketahui',
    },
    'interview_api_failed': {
        'en': 'Interview API call failed: {error_msg}. Please check the OASIS simulation environment status.',
        'zh': '采访API调用失败：{error_msg}。请检查OASIS模拟环境状态。',
        'ms': 'Panggilan API temu bual gagal: {error_msg}. Sila semak status persekitaran simulasi OASIS.',
    },
}


def get_string(key: str, **kwargs) -> str:
    """
    Return a translated string for *key* in the currently configured language.

    Parameters
    ----------
    key : str
        Lookup key in the ``STRINGS`` dictionary.
    **kwargs
        Placeholder values that will be interpolated into the string
        via ``str.format()``.

    Returns
    -------
    str
        The translated, formatted string.  Falls back to English if the
        configured language is unavailable, or returns the raw key if
        the key itself is missing.
    """
    lang = getattr(Config, 'OUTPUT_LANGUAGE', 'en') or 'en'
    entry = STRINGS.get(key)
    if entry is None:
        return key

    text = entry.get(lang) or entry.get('en', key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return text
