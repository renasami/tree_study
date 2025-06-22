import hashlib
from typing import List, Optional, Union, Any, Tuple
from enum import Enum

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

class MerklePatriciaTrie17:
    """17分木Merkle Patricia Tree（イーサリアム式）"""
    
    def __init__(self):
        self.root = MPT17Node(NodeType.BLANK)
        self.stats = {
            "total_nodes": 0,
            "branch_nodes": 0,
            "extension_nodes": 0,
            "leaf_nodes": 0
        }
    
    @staticmethod
    def string_to_nibbles(s: str) -> str:
        """文字列を16進数のニブル列に変換"""
        # 各文字を16進数に変換し、ニブル（4ビット）単位に分解
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
    def common_prefix_length(s1: str, s2: str) -> int:
        """共通プレフィックスの長さを返す"""
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def insert(self, key: str, value: Any) -> None:
        """キーと値をトライに挿入"""
        print(f"\n{'='*60}")
        print(f"Inserting: '{key}' -> {value}")
        print(f"{'='*60}")
        
        # キーをニブルに変換
        nibbles = self.string_to_nibbles(key)
        print(f"Key in nibbles: {nibbles}")
        print(f"Nibble sequence: {' '.join(nibbles)}")
        
        # ルートが空の場合
        if self.root.node_type == NodeType.BLANK:
            self.root = MPT17Node(NodeType.LEAF)
            self.root.path = nibbles
            self.root.value = value
            self.stats["leaf_nodes"] += 1
            print(f"Created root LEAF node with path: {nibbles}")
        else:
            self._insert_recursive(self.root, nibbles, value, 0)
        
        # ハッシュを再計算
        root_hash = self.root.calculate_hash()
        print(f"\nRoot hash updated: {root_hash}")
    
    def _insert_recursive(self, node: MPT17Node, remaining_nibbles: str, value: Any, depth: int) -> MPT17Node:
        """再帰的に挿入"""
        indent = "  " * depth
        
        if node.node_type == NodeType.LEAF:
            print(f"{indent}Current node: LEAF with path '{node.path}'")
            
            # 共通プレフィックスを見つける
            common_len = self.common_prefix_length(node.path, remaining_nibbles)
            print(f"{indent}Common prefix length: {common_len}")
            
            if common_len == len(node.path) == len(remaining_nibbles):
                # 完全一致 - 値を更新
                print(f"{indent}Exact match - updating value")
                node.value = value
                return node
            
            # ブランチノードを作成
            branch = MPT17Node(NodeType.BRANCH)
            self.stats["branch_nodes"] += 1
            print(f"{indent}Creating BRANCH node")
            
            # 共通プレフィックスがある場合、拡張ノードを作成
            if common_len > 0:
                extension = MPT17Node(NodeType.EXTENSION)
                extension.path = node.path[:common_len]
                self.stats["extension_nodes"] += 1
                print(f"{indent}Creating EXTENSION node with path '{extension.path}'")
                
                # 既存のリーフノードを調整
                old_remaining = node.path[common_len:]
                new_remaining = remaining_nibbles[common_len:]
                
                if old_remaining:
                    old_nibble = int(old_remaining[0], 16)
                    old_leaf = MPT17Node(NodeType.LEAF)
                    old_leaf.path = old_remaining[1:]
                    old_leaf.value = node.value
                    branch.branches[old_nibble] = old_leaf
                    print(f"{indent}  Old leaf at branch[{old_nibble:x}] with remaining path '{old_leaf.path}'")
                else:
                    # 既存のノードは終端
                    branch.value = node.value
                    print(f"{indent}  Old value at branch terminator")
                
                if new_remaining:
                    new_nibble = int(new_remaining[0], 16)
                    new_leaf = MPT17Node(NodeType.LEAF)
                    new_leaf.path = new_remaining[1:]
                    new_leaf.value = value
                    branch.branches[new_nibble] = new_leaf
                    self.stats["leaf_nodes"] += 1
                    print(f"{indent}  New leaf at branch[{new_nibble:x}] with remaining path '{new_leaf.path}'")
                else:
                    # 新しいノードは終端
                    branch.value = value
                    print(f"{indent}  New value at branch terminator")
                
                # 拡張ノードの最初のブランチをセット
                extension.branches[0] = branch
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
                
                return branch
        
        elif node.node_type == NodeType.EXTENSION:
            print(f"{indent}Current node: EXTENSION with path '{node.path}'")
            
            common_len = self.common_prefix_length(node.path, remaining_nibbles)
            
            if common_len == len(node.path):
                # 拡張ノードのパスを通過
                remaining = remaining_nibbles[common_len:]
                print(f"{indent}Traversing extension, remaining: '{remaining}'")
                
                # 最初のブランチに進む（拡張ノードは1つの子しか持たない）
                if node.branches[0]:
                    node.branches[0] = self._insert_recursive(node.branches[0], remaining, value, depth + 1)
                return node
            else:
                # 拡張ノードを分割する必要がある
                print(f"{indent}Splitting extension node at position {common_len}")
                # （実装は省略 - より複雑）
                return node
        
        elif node.node_type == NodeType.BRANCH:
            print(f"{indent}Current node: BRANCH")
            
            if not remaining_nibbles:
                # ターミネーター位置に値を設定
                print(f"{indent}Setting value at terminator")
                node.value = value
            else:
                # 適切なブランチに進む
                nibble = int(remaining_nibbles[0], 16)
                remaining = remaining_nibbles[1:]
                print(f"{indent}Following branch[{nibble:x}], remaining: '{remaining}'")
                
                if node.branches[nibble] is None:
                    # 新しいリーフノードを作成
                    leaf = MPT17Node(NodeType.LEAF)
                    leaf.path = remaining
                    leaf.value = value
                    node.branches[nibble] = leaf
                    self.stats["leaf_nodes"] += 1
                    print(f"{indent}Created new leaf at branch[{nibble:x}]")
                else:
                    node.branches[nibble] = self._insert_recursive(
                        node.branches[nibble], remaining, value, depth + 1
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
    
    def print_tree(self, node: Optional[MPT17Node] = None, prefix: str = "", branch_info: str = "") -> None:
        """木構造を視覚的に表示"""
        if node is None:
            return
        
        if node == self.root:
            print(f"Root ({node.node_type.value}) hash={node.hash}")
            node = self.root
        elif branch_info:
            type_str = f"[{node.node_type.value.upper()}]"
            path_str = f" path='{node.path}'" if node.path else ""
            value_str = f" value={node.value}" if node.value is not None else ""
            hash_str = f" hash={node.hash}" if node.hash else ""
            print(f"{prefix}├── {branch_info} {type_str}{path_str}{value_str}{hash_str}")
        
        if node.node_type == NodeType.BRANCH:
            # ブランチの子を表示
            active_branches = [(i, b) for i, b in enumerate(node.branches) if b is not None]
            
            for idx, (i, branch) in enumerate(active_branches):
                is_last = idx == len(active_branches) - 1
                branch_char = f"[{i:x}]" if i < 16 else "[T]"  # T for terminator
                next_prefix = prefix + ("│   " if not is_last else "    ")
                self.print_tree(branch, next_prefix, branch_char)
        
        elif node.node_type == NodeType.EXTENSION:
            # 拡張ノードの子を表示
            if node.branches[0]:
                self.print_tree(node.branches[0], prefix + "    ", "→")
    
    def get_stats_summary(self) -> str:
        """統計情報のサマリーを返す"""
        total = sum(self.stats.values()) - self.stats["total_nodes"]
        self.stats["total_nodes"] = total
        
        return f"""
統計情報:
  総ノード数: {self.stats['total_nodes']}
  - Branch nodes: {self.stats['branch_nodes']}
  - Extension nodes: {self.stats['extension_nodes']}
  - Leaf nodes: {self.stats['leaf_nodes']}
"""


def demonstrate_17_tree():
    """17分木の動作をデモンストレーション"""
    print("="*80)
    print("17分木 Merkle Patricia Tree デモンストレーション")
    print("="*80)
    print("\n説明:")
    print("- 各ノードは最大17個の子を持つ（0-9, a-f の16進数 + 終端記号）")
    print("- キーは16進数のニブル（4ビット）単位で処理")
    print("- イーサリアムのアドレスやハッシュ値の保存に最適化")
    print("="*80)
    
    # テストケース1: 基本的な挿入
    print("\n[テストケース1: 基本的な挿入]")
    trie = MerklePatriciaTrie17()
    
    test_data = [
        ("cat", 100),
        ("car", 200),
        ("card", 300),
        ("dog", 400),
    ]
    
    for key, value in test_data:
        trie.insert(key, value)
    
    print("\n[最終的な木構造]")
    trie.print_tree()
    
    print(trie.get_stats_summary())
    
    # 検索テスト
    print("\n[検索テスト]")
    for key, expected in test_data:
        result = trie.search(key)
        status = "✓" if result == expected else "✗"
        print(f"{status} Search '{key}': {result} (expected: {expected})")
    
    # テストケース2: 16進数文字列での動作
    print("\n" + "="*80)
    print("[テストケース2: 16進数アドレス風のキー]")
    print("="*80)
    
    trie2 = MerklePatriciaTrie17()
    
    # イーサリアムアドレス風のキー（短縮版）
    addresses = [
        ("0xAB", 1000),
        ("0xABC", 2000),
        ("0xABCD", 3000),
        ("0xBA", 4000),
    ]
    
    for addr, balance in addresses:
        trie2.insert(addr, balance)
    
    print("\n[アドレス風キーでの木構造]")
    trie2.print_tree()
    
    # ニブル表現の説明
    print("\n[ニブル変換の例]")
    for key, _ in test_data[:2]:
        nibbles = MerklePatriciaTrie17.string_to_nibbles(key)
        print(f"'{key}' -> nibbles: {nibbles} ({' '.join(nibbles)})")
        
        # ASCIIコードも表示
        ascii_codes = [f"{ord(c):02x}" for c in key]
        print(f"     ASCII: {' '.join(ascii_codes)}")


def compare_with_standard_patricia():
    """標準的なPatricia Treeと17分木の比較"""
    print("\n" + "="*80)
    print("標準Patricia Tree vs 17分木の比較")
    print("="*80)
    
    # 同じデータで両方を構築
    test_data = [
        ("test", 1),
        ("testing", 2),
        ("tester", 3),
        ("team", 4),
    ]
    
    print("テストデータ:", [k for k, _ in test_data])
    
    # 17分木の場合
    print("\n[17分木でのニブル表現]")
    for key, _ in test_data:
        nibbles = MerklePatriciaTrie17.string_to_nibbles(key)
        print(f"  '{key}' -> {nibbles} (長さ: {len(nibbles)} ニブル)")
    
    print("\n[17分木の利点]")
    print("1. 16進数データ（アドレス、ハッシュ）に最適化")
    print("2. 各ノードの分岐数が固定（17）で予測可能")
    print("3. ニブル単位の処理により、バイト境界を跨ぐキーも効率的に処理")
    print("4. ブロックチェーンでの状態管理に適している")


if __name__ == "__main__":
    demonstrate_17_tree()
    compare_with_standard_patricia()