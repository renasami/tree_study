import hashlib
from typing import List, Optional, Union, Any, Tuple, Dict
from enum import Enum
import sys

class NodeType(Enum):
    """ノードタイプの定義"""
    BLANK = "blank"          # 空ノード
    LEAF = "leaf"            # リーフノード（キーの終端）
    EXTENSION = "extension"  # 拡張ノード（共通プレフィックス）
    BRANCH = "branch"        # ブランチノード（17分岐）

class MPT17Node:
    """17分木Merkle Patricia Treeのノード"""
    def __init__(self, node_type: NodeType):
        self.node_type = node_type
        self.branches: List[Optional['MPT17Node']] = [None] * 17  # 0-15 + terminator
        self.path: str = ""  # Extension/Leafノードのパス（nibbles）
        self.value: Optional[Any] = None
        self.hash: Optional[str] = None
    
    def calculate_hash(self) -> str:
        """ノードのハッシュを計算"""
        hasher = hashlib.sha256()
        
        # ノードタイプをハッシュに含める
        hasher.update(self.node_type.value.encode())
        
        if self.node_type == NodeType.LEAF:
            hasher.update(self.path.encode())
            hasher.update(str(self.value).encode() if self.value else b"")
            
        elif self.node_type == NodeType.EXTENSION:
            hasher.update(self.path.encode())
            # 子ノードのハッシュを含める
            for branch in self.branches:
                if branch:
                    hasher.update(branch.calculate_hash().encode())
                    
        elif self.node_type == NodeType.BRANCH:
            # 各ブランチのハッシュを含める
            for i, branch in enumerate(self.branches):
                if branch:
                    hasher.update(f"{i}:".encode())
                    hasher.update(branch.calculate_hash().encode())
            # ターミネーター（インデックス16）の値
            if self.value is not None:
                hasher.update(b"value:")
                hasher.update(str(self.value).encode())
        
        self.hash = hasher.hexdigest()[:16]
        return self.hash
    
    def get_memory_size(self) -> int:
        """ノードのメモリ使用量を推定（バイト）"""
        size = sys.getsizeof(self)
        size += sys.getsizeof(self.branches)
        size += sys.getsizeof(self.path)
        size += sys.getsizeof(self.value)
        size += sys.getsizeof(self.hash) if self.hash else 0
        size += sys.getsizeof(self.node_type)
        
        # 各ブランチへの参照
        for branch in self.branches:
            if branch is not None:
                size += sys.getsizeof(branch)
        
        return size

class MerklePatriciaTrie17:
    """17分木Merkle Patricia Tree（イーサリアム式）"""
    
    def __init__(self, show_steps: bool = False):
        self.root = MPT17Node(NodeType.BLANK)
        self.show_steps = show_steps
        self.insertion_count = 0
        self.stats = {
            "total_nodes": 0,
            "branch_nodes": 0,
            "extension_nodes": 0,
            "leaf_nodes": 0,
            "blank_nodes": 1  # 初期ルート
        }
    
    @staticmethod
    def string_to_nibbles(s: str) -> str:
        """文字列を16進数のニブル列に変換"""
        nibbles = ""
        for char in s:
            hex_val = format(ord(char), '02x')
            nibbles += hex_val
        return nibbles
    
    @staticmethod
    def nibbles_to_string(nibbles: str) -> str:
        """ニブル列を文字列に戻す"""
        if len(nibbles) % 2 != 0:
            raise ValueError("Invalid nibbles length")
        
        result = ""
        for i in range(0, len(nibbles), 2):
            hex_val = nibbles[i:i+2]
            result += chr(int(hex_val, 16))
        return result
    
    @staticmethod
    def format_nibbles(nibbles: str, max_length: int = 20) -> str:
        """ニブルを見やすくフォーマット"""
        if len(nibbles) <= max_length:
            return ' '.join(nibbles)
        else:
            return ' '.join(nibbles[:max_length]) + f"... ({len(nibbles)} nibbles)"
    
    @staticmethod
    def common_prefix_length(s1: str, s2: str) -> int:
        """共通プレフィックスの長さを返す"""
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def insert(self, key: str, value: Any) -> None:
        """キーと値をトライに挿入"""
        self.insertion_count += 1
        
        if self.show_steps:
            print(f"\n{'='*80}")
            print(f"[Insertion #{self.insertion_count}] Inserting: '{key}' -> {value}")
            print(f"{'='*80}")
        
        # キーをニブルに変換
        nibbles = self.string_to_nibbles(key)
        
        if self.show_steps:
            print(f"\nKey conversion:")
            print(f"  Original: '{key}'")
            print(f"  ASCII codes: {' '.join([f'{ord(c):02x}' for c in key])}")
            print(f"  Nibbles: {nibbles}")
            print(f"  Formatted: {self.format_nibbles(nibbles)}")
        
        # ルートが空の場合
        if self.root.node_type == NodeType.BLANK:
            self.root = MPT17Node(NodeType.LEAF)
            self.root.path = nibbles
            self.root.value = value
            self.stats["blank_nodes"] -= 1
            self.stats["leaf_nodes"] += 1
            
            if self.show_steps:
                print(f"\n✓ Created root LEAF node")
                print(f"  Path: {self.format_nibbles(nibbles)}")
                print(f"  Value: {value}")
        else:
            # 重要: _insert_recursiveの戻り値でルートを更新
            self.root = self._insert_recursive(self.root, nibbles, value, 0, "root")
        
        # ハッシュを再計算
        old_hash = self.root.hash
        new_hash = self.root.calculate_hash()
        
        if self.show_steps:
            print(f"\n🔒 Hash Update:")
            print(f"  Old root hash: {old_hash}")
            print(f"  New root hash: {new_hash}")
            
            print(f"\n[Tree structure after insertion]")
            self.print_tree(show_details=True)
    
    def _insert_recursive(self, node: MPT17Node, remaining_nibbles: str, value: Any, 
                         depth: int, path_info: str) -> MPT17Node:
        """再帰的に挿入"""
        indent = "  " * depth
        
        if self.show_steps:
            print(f"\n{indent}📍 At {path_info}")
            print(f"{indent}  Node type: {node.node_type.value}")
            if node.path:
                print(f"{indent}  Node path: {self.format_nibbles(node.path)}")
            print(f"{indent}  Remaining nibbles: {self.format_nibbles(remaining_nibbles)}")
        
        if node.node_type == NodeType.LEAF:
            # 共通プレフィックスを見つける
            common_len = self.common_prefix_length(node.path, remaining_nibbles)
            
            if self.show_steps:
                print(f"{indent}  Common prefix length: {common_len}")
                if common_len > 0:
                    print(f"{indent}  Common prefix: {self.format_nibbles(node.path[:common_len])}")
            
            if common_len == len(node.path) == len(remaining_nibbles):
                # 完全一致 - 値を更新
                if self.show_steps:
                    print(f"{indent}  ✓ Exact match - updating value")
                node.value = value
                return node
            
            # ブランチノードを作成
            branch = MPT17Node(NodeType.BRANCH)
            self.stats["branch_nodes"] += 1
            
            if self.show_steps:
                print(f"{indent}  🌿 Creating BRANCH node")
            
            # 共通プレフィックスがある場合、拡張ノードを作成
            if common_len > 0:
                extension = MPT17Node(NodeType.EXTENSION)
                extension.path = node.path[:common_len]
                self.stats["extension_nodes"] += 1
                
                if self.show_steps:
                    print(f"{indent}  📏 Creating EXTENSION node")
                    print(f"{indent}    Extension path: {self.format_nibbles(extension.path)}")
                
                # 既存のリーフノードを調整
                old_remaining = node.path[common_len:]
                new_remaining = remaining_nibbles[common_len:]
                
                if old_remaining:
                    old_nibble = int(old_remaining[0], 16)
                    old_leaf = MPT17Node(NodeType.LEAF)
                    old_leaf.path = old_remaining[1:]
                    old_leaf.value = node.value
                    branch.branches[old_nibble] = old_leaf
                    
                    if self.show_steps:
                        print(f"{indent}    Old leaf → branch[{old_nibble:x}]")
                        print(f"{indent}      Remaining path: {self.format_nibbles(old_leaf.path)}")
                else:
                    # 既存のノードは終端
                    branch.value = node.value
                    
                    if self.show_steps:
                        print(f"{indent}    Old value → branch terminator")
                
                if new_remaining:
                    new_nibble = int(new_remaining[0], 16)
                    new_leaf = MPT17Node(NodeType.LEAF)
                    new_leaf.path = new_remaining[1:]
                    new_leaf.value = value
                    branch.branches[new_nibble] = new_leaf
                    self.stats["leaf_nodes"] += 1
                    
                    if self.show_steps:
                        print(f"{indent}    New leaf → branch[{new_nibble:x}]")
                        print(f"{indent}      Remaining path: {self.format_nibbles(new_leaf.path)}")
                else:
                    # 新しいノードは終端
                    branch.value = value
                    
                    if self.show_steps:
                        print(f"{indent}    New value → branch terminator")
                
                # 拡張ノードの最初のブランチをセット
                extension.branches[0] = branch
                self.stats["leaf_nodes"] -= 1  # 元のリーフノードを削除カウント
                return extension
            else:
                # 共通プレフィックスなし - 直接ブランチに分岐
                old_nibble = int(node.path[0], 16)
                old_leaf = MPT17Node(NodeType.LEAF)
                old_leaf.path = node.path[1:]
                old_leaf.value = node.value
                branch.branches[old_nibble] = old_leaf
                
                new_nibble = int(remaining_nibbles[0], 16)
                new_leaf = MPT17Node(NodeType.LEAF)
                new_leaf.path = remaining_nibbles[1:]
                new_leaf.value = value
                branch.branches[new_nibble] = new_leaf
                self.stats["leaf_nodes"] += 1
                
                if self.show_steps:
                    print(f"{indent}    No common prefix - direct branching")
                    print(f"{indent}    Old → branch[{old_nibble:x}]")
                    print(f"{indent}    New → branch[{new_nibble:x}]")
                
                return branch
        
        elif node.node_type == NodeType.EXTENSION:
            common_len = self.common_prefix_length(node.path, remaining_nibbles)
            
            if common_len == len(node.path):
                # 拡張ノードのパスを通過
                remaining = remaining_nibbles[common_len:]
                
                if self.show_steps:
                    print(f"{indent}  ↓ Traversing extension")
                    print(f"{indent}    Consumed: {self.format_nibbles(node.path)}")
                    print(f"{indent}    Remaining: {self.format_nibbles(remaining)}")
                
                # 最初のブランチに進む（拡張ノードは1つの子しか持たない）
                if node.branches[0]:
                    node.branches[0] = self._insert_recursive(
                        node.branches[0], remaining, value, depth + 1, 
                        f"{path_info} → extension"
                    )
                return node
            else:
                # 拡張ノードを分割する必要がある
                if self.show_steps:
                    print(f"{indent}  ✂️ Splitting extension node at position {common_len}")
                
                # 新しいブランチノードを作成
                new_branch = MPT17Node(NodeType.BRANCH)
                self.stats["branch_nodes"] += 1
                
                # 共通部分がある場合は新しい拡張ノードを作成
                if common_len > 0:
                    new_extension = MPT17Node(NodeType.EXTENSION)
                    new_extension.path = node.path[:common_len]
                    self.stats["extension_nodes"] += 1
                    
                    # 既存の拡張ノードの残り
                    old_remaining = node.path[common_len:]
                    old_nibble = int(old_remaining[0], 16)
                    
                    # 既存の拡張ノードを調整
                    if len(old_remaining) > 1:
                        shortened_extension = MPT17Node(NodeType.EXTENSION)
                        shortened_extension.path = old_remaining[1:]
                        shortened_extension.branches[0] = node.branches[0]
                        new_branch.branches[old_nibble] = shortened_extension
                    else:
                        new_branch.branches[old_nibble] = node.branches[0]
                    
                    # 新しい値を挿入
                    new_remaining = remaining_nibbles[common_len:]
                    if new_remaining:
                        new_nibble = int(new_remaining[0], 16)
                        new_leaf = MPT17Node(NodeType.LEAF)
                        new_leaf.path = new_remaining[1:]
                        new_leaf.value = value
                        new_branch.branches[new_nibble] = new_leaf
                        self.stats["leaf_nodes"] += 1
                    else:
                        new_branch.value = value
                    
                    new_extension.branches[0] = new_branch
                    return new_extension
                else:
                    # 共通部分なし
                    old_nibble = int(node.path[0], 16)
                    if len(node.path) > 1:
                        shortened_extension = MPT17Node(NodeType.EXTENSION)
                        shortened_extension.path = node.path[1:]
                        shortened_extension.branches[0] = node.branches[0]
                        new_branch.branches[old_nibble] = shortened_extension
                    else:
                        new_branch.branches[old_nibble] = node.branches[0]
                    
                    new_nibble = int(remaining_nibbles[0], 16)
                    new_leaf = MPT17Node(NodeType.LEAF)
                    new_leaf.path = remaining_nibbles[1:]
                    new_leaf.value = value
                    new_branch.branches[new_nibble] = new_leaf
                    self.stats["leaf_nodes"] += 1
                    
                    return new_branch
        
        elif node.node_type == NodeType.BRANCH:
            if not remaining_nibbles:
                # ターミネーター位置に値を設定
                if self.show_steps:
                    print(f"{indent}  ✓ Setting value at terminator")
                node.value = value
            else:
                # 適切なブランチに進む
                nibble = int(remaining_nibbles[0], 16)
                remaining = remaining_nibbles[1:]
                
                if self.show_steps:
                    print(f"{indent}  → Following branch[{nibble:x}]")
                    print(f"{indent}    Remaining: {self.format_nibbles(remaining)}")
                
                if node.branches[nibble] is None:
                    # 新しいリーフノードを作成
                    leaf = MPT17Node(NodeType.LEAF)
                    leaf.path = remaining
                    leaf.value = value
                    node.branches[nibble] = leaf
                    self.stats["leaf_nodes"] += 1
                    
                    if self.show_steps:
                        print(f"{indent}    ✓ Created new leaf at branch[{nibble:x}]")
                        print(f"{indent}      Path: {self.format_nibbles(remaining)}")
                else:
                    node.branches[nibble] = self._insert_recursive(
                        node.branches[nibble], remaining, value, depth + 1,
                        f"{path_info} → branch[{nibble:x}]"
                    )
            
            return node
        
        return node
    
    def search(self, key: str) -> Optional[Any]:
        """キーに対応する値を検索"""
        nibbles = self.string_to_nibbles(key)
        return self._search_recursive(self.root, nibbles)
    
    def _search_recursive(self, node: Optional[MPT17Node], remaining_nibbles: str) -> Optional[Any]:
        """再帰的に検索"""
        if node is None or node.node_type == NodeType.BLANK:
            return None
        
        if node.node_type == NodeType.LEAF:
            if node.path == remaining_nibbles:
                return node.value
            return None
        
        elif node.node_type == NodeType.EXTENSION:
            if remaining_nibbles.startswith(node.path):
                remaining = remaining_nibbles[len(node.path):]
                return self._search_recursive(node.branches[0], remaining)
            return None
        
        elif node.node_type == NodeType.BRANCH:
            if not remaining_nibbles:
                return node.value  # ターミネーターの値
            
            nibble = int(remaining_nibbles[0], 16)
            remaining = remaining_nibbles[1:]
            return self._search_recursive(node.branches[nibble], remaining)
        
        return None
    
    def print_tree(self, node: Optional[MPT17Node] = None, prefix: str = "", 
                   branch_info: str = "", show_details: bool = False, is_last: bool = True) -> None:
        """木構造を視覚的に表示"""
        # デバッグモード（必要に応じて有効化）
        debug = False
        
        # 初回呼び出し時
        if node is None:
            node = self.root
            if debug:
                print(f"[DEBUG] Starting print_tree with root node type: {node.node_type}")
            
            type_str = f"({node.node_type.value})"
            hash_str = f" hash={node.hash}" if node.hash else ""
            print(f"Root {type_str}{hash_str}")
            
            # ルートノードがBLANKの場合
            if node.node_type == NodeType.BLANK:
                print("└── (empty)")
                return
            
            # ルートノードがLEAFの場合
            elif node.node_type == NodeType.LEAF:
                path_str = f" path='{node.path}'" if node.path else ""
                value_str = f" value={node.value}" if node.value is not None else ""
                print(f"└── [LEAF]{path_str}{value_str}")
                return
            
            # BRANCHまたはEXTENSIONの場合、再帰的に処理
            elif node.node_type == NodeType.BRANCH:
                if debug:
                    print(f"[DEBUG] Root is BRANCH, processing children")
                self._print_branch_children(node, "", show_details)
                return
            
            elif node.node_type == NodeType.EXTENSION:
                if debug:
                    print(f"[DEBUG] Root is EXTENSION, processing child")
                # 拡張ノードは最初のブランチに子を持つ
                if node.branches[0] is not None:
                    self.print_tree(node.branches[0], "└── ", "→", show_details, True)
                return
        
        # 再帰呼び出し時の処理
        # 接続線を決定
        connector = "└── " if is_last else "├── "
        type_str = f"[{node.node_type.value.upper()}]"
        
        # パスを表示（長い場合は省略）
        path_str = ""
        if node.path:
            if show_details or len(node.path) <= 10:
                path_str = f" path='{node.path}'"
            else:
                path_str = f" path='{node.path[:10]}...({len(node.path)}nibbles)'"
        
        value_str = f" value={node.value}" if node.value is not None else ""
        hash_str = f" hash={node.hash[:8]}..." if node.hash and show_details else ""
        
        print(f"{prefix}{connector}{branch_info} {type_str}{path_str}{value_str}{hash_str}")
        
        # 子ノードのための新しいprefix
        new_prefix = prefix + ("    " if is_last else "│   ")
        
        # ノードタイプに応じて子を処理
        if node.node_type == NodeType.BRANCH:
            self._print_branch_children(node, new_prefix, show_details)
        elif node.node_type == NodeType.EXTENSION:
            if node.branches[0] is not None:
                self.print_tree(node.branches[0], new_prefix, "→", show_details, True)
    
    def print_tree_simple(self) -> None:
        """シンプルな木構造表示（デバッグ用）"""
        print("\n[Simple Tree View]")
        print(f"Root type: {self.root.node_type.value}")
        if self.root.hash:
            print(f"Root hash: {self.root.hash}")
        
        self._print_node_simple(self.root, "", "ROOT")
    
    def _print_node_simple(self, node: MPT17Node, indent: str, label: str) -> None:
        """ノードをシンプルに表示"""
        # ノードの基本情報を表示
        type_label = node.node_type.value.upper()
        path_info = f" path='{node.path}'" if node.path else ""
        value_info = f" value={node.value}" if node.value is not None else ""
        
        print(f"{indent}{label}: [{type_label}]{path_info}{value_info}")
        
        # 子ノードを表示
        if node.node_type == NodeType.BRANCH:
            # ターミネーター値
            if node.value is not None:
                print(f"{indent}  └─ [T] terminator: {node.value}")
            
            # 各ブランチ
            for i in range(16):
                if node.branches[i] is not None:
                    self._print_node_simple(node.branches[i], indent + "  ", f"[{i:x}]")
        
        elif node.node_type == NodeType.EXTENSION:
            if node.branches[0] is not None:
                self._print_node_simple(node.branches[0], indent + "  ", "→")
    
    def _print_branch_children(self, node: MPT17Node, prefix: str, show_details: bool) -> None:
        """ブランチノードの子要素を表示"""
        children = []
        
        # ターミネーターの値があるか確認（インデックス16）
        if node.value is not None:
            children.append(("T", "terminator", node.value))
        
        # アクティブなブランチを収集（0-15）
        for i in range(16):
            if node.branches[i] is not None:
                children.append((i, f"[{i:x}]", node.branches[i]))
        
        # 子要素を表示
        for idx, child_info in enumerate(children):
            is_last_child = idx == len(children) - 1
            
            if len(child_info) == 3 and isinstance(child_info[2], MPT17Node):
                # 通常のブランチ
                _, label, child_node = child_info
                self.print_tree(child_node, prefix, label, show_details, is_last_child)
            else:
                # ターミネーター値
                _, label, value = child_info
                connector = "└── " if is_last_child else "├── "
                print(f"{prefix}{connector}[{label}] value={value}")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        def count_recursive(node, depth=0):
            if node is None:
                return 0, [], 0, [], []
            
            count = 1
            depths = [depth]
            memory = node.get_memory_size()
            path_lengths = []
            branch_factors = []
            
            if node.path:
                path_lengths.append(len(node.path))
            
            if node.node_type == NodeType.BRANCH:
                active_branches = sum(1 for b in node.branches if b is not None)
                branch_factors.append(active_branches)
            
            for branch in node.branches:
                if branch:
                    c, d, m, p, b = count_recursive(branch, depth + 1)
                    count += c
                    depths.extend(d)
                    memory += m
                    path_lengths.extend(p)
                    branch_factors.extend(b)
            
            return count, depths, memory, path_lengths, branch_factors
        
        node_count, depths, total_memory, path_lengths, branch_factors = count_recursive(self.root)
        
        return {
            "node_count": node_count,
            "node_types": {
                "branch": self.stats["branch_nodes"],
                "extension": self.stats["extension_nodes"],
                "leaf": self.stats["leaf_nodes"]
            },
            "max_depth": max(depths) if depths else 0,
            "avg_depth": sum(depths) / len(depths) if depths else 0,
            "total_memory": total_memory,
            "avg_memory_per_node": total_memory / node_count if node_count > 0 else 0,
            "avg_path_length": sum(path_lengths) / len(path_lengths) if path_lengths else 0,
            "avg_branch_factor": sum(branch_factors) / len(branch_factors) if branch_factors else 0,
            "max_branch_factor": max(branch_factors) if branch_factors else 0
        }
    
    def visualize_stats(self):
        """統計情報を視覚的に表示"""
        stats = self.get_stats()
        
        print("\n" + "="*60)
        print("📊 統計情報")
        print("="*60)
        
        print(f"\n📈 ノード統計:")
        print(f"  総ノード数: {stats['node_count']}")
        print(f"  - Branch nodes: {stats['node_types']['branch']}")
        print(f"  - Extension nodes: {stats['node_types']['extension']}")
        print(f"  - Leaf nodes: {stats['node_types']['leaf']}")
        
        print(f"\n🌳 木の構造:")
        print(f"  最大深さ: {stats['max_depth']}")
        print(f"  平均深さ: {stats['avg_depth']:.2f}")
        print(f"  平均分岐因子: {stats['avg_branch_factor']:.2f}")
        print(f"  最大分岐因子: {stats['max_branch_factor']}")
        
        print(f"\n💾 メモリ使用量:")
        print(f"  総メモリ: {stats['total_memory']:,} bytes")
        print(f"  ノードあたり平均: {stats['avg_memory_per_node']:.1f} bytes")
        
        print(f"\n🔤 パス長:")
        print(f"  平均パス長: {stats['avg_path_length']:.2f} nibbles")
        
        # メモリ使用量のバーグラフ
        self._draw_memory_bar(stats)
    
    def _draw_memory_bar(self, stats):
        """メモリ使用量のバーグラフを描画"""
        node_types = stats['node_types']
        total = sum(node_types.values())
        
        if total == 0:
            return
        
        print(f"\n📊 ノードタイプ分布:")
        max_bar_width = 40
        
        for node_type, count in node_types.items():
            if count > 0:
                percentage = (count / total) * 100
                bar_width = int((count / total) * max_bar_width)
                bar = "█" * bar_width
                print(f"  {node_type:10}: {bar} {count:3} ({percentage:5.1f}%)")


def interactive_demo():
    """インタラクティブなデモ"""
    trie = None
    
    while True:
        print("\n" + "="*80)
        print("🌲 17分木 Merkle Patricia Tree インタラクティブデモ")
        print("="*80)
        print("1. 新しいトライを作成")
        print("2. キー/値を挿入（ステップ表示あり）")
        print("3. キー/値を挿入（ステップ表示なし）")
        print("4. 値を検索")
        print("5. 木構造を表示（簡易）")
        print("6. 木構造を表示（詳細）")
        print("7. 統計情報を表示")
        print("8. プリセットデータでテスト")
        print("9. ニブル変換の説明")
        print("10. シンプル表示（デバッグ用）")
        print("0. 終了")
        print("-"*80)
        
        choice = input("選択してください (0-10): ").strip()
        
        if choice == "0":
            print("終了します...")
            break
        
        elif choice == "1":
            show_steps = input("ステップ表示を有効にしますか？ (y/n): ").strip().lower() == 'y'
            trie = MerklePatriciaTrie17(show_steps=show_steps)
            print("✓ 新しいトライを作成しました")
        
        elif choice in ["2", "3"]:
            if trie is None:
                print("❌ まずトライを作成してください（オプション1）")
                continue
            
            key = input("キーを入力: ").strip()
            if not key:
                print("❌ キーが空です")
                continue
            
            try:
                value = int(input("値を入力（整数）: ").strip())
            except ValueError:
                print("❌ 無効な値です")
                continue
            
            # 一時的にshow_stepsを設定
            old_show_steps = trie.show_steps
            trie.show_steps = (choice == "2")
            
            trie.insert(key, value)
            
            trie.show_steps = old_show_steps
            
            if choice == "3":
                print(f"✓ '{key}' -> {value} を挿入しました")
        
        elif choice == "4":
            if trie is None:
                print("❌ まずトライを作成してください")
                continue
            
            key = input("検索するキーを入力: ").strip()
            result = trie.search(key)
            
            if result is not None:
                print(f"✓ 見つかりました: '{key}' -> {result}")
            else:
                print(f"❌ '{key}' は見つかりませんでした")
        
        elif choice in ["5", "6"]:
            if trie is None:
                print("❌ まずトライを作成してください")
                continue
            
            show_details = (choice == "6")
            print("\n[現在の木構造]")
            trie.print_tree(show_details=show_details)
        
        elif choice == "7":
            if trie is None:
                print("❌ まずトライを作成してください")
                continue
            
            trie.visualize_stats()
        
        elif choice == "8":
            print("\nプリセットデータセットを選択:")
            print("1. 基本テスト（cat, car, card, dog）")
            print("2. 共通プレフィックステスト（test, testing, tester, team）")
            print("3. イーサリアムアドレス風（0xAB, 0xABC, 0xABCD, 0xBA）")
            
            preset_choice = input("選択 (1-3): ").strip()
            
            presets = {
                "1": [("cat", 100), ("car", 200), ("card", 300), ("dog", 400)],
                "2": [("test", 1), ("testing", 2), ("tester", 3), ("team", 4)],
                "3": [("0xAB", 1000), ("0xABC", 2000), ("0xABCD", 3000), ("0xBA", 4000)]
            }
            
            if preset_choice in presets:
                show_steps = input("ステップ表示を有効にしますか？ (y/n): ").strip().lower() == 'y'
                trie = MerklePatriciaTrie17(show_steps=show_steps)
                
                for key, value in presets[preset_choice]:
                    trie.insert(key, value)
                
                print("\n✓ プリセットデータを挿入しました")
                print("\n[最終的な木構造]")
                trie.print_tree(show_details=True)
                
                # シンプル表示も追加
                print("\n[シンプル表示でも確認]")
                trie.print_tree_simple()
            else:
                print("❌ 無効な選択です")
        
        elif choice == "9":
            print("\n" + "="*60)
            print("📚 ニブル変換の説明")
            print("="*60)
            
            example = input("変換する文字列を入力（デフォルト: 'cat'）: ").strip() or "cat"
            
            print(f"\n文字列: '{example}'")
            print("\n変換プロセス:")
            
            for i, char in enumerate(example):
                ascii_code = ord(char)
                hex_val = format(ascii_code, '02x')
                print(f"  '{char}' -> ASCII: {ascii_code} -> 16進数: 0x{hex_val} -> ニブル: {hex_val[0]} {hex_val[1]}")
            
            nibbles = MerklePatriciaTrie17.string_to_nibbles(example)
            print(f"\n最終的なニブル列: {nibbles}")
            print(f"フォーマット済み: {' '.join(nibbles)}")
            
            print("\n📝 説明:")
            print("- 各文字は8ビット（1バイト）")
            print("- 1バイト = 2ニブル（各4ビット）")
            print("- 16進数の1文字 = 1ニブル")
            print("- 17分木では各ニブルが分岐を決定（0-F + 終端）")
        
        elif choice == "10":
            if trie is None:
                print("❌ まずトライを作成してください")
                continue
            
            trie.print_tree_simple()
        
        else:
            print("❌ 無効な選択です")


def test_tree_display():
    """木構造表示のテスト"""
    print("木構造表示のテスト")
    print("="*60)
    
    # テスト用のトライを作成
    trie = MerklePatriciaTrie17(show_steps=False)
    
    # データを挿入
    test_data = [("cat", 100), ("car", 200), ("card", 300), ("dog", 400)]
    print("テストデータ:", test_data)
    
    for key, value in test_data:
        trie.insert(key, value)
    
    print("\n[シンプル表示]")
    trie.print_tree_simple()
    
    print("\n[通常表示（簡易）]")
    trie.print_tree(show_details=False)
    
    print("\n[通常表示（詳細）]")
    trie.print_tree(show_details=True)
    
    # 統計情報も表示
    print("\n[統計情報]")
    trie.visualize_stats()
    
    # イーサリアム風アドレスもテスト
    print("\n\n" + "="*60)
    print("イーサリアム風アドレスのテスト")
    print("="*60)
    
    trie2 = MerklePatriciaTrie17(show_steps=False)
    eth_data = [("0xAB", 1000), ("0xABC", 2000), ("0xABCD", 3000), ("0xBA", 4000)]
    print("テストデータ:", eth_data)
    
    for key, value in eth_data:
        trie2.insert(key, value)
    
    print("\n[シンプル表示]")
    trie2.print_tree_simple()
    
    print("\n[通常表示]")
    trie2.print_tree(show_details=True)


if __name__ == "__main__":
    # テストモードかインタラクティブモードを選択
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_tree_display()
    else:
        interactive_demo()