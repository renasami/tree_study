import hashlib
from typing import Dict, Optional, List, Tuple, Any

# ===== 1. Basic Radix Tree =====
class BasicRadixNode:
    """Basic Radix Treeのノード"""
    def __init__(self):
        self.children: Dict[str, 'BasicRadixNode'] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None

class BasicRadixTree:
    """基本的なRadix Treeの実装"""
    def __init__(self, show_steps: bool = False):
        self.root = BasicRadixNode()
        self.show_steps = show_steps
        self.insertion_count = 0
    
    def insert(self, key: str, value: Any) -> None:
        """基本的なRadix Treeへの挿入"""
        if not key:
            raise ValueError("Key cannot be empty")
        
        self.insertion_count += 1
        print(f"\n{'='*60}")
        print(f"[Basic Radix] Insertion #{self.insertion_count}: {key} -> {value}")
        print(f"{'='*60}")
        
        node = self.root
        original_key = key
        path = []
        
        while key:
            found = False
            for edge_label, child in node.children.items():
                # 共通接頭辞を見つける
                common_len = self._common_prefix_length(key, edge_label)
                
                if common_len > 0:
                    print(f"  Found common prefix: '{edge_label[:common_len]}' with edge '{edge_label}'")
                    
                    if common_len == len(edge_label):
                        # エッジラベル全体が一致
                        path.append(edge_label)
                        node = child
                        key = key[common_len:]
                        found = True
                        break
                    else:
                        # エッジを分割する必要がある
                        print(f"  Splitting edge '{edge_label}' at position {common_len}")
                        print(f"    - Common part: '{edge_label[:common_len]}'")
                        print(f"    - Remaining old: '{edge_label[common_len:]}'")
                        print(f"    - Remaining new: '{key[common_len:]}'")
                        
                        # 新しい中間ノード
                        mid_node = BasicRadixNode()
                        
                        # 既存の子ノードを付け替え
                        remaining_label = edge_label[common_len:]
                        mid_node.children[remaining_label] = child
                        
                        # 親ノードの子を更新
                        del node.children[edge_label]
                        node.children[edge_label[:common_len]] = mid_node
                        
                        path.append(edge_label[:common_len])
                        node = mid_node
                        key = key[common_len:]
                        found = True
                        break
            
            if not found:
                # 新しいエッジを作成
                print(f"  Creating new edge with label: '{key}'")
                new_node = BasicRadixNode()
                node.children[key] = new_node
                path.append(key)
                node = new_node
                key = ""
        
        node.is_end_of_word = True
        node.value = value
        print(f"  Marked node as end of word with value: {value}")
        print(f"  Full path: {' -> '.join(path) if path else '(root)'}")
        
        if self.show_steps:
            print(f"\n[Tree structure after inserting '{original_key}']")
            self.print_tree(show_internal_nodes=True)
    
    def search(self, key: str) -> Optional[Any]:
        """キーに対応する値を検索"""
        if not key:
            return None
            
        node = self.root
        
        while key:
            found = False
            for edge_label, child in node.children.items():
                common_len = self._common_prefix_length(key, edge_label)
                
                if common_len == len(edge_label):
                    # エッジラベル全体が一致
                    node = child
                    key = key[common_len:]
                    found = True
                    break
                elif common_len == len(key) and common_len < len(edge_label):
                    # キーが途中で終わる場合
                    return None
            
            if not found:
                return None
        
        return node.value if node.is_end_of_word else None
    
    def _common_prefix_length(self, s1: str, s2: str) -> int:
        """2つの文字列の共通接頭辞の長さを返す"""
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def print_tree(self, node: Optional[BasicRadixNode] = None, prefix: str = "", edge_label: str = "", 
                   show_internal_nodes: bool = False) -> None:
        """木構造を視覚的に出力"""
        if node is None:
            node = self.root
            print("Root")
        
        if edge_label:
            end_marker = " (*)" if node.is_end_of_word else ""
            value_str = f" [{node.value}]" if node.value is not None else ""
            node_type = " [LEAF]" if not node.children else " [INTERNAL]" if show_internal_nodes else ""
            print(f"{prefix}├── {edge_label}{end_marker}{value_str}{node_type}")
        
        sorted_children = sorted(node.children.items())
        for i, (label, child) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            next_prefix = prefix + ("    " if edge_label == "" else ("│   " if not is_last else "    "))
            self.print_tree(child, next_prefix, label, show_internal_nodes)


# ===== 2. Optimized Patricia Tree (Path Compressed) =====
class PatriciaNode:
    """Patricia Treeのノード"""
    def __init__(self):
        self.children: Dict[str, Tuple[str, 'PatriciaNode']] = {}  # key -> (full_path, node)
        self.is_end_of_word = False
        self.value: Optional[Any] = None

class PatriciaTree:
    """パス圧縮されたPatricia Treeの実装"""
    def __init__(self, show_steps: bool = False):
        self.root = PatriciaNode()
        self.show_steps = show_steps
        self.insertion_count = 0
    
    def insert(self, key: str, value: Any) -> None:
        """パス圧縮されたPatricia Treeへの挿入"""
        if not key:
            raise ValueError("Key cannot be empty")
        
        self.insertion_count += 1
        print(f"\n{'='*60}")
        print(f"[Patricia Tree] Insertion #{self.insertion_count}: {key} -> {value}")
        print(f"{'='*60}")
        
        self._insert_helper(self.root, key, value, "")
        
        if self.show_steps:
            print(f"\n[Tree structure after inserting '{key}']")
            self.print_tree(show_internal_nodes=True)
    
    def _insert_helper(self, node: PatriciaNode, remaining_key: str, value: Any, path_so_far: str) -> None:
        if not remaining_key:
            node.is_end_of_word = True
            node.value = value
            print(f"  Reached end of key at path: '{path_so_far}'")
            return
        
        first_char = remaining_key[0]
        
        if first_char in node.children:
            full_path, child = node.children[first_char]
            common_len = self._common_prefix_length(remaining_key, full_path)
            
            print(f"  Found edge starting with '{first_char}', full path: '{full_path}'")
            print(f"  Common prefix length: {common_len}")
            print(f"    - Remaining key: '{remaining_key}'")
            print(f"    - Common part: '{remaining_key[:common_len]}'")
            
            if common_len == len(full_path):
                # 完全一致 - 子ノードに進む
                print(f"  Full match - proceeding to child node")
                self._insert_helper(child, remaining_key[common_len:], value, path_so_far + full_path)
            else:
                # パスを分割する必要がある
                print(f"  Splitting path '{full_path}' at position {common_len}")
                print(f"    - Common prefix: '{full_path[:common_len]}'")
                print(f"    - Old remaining: '{full_path[common_len:]}'")
                print(f"    - New remaining: '{remaining_key[common_len:]}'")
                
                # 新しい中間ノード
                mid_node = PatriciaNode()
                
                # 既存の子ノードを付け替え
                old_remaining = full_path[common_len:]
                if old_remaining:
                    mid_node.children[old_remaining[0]] = (old_remaining, child)
                else:
                    # 既存のノードの内容を中間ノードにコピー
                    mid_node.is_end_of_word = child.is_end_of_word
                    mid_node.value = child.value
                    mid_node.children = child.children
                
                # 親ノードの参照を更新
                node.children[first_char] = (full_path[:common_len], mid_node)
                
                # 新しいキーの残りを処理
                new_remaining = remaining_key[common_len:]
                if new_remaining:
                    self._insert_helper(mid_node, new_remaining, value, path_so_far + full_path[:common_len])
                else:
                    mid_node.is_end_of_word = True
                    mid_node.value = value
        else:
            # 新しいパスを作成
            print(f"  Creating new path: '{remaining_key}'")
            new_node = PatriciaNode()
            new_node.is_end_of_word = True
            new_node.value = value
            node.children[first_char] = (remaining_key, new_node)
    
    def search(self, key: str) -> Optional[Any]:
        """キーに対応する値を検索"""
        if not key:
            return None
            
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
        """2つの文字列の共通接頭辞の長さを返す"""
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def print_tree(self, node: Optional[PatriciaNode] = None, prefix: str = "", path: str = "",
                   show_internal_nodes: bool = False) -> None:
        """木構造を視覚的に出力"""
        if node is None:
            node = self.root
            print("Root")
        
        if path:
            end_marker = " (*)" if node.is_end_of_word else ""
            value_str = f" [{node.value}]" if node.value is not None else ""
            node_type = " [LEAF]" if not node.children else " [INTERNAL]" if show_internal_nodes else ""
            child_count = f" (children: {len(node.children)})" if show_internal_nodes and node.children else ""
            print(f"{prefix}├── {path}{end_marker}{value_str}{node_type}{child_count}")
        
        sorted_children = sorted(node.children.items())
        for i, (first_char, (full_path, child)) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            next_prefix = prefix + ("    " if path == "" else ("│   " if not is_last else "    "))
            self.print_tree(child, next_prefix, full_path, show_internal_nodes)


# ===== 3. Merkle Patricia Tree =====
class MerklePatriciaNode:
    """Merkle Patricia Treeのノード"""
    def __init__(self):
        self.children: Dict[str, Tuple[str, 'MerklePatriciaNode']] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None
        self.hash: Optional[str] = None
    
    def calculate_hash(self, force_recalculate: bool = False) -> str:
        """ノードのハッシュ値を計算"""
        hasher = hashlib.sha256()
        
        # 値のハッシュ
        if self.value is not None:
            hasher.update(str(self.value).encode())
        
        # 子ノードのハッシュを含める
        for first_char, (path, child) in sorted(self.children.items()):
            hasher.update(path.encode())
            if force_recalculate or child.hash is None:
                child.calculate_hash(force_recalculate)
            if child.hash:
                hasher.update(child.hash.encode())
        
        # 終端フラグ
        hasher.update(str(self.is_end_of_word).encode())
        
        self.hash = hasher.hexdigest()[:16]  # 表示用に短縮
        return self.hash

class MerklePatriciaTree:
    """Merkle Patricia Treeの実装（ハッシュ機能付き）"""
    def __init__(self, show_steps: bool = False):
        self.root = MerklePatriciaNode()
        self.show_steps = show_steps
        self.insertion_count = 0
    
    def insert(self, key: str, value: Any) -> None:
        """Merkle Patricia Treeへの挿入"""
        if not key:
            raise ValueError("Key cannot be empty")
        
        self.insertion_count += 1
        print(f"\n{'='*60}")
        print(f"[Merkle Patricia] Insertion #{self.insertion_count}: {key} -> {value}")
        print(f"{'='*60}")
        
        self._insert_helper(self.root, key, value, "")
        
        # ハッシュを再計算
        print("\n  Recalculating hashes...")
        old_hash = self.root.hash
        new_hash = self.root.calculate_hash(force_recalculate=True)
        print(f"  Root hash changed: {old_hash} -> {new_hash}")
        
        if self.show_steps:
            print(f"\n[Tree structure after inserting '{key}']")
            self.print_tree(show_internal_nodes=True)
    
    def _insert_helper(self, node: MerklePatriciaNode, remaining_key: str, value: Any, path_so_far: str) -> None:
        if not remaining_key:
            node.is_end_of_word = True
            node.value = value
            print(f"  Reached end of key at path: '{path_so_far}'")
            return
        
        first_char = remaining_key[0]
        
        if first_char in node.children:
            full_path, child = node.children[first_char]
            common_len = self._common_prefix_length(remaining_key, full_path)
            
            print(f"  Found edge starting with '{first_char}', full path: '{full_path}'")
            
            if common_len == len(full_path):
                self._insert_helper(child, remaining_key[common_len:], value, path_so_far + full_path)
            else:
                print(f"  Splitting path '{full_path}' at position {common_len}")
                
                mid_node = MerklePatriciaNode()
                
                old_remaining = full_path[common_len:]
                if old_remaining:
                    mid_node.children[old_remaining[0]] = (old_remaining, child)
                else:
                    # 既存のノードの内容を中間ノードにコピー
                    mid_node.is_end_of_word = child.is_end_of_word
                    mid_node.value = child.value
                    mid_node.children = child.children
                
                node.children[first_char] = (full_path[:common_len], mid_node)
                
                new_remaining = remaining_key[common_len:]
                if new_remaining:
                    self._insert_helper(mid_node, new_remaining, value, path_so_far + full_path[:common_len])
                else:
                    mid_node.is_end_of_word = True
                    mid_node.value = value
        else:
            print(f"  Creating new path: '{remaining_key}'")
            new_node = MerklePatriciaNode()
            new_node.is_end_of_word = True
            new_node.value = value
            node.children[first_char] = (remaining_key, new_node)
    
    def search(self, key: str) -> Optional[Any]:
        """キーに対応する値を検索"""
        if not key:
            return None
            
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
        """2つの文字列の共通接頭辞の長さを返す"""
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def print_tree(self, node: Optional[MerklePatriciaNode] = None, prefix: str = "", path: str = "",
                   show_internal_nodes: bool = False) -> None:
        """木構造を視覚的に出力"""
        if node is None:
            node = self.root
            print(f"Root (hash: {node.hash})")
        
        if path:
            end_marker = " (*)" if node.is_end_of_word else ""
            value_str = f" [{node.value}]" if node.value is not None else ""
            hash_str = f" hash={node.hash}" if node.hash else ""
            node_type = " [LEAF]" if not node.children else " [INTERNAL]" if show_internal_nodes else ""
            print(f"{prefix}├── {path}{end_marker}{value_str}{hash_str}{node_type}")
        
        sorted_children = sorted(node.children.items())
        for i, (first_char, (full_path, child)) in enumerate(sorted_children):
            is_last = i == len(sorted_children) - 1
            next_prefix = prefix + ("    " if path == "" else ("│   " if not is_last else "    "))
            self.print_tree(child, next_prefix, full_path, show_internal_nodes)
    
    def verify_integrity(self) -> bool:
        """ルートハッシュを再計算して整合性を検証"""
        old_hash = self.root.hash
        new_hash = self.root.calculate_hash(force_recalculate=True)
        
        print(f"\n[Integrity Check]")
        print(f"  Stored root hash:     {old_hash}")
        print(f"  Calculated root hash: {new_hash}")
        print(f"  Integrity: {'VALID' if old_hash == new_hash else 'INVALID'}")
        
        return old_hash == new_hash


# ===== インタラクティブデモ =====
def interactive_demo():
    """インタラクティブなデモンストレーション"""
    test_data = [
        ("cat", 100),
        ("cats", 200),
        ("dog", 300),
        ("dodge", 400),
        ("door", 500),
    ]
    
    while True:
        print("\n" + "="*60)
        print("Radix Tree Demonstrations")
        print("="*60)
        print("1. Basic Radix Tree")
        print("2. Patricia Tree (Path Compressed)")
        print("3. Merkle Patricia Tree (with Hashing)")
        print("4. Compare all trees (without step-by-step)")
        print("0. Exit")
        print("-"*60)
        
        choice = input("Select an option (0-4): ").strip()
        
        if choice == "0":
            print("Exiting...")
            break
            
        show_steps = False
        if choice in ["1", "2", "3"]:
            step_choice = input("Show step-by-step tree construction? (y/n): ").strip().lower()
            show_steps = step_choice == 'y'
        
        if choice == "1":
            print("\n" + "="*60)
            print("BASIC RADIX TREE DEMONSTRATION")
            print("="*60)
            
            radix = BasicRadixTree(show_steps=show_steps)
            for key, value in test_data:
                radix.insert(key, value)
            
            print("\n[Final Basic Radix Tree Structure]")
            radix.print_tree(show_internal_nodes=True)
            
            # 検索テスト
            print("\n[Search Test]")
            for key, expected_value in test_data:
                found_value = radix.search(key)
                status = "✓" if found_value == expected_value else "✗"
                print(f"  {status} Search '{key}': {found_value} (expected: {expected_value})")
                
        elif choice == "2":
            print("\n" + "="*60)
            print("PATRICIA TREE DEMONSTRATION")
            print("="*60)
            
            patricia = PatriciaTree(show_steps=show_steps)
            for key, value in test_data:
                patricia.insert(key, value)
            
            print("\n[Final Patricia Tree Structure]")
            patricia.print_tree(show_internal_nodes=True)
            
            # 検索テスト
            print("\n[Search Test]")
            for key, expected_value in test_data:
                found_value = patricia.search(key)
                status = "✓" if found_value == expected_value else "✗"
                print(f"  {status} Search '{key}': {found_value} (expected: {expected_value})")
                
        elif choice == "3":
            print("\n" + "="*60)
            print("MERKLE PATRICIA TREE DEMONSTRATION")
            print("="*60)
            
            merkle = MerklePatriciaTree(show_steps=show_steps)
            for key, value in test_data:
                merkle.insert(key, value)
            
            print("\n[Final Merkle Patricia Tree Structure]")
            merkle.print_tree(show_internal_nodes=True)
            
            # 検索テスト
            print("\n[Search Test]")
            for key, expected_value in test_data:
                found_value = merkle.search(key)
                status = "✓" if found_value == expected_value else "✗"
                print(f"  {status} Search '{key}': {found_value} (expected: {expected_value})")
            
            # 整合性チェック
            merkle.verify_integrity()
            
            # データ改変シミュレーション
            corrupt_choice = input("\nSimulate data corruption? (y/n): ").strip().lower()
            if corrupt_choice == 'y':
                print("\n[Simulating Data Corruption]")
                if merkle.root.children:
                    if 'c' in merkle.root.children:
                        _, cat_node = merkle.root.children['c']
                        for _, (_, child) in cat_node.children.items():
                            if child.value is not None:
                                old_value = child.value
                                old_hash = child.hash
                                child.value += 1000
                                print(f"  Changing value from {old_value} to {child.value}")
                                print(f"  Node hash remains: {old_hash}")
                                break
                
                merkle.verify_integrity()
                
        elif choice == "4":
            print("\n" + "="*60)
            print("COMPARING ALL TREE STRUCTURES")
            print("="*60)
            
            # 各木を構築
            radix = BasicRadixTree(show_steps=False)
            patricia = PatriciaTree(show_steps=False)
            merkle = MerklePatriciaTree(show_steps=False)
            
            for key, value in test_data:
                radix.insert(key, value)
                patricia.insert(key, value)
                merkle.insert(key, value)
            
            print("\n[1. Basic Radix Tree]")
            radix.print_tree()
            
            print("\n[2. Patricia Tree]")
            patricia.print_tree()
            
            print("\n[3. Merkle Patricia Tree]")
            merkle.print_tree()
            
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    # インタラクティブモードで実行
    interactive_demo()