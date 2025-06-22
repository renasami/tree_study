import hashlib
from typing import Dict, Optional, Any, Tuple
import sys

# ===== 1. True Basic Radix Tree（1文字ずつ処理）=====
class TrueBasicRadixNode:
    def __init__(self):
        self.children: Dict[str, 'TrueBasicRadixNode'] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None
        
    def get_memory_size(self) -> int:
        """ノードのメモリ使用量を推定（バイト）"""
        size = sys.getsizeof(self)
        size += sys.getsizeof(self.children)
        size += sys.getsizeof(self.is_end_of_word)
        size += sys.getsizeof(self.value)
        # 子ノードへの参照
        for key in self.children:
            size += sys.getsizeof(key)  # キー（文字）のサイズ
        return size

class TrueBasicRadixTree:
    """本来のBasic Radix Tree - 1文字ずつのエッジ"""
    def __init__(self):
        self.root = TrueBasicRadixNode()
    
    def insert(self, key: str, value: Any) -> None:
        node = self.root
        
        # 1文字ずつ処理
        for char in key:
            if char not in node.children:
                node.children[char] = TrueBasicRadixNode()
            node = node.children[char]
        
        node.is_end_of_word = True
        node.value = value
    
    def search(self, key: str) -> Optional[Any]:
        node = self.root
        for char in key:
            if char not in node.children:
                return None
            node = node.children[char]
        return node.value if node.is_end_of_word else None
    
    def print_tree(self, node: Optional[TrueBasicRadixNode] = None, prefix: str = "", char: str = "") -> None:
        if node is None:
            node = self.root
            print("Root")
        
        if char:
            end_marker = " (*)" if node.is_end_of_word else ""
            value_str = f" [{node.value}]" if node.value is not None else ""
            children_count = len(node.children)
            node_info = f" (children: {children_count})" if children_count > 0 and not node.is_end_of_word else ""
            print(f"{prefix}├── '{char}'{end_marker}{value_str}{node_info}")
        
        sorted_children = sorted(node.children.items())
        for i, (child_char, child_node) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            next_prefix = prefix + ("    " if char == "" else ("│   " if not is_last else "    "))
            self.print_tree(child_node, next_prefix, child_char)
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        def count_recursive(node):
            count = 1
            depth_list = [0]
            memory = node.get_memory_size()
            
            for child in node.children.values():
                child_count, child_depths, child_memory = count_recursive(child)
                count += child_count
                depth_list.extend([d + 1 for d in child_depths])
                memory += child_memory
            
            return count, depth_list, memory
        
        node_count, depths, total_memory = count_recursive(self.root)
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        
        return {
            "node_count": node_count,
            "max_depth": max_depth,
            "avg_depth": avg_depth,
            "total_memory": total_memory,
            "avg_memory_per_node": total_memory / node_count if node_count > 0 else 0
        }


# ===== 2. Patricia Tree（パス圧縮あり）=====
class PatriciaNode:
    def __init__(self):
        self.children: Dict[str, Tuple[str, 'PatriciaNode']] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None
    
    def get_memory_size(self) -> int:
        """ノードのメモリ使用量を推定（バイト）"""
        size = sys.getsizeof(self)
        size += sys.getsizeof(self.children)
        size += sys.getsizeof(self.is_end_of_word)
        size += sys.getsizeof(self.value)
        # エッジラベルのサイズ
        for key, (path, _) in self.children.items():
            size += sys.getsizeof(key)
            size += sys.getsizeof(path)  # パス文字列のサイズ
        return size

class PatriciaTree:
    """最適化されたPatricia Tree - パス圧縮"""
    def __init__(self):
        self.root = PatriciaNode()
    
    def insert(self, key: str, value: Any) -> None:
        self._insert_helper(self.root, key, value)
    
    def _insert_helper(self, node: PatriciaNode, remaining_key: str, value: Any) -> None:
        if not remaining_key:
            node.is_end_of_word = True
            node.value = value
            return
        
        first_char = remaining_key[0]
        
        if first_char in node.children:
            full_path, child = node.children[first_char]
            common_len = self._common_prefix_length(remaining_key, full_path)
            
            if common_len == len(full_path):
                self._insert_helper(child, remaining_key[common_len:], value)
            else:
                # パスを分割
                mid_node = PatriciaNode()
                
                old_remaining = full_path[common_len:]
                if old_remaining:
                    mid_node.children[old_remaining[0]] = (old_remaining, child)
                else:
                    mid_node.is_end_of_word = child.is_end_of_word
                    mid_node.value = child.value
                    mid_node.children = child.children
                
                node.children[first_char] = (full_path[:common_len], mid_node)
                
                new_remaining = remaining_key[common_len:]
                if new_remaining:
                    self._insert_helper(mid_node, new_remaining, value)
                else:
                    mid_node.is_end_of_word = True
                    mid_node.value = value
        else:
            # 新しいパスを作成（圧縮）
            new_node = PatriciaNode()
            new_node.is_end_of_word = True
            new_node.value = value
            node.children[first_char] = (remaining_key, new_node)
    
    def search(self, key: str) -> Optional[Any]:
        node = self.root
        
        while key:
            first_char = key[0]
            
            if first_char not in node.children:
                return None
            
            full_path, child = node.children[first_char]
            
            if key.startswith(full_path):
                node = child
                key = key[len(full_path):]
            else:
                return None
        
        return node.value if node.is_end_of_word else None
    
    def _common_prefix_length(self, s1: str, s2: str) -> int:
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def print_tree(self, node: Optional[PatriciaNode] = None, prefix: str = "", path: str = "") -> None:
        if node is None:
            node = self.root
            print("Root")
        
        if path:
            end_marker = " (*)" if node.is_end_of_word else ""
            value_str = f" [{node.value}]" if node.value is not None else ""
            print(f"{prefix}├── \"{path}\"{end_marker}{value_str}")
        
        sorted_children = sorted(node.children.items())
        for i, (first_char, (full_path, child)) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            next_prefix = prefix + ("    " if path == "" else ("│   " if not is_last else "    "))
            self.print_tree(child, next_prefix, full_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        def count_recursive(node, depth=0):
            count = 1
            depths = [depth]
            memory = node.get_memory_size()
            edge_lengths = []
            
            for _, (path, child) in node.children.items():
                edge_lengths.append(len(path))
                child_count, child_depths, child_memory, child_edges = count_recursive(child, depth + 1)
                count += child_count
                depths.extend(child_depths)
                memory += child_memory
                edge_lengths.extend(child_edges)
            
            return count, depths, memory, edge_lengths
        
        node_count, depths, total_memory, edge_lengths = count_recursive(self.root)
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        avg_edge_length = sum(edge_lengths) / len(edge_lengths) if edge_lengths else 0
        
        return {
            "node_count": node_count,
            "max_depth": max_depth,
            "avg_depth": avg_depth,
            "total_memory": total_memory,
            "avg_memory_per_node": total_memory / node_count if node_count > 0 else 0,
            "avg_edge_length": avg_edge_length
        }


# ===== 3. Merkle Patricia Tree（パス圧縮 + ハッシュ）=====
class MerklePatriciaNode:
    def __init__(self):
        self.children: Dict[str, Tuple[str, 'MerklePatriciaNode']] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None
        self.hash: Optional[str] = None
    
    def calculate_hash(self, force_recalculate: bool = False) -> str:
        """ノードのハッシュ値を計算"""
        if not force_recalculate and self.hash:
            return self.hash
            
        hasher = hashlib.sha256()
        
        if self.value is not None:
            hasher.update(str(self.value).encode())
        
        for first_char, (path, child) in sorted(self.children.items()):
            hasher.update(path.encode())
            child_hash = child.calculate_hash(force_recalculate)
            hasher.update(child_hash.encode())
        
        hasher.update(str(self.is_end_of_word).encode())
        
        self.hash = hasher.hexdigest()[:16]
        return self.hash
    
    def get_memory_size(self) -> int:
        """ノードのメモリ使用量を推定（バイト）"""
        size = sys.getsizeof(self)
        size += sys.getsizeof(self.children)
        size += sys.getsizeof(self.is_end_of_word)
        size += sys.getsizeof(self.value)
        size += sys.getsizeof(self.hash) if self.hash else 0
        
        for key, (path, _) in self.children.items():
            size += sys.getsizeof(key)
            size += sys.getsizeof(path)
        
        return size

class MerklePatriciaTree:
    """Merkle Patricia Tree - パス圧縮 + ハッシュ機能"""
    def __init__(self):
        self.root = MerklePatriciaNode()
    
    def insert(self, key: str, value: Any) -> None:
        self._insert_helper(self.root, key, value)
        self.root.calculate_hash(force_recalculate=True)
    
    def _insert_helper(self, node: MerklePatriciaNode, remaining_key: str, value: Any) -> None:
        if not remaining_key:
            node.is_end_of_word = True
            node.value = value
            return
        
        first_char = remaining_key[0]
        
        if first_char in node.children:
            full_path, child = node.children[first_char]
            common_len = self._common_prefix_length(remaining_key, full_path)
            
            if common_len == len(full_path):
                self._insert_helper(child, remaining_key[common_len:], value)
            else:
                mid_node = MerklePatriciaNode()
                
                old_remaining = full_path[common_len:]
                if old_remaining:
                    mid_node.children[old_remaining[0]] = (old_remaining, child)
                else:
                    mid_node.is_end_of_word = child.is_end_of_word
                    mid_node.value = child.value
                    mid_node.children = child.children
                
                node.children[first_char] = (full_path[:common_len], mid_node)
                
                new_remaining = remaining_key[common_len:]
                if new_remaining:
                    self._insert_helper(mid_node, new_remaining, value)
                else:
                    mid_node.is_end_of_word = True
                    mid_node.value = value
        else:
            new_node = MerklePatriciaNode()
            new_node.is_end_of_word = True
            new_node.value = value
            node.children[first_char] = (remaining_key, new_node)
    
    def search(self, key: str) -> Optional[Any]:
        node = self.root
        
        while key:
            first_char = key[0]
            
            if first_char not in node.children:
                return None
            
            full_path, child = node.children[first_char]
            
            if key.startswith(full_path):
                node = child
                key = key[len(full_path):]
            else:
                return None
        
        return node.value if node.is_end_of_word else None
    
    def verify_integrity(self) -> bool:
        """ルートハッシュを再計算して整合性を検証"""
        old_hash = self.root.hash
        new_hash = self.root.calculate_hash(force_recalculate=True)
        return old_hash == new_hash
    
    def _common_prefix_length(self, s1: str, s2: str) -> int:
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def print_tree(self, node: Optional[MerklePatriciaNode] = None, prefix: str = "", path: str = "") -> None:
        if node is None:
            node = self.root
            print(f"Root (hash: {node.hash})")
        
        if path:
            end_marker = " (*)" if node.is_end_of_word else ""
            value_str = f" [{node.value}]" if node.value is not None else ""
            hash_str = f" hash={node.hash}" if node.hash else ""
            print(f"{prefix}├── \"{path}\"{end_marker}{value_str}{hash_str}")
        
        sorted_children = sorted(node.children.items())
        for i, (first_char, (full_path, child)) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            next_prefix = prefix + ("    " if path == "" else ("│   " if not is_last else "    "))
            self.print_tree(child, next_prefix, full_path)
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        def count_recursive(node, depth=0):
            count = 1
            depths = [depth]
            memory = node.get_memory_size()
            edge_lengths = []
            
            for _, (path, child) in node.children.items():
                edge_lengths.append(len(path))
                child_count, child_depths, child_memory, child_edges = count_recursive(child, depth + 1)
                count += child_count
                depths.extend(child_depths)
                memory += child_memory
                edge_lengths.extend(child_edges)
            
            return count, depths, memory, edge_lengths
        
        node_count, depths, total_memory, edge_lengths = count_recursive(self.root)
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0
        avg_edge_length = sum(edge_lengths) / len(edge_lengths) if edge_lengths else 0
        
        return {
            "node_count": node_count,
            "max_depth": max_depth,
            "avg_depth": avg_depth,
            "total_memory": total_memory,
            "avg_memory_per_node": total_memory / node_count if node_count > 0 else 0,
            "avg_edge_length": avg_edge_length
        }


def visualize_memory_usage(stats_dict: Dict[str, Dict[str, Any]]):
    """メモリ使用量を視覚的に表示"""
    print("\n" + "="*80)
    print("メモリ使用量の視覚的比較")
    print("="*80)
    
    # メモリバーの最大幅
    max_bar_width = 50
    max_memory = max(stats['total_memory'] for stats in stats_dict.values())
    
    for tree_name, stats in stats_dict.items():
        memory = stats['total_memory']
        bar_width = int((memory / max_memory) * max_bar_width)
        bar = "█" * bar_width
        
        print(f"\n{tree_name}:")
        print(f"  メモリ: {bar} {memory:,} bytes")
        print(f"  ノード数: {stats['node_count']}")
        print(f"  平均メモリ/ノード: {stats['avg_memory_per_node']:.1f} bytes")
    
    # 相対比較
    print("\n相対比較（Basic Radix Treeを100%とした場合）:")
    basic_memory = stats_dict["Basic Radix Tree"]["total_memory"]
    for tree_name, stats in stats_dict.items():
        relative = (stats['total_memory'] / basic_memory) * 100
        print(f"  {tree_name}: {relative:.1f}%")


def create_comparison_table(stats_dict: Dict[str, Dict[str, Any]]):
    """比較表を作成"""
    print("\n" + "="*80)
    print("詳細比較表")
    print("="*80)
    
    # ヘッダー
    headers = ["指標", "Basic Radix", "Patricia", "Merkle Patricia"]
    col_widths = [20, 15, 15, 15]
    
    # ヘッダー行
    header_line = ""
    for header, width in zip(headers, col_widths):
        header_line += f"{header:<{width}}"
    print(header_line)
    print("-" * sum(col_widths))
    
    # データ行
    metrics = [
        ("ノード数", "node_count", "{:,}"),
        ("最大深さ", "max_depth", "{}"),
        ("平均深さ", "avg_depth", "{:.2f}"),
        ("総メモリ (bytes)", "total_memory", "{:,}"),
        ("メモリ/ノード", "avg_memory_per_node", "{:.1f}"),
    ]
    
    tree_names = ["Basic Radix Tree", "Patricia Tree", "Merkle Patricia Tree"]
    
    for metric_name, metric_key, format_str in metrics:
        row = f"{metric_name:<{col_widths[0]}}"
        for i, tree_name in enumerate(tree_names):
            if metric_key in stats_dict[tree_name]:
                value = stats_dict[tree_name][metric_key]
                formatted = format_str.format(value)
                row += f"{formatted:<{col_widths[i+1]}}"
            else:
                row += f"{'N/A':<{col_widths[i+1]}}"
        print(row)
    
    # Patricia/Merkleのみの指標
    if "avg_edge_length" in stats_dict["Patricia Tree"]:
        row = f"{'平均エッジ長':<{col_widths[0]}}"
        row += f"{'N/A':<{col_widths[1]}}"
        row += f"{stats_dict['Patricia Tree']['avg_edge_length']:.2f}".ljust(col_widths[2])
        row += f"{stats_dict['Merkle Patricia Tree']['avg_edge_length']:.2f}".ljust(col_widths[3])
        print(row)


def run_comprehensive_comparison():
    """包括的な比較を実行"""
    test_cases = [
        {
            "name": "ケース1: 共通プレフィックスが多い",
            "data": [
                ("test", 1),
                ("testing", 2),
                ("tester", 3),
                ("tested", 4),
                ("testimony", 5),
            ]
        },
        {
            "name": "ケース2: 長い単語",
            "data": [
                ("algorithm", 10),
                ("algorithmic", 20),
                ("algorithmically", 30),
                ("algebra", 40),
                ("algebraic", 50),
            ]
        },
        {
            "name": "ケース3: より現実的なケース",
            "data": [
                ("apple", 1),
                ("application", 2),
                ("apply", 3),
                ("banana", 4),
                ("band", 5),
                ("bandana", 6),
                ("can", 7),
                ("canada", 8),
                ("canadian", 9),
                ("cant", 10),
            ]
        }
    ]
    
    for test_case in test_cases:
        print("\n" + "="*80)
        print(f"{test_case['name']}")
        print("="*80)
        print(f"データ: {[item[0] for item in test_case['data']]}")
        
        # 各木を構築
        basic = TrueBasicRadixTree()
        patricia = PatriciaTree()
        merkle = MerklePatriciaTree()
        
        for key, value in test_case['data']:
            basic.insert(key, value)
            patricia.insert(key, value)
            merkle.insert(key, value)
        
        # 木構造を表示
        print("\n[1. Basic Radix Tree - 1文字ずつ]")
        basic.print_tree()
        
        print("\n[2. Patricia Tree - パス圧縮]")
        patricia.print_tree()
        
        print("\n[3. Merkle Patricia Tree - パス圧縮+ハッシュ]")
        merkle.print_tree()
        
        # 統計情報を収集
        stats = {
            "Basic Radix Tree": basic.get_stats(),
            "Patricia Tree": patricia.get_stats(),
            "Merkle Patricia Tree": merkle.get_stats()
        }
        
        # 視覚的な比較
        visualize_memory_usage(stats)
        create_comparison_table(stats)
        
        # 検索性能テスト
        print("\n検索性能テスト:")
        for key, expected in test_case['data'][:3]:  # 最初の3つだけテスト
            basic_result = basic.search(key)
            patricia_result = patricia.search(key)
            merkle_result = merkle.search(key)
            
            print(f"  '{key}': Basic={basic_result}, Patricia={patricia_result}, Merkle={merkle_result} (期待値: {expected})")


if __name__ == "__main__":
    run_comprehensive_comparison()