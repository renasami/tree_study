from typing import Dict, Optional, Any

# ===== 真のBasic Radix Tree（1文字ずつ処理）=====
class TrueBasicRadixNode:
    def __init__(self):
        self.children: Dict[str, 'TrueBasicRadixNode'] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None

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


# ===== Patricia Tree（パス圧縮あり）=====
class OptimizedPatriciaNode:
    def __init__(self):
        self.children: Dict[str, tuple[str, 'OptimizedPatriciaNode']] = {}
        self.is_end_of_word = False
        self.value: Optional[Any] = None

class OptimizedPatriciaTree:
    """最適化されたPatricia Tree - パス圧縮"""
    def __init__(self):
        self.root = OptimizedPatriciaNode()
    
    def insert(self, key: str, value: Any) -> None:
        self._insert_helper(self.root, key, value)
    
    def _insert_helper(self, node: OptimizedPatriciaNode, remaining_key: str, value: Any) -> None:
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
                mid_node = OptimizedPatriciaNode()
                
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
            new_node = OptimizedPatriciaNode()
            new_node.is_end_of_word = True
            new_node.value = value
            node.children[first_char] = (remaining_key, new_node)
    
    def _common_prefix_length(self, s1: str, s2: str) -> int:
        i = 0
        while i < len(s1) and i < len(s2) and s1[i] == s2[i]:
            i += 1
        return i
    
    def print_tree(self, node: Optional[OptimizedPatriciaNode] = None, prefix: str = "", path: str = "") -> None:
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


def demonstrate_differences():
    """違いを明確に示すデモンストレーション"""
    
    # より違いが分かりやすいテストデータ
    test_cases = [
        {
            "name": "ケース1: 共通プレフィックスが多い場合",
            "data": [
                ("test", 1),
                ("testing", 2),
                ("tester", 3),
                ("tested", 4),
            ]
        },
        {
            "name": "ケース2: 長い共通部分を持つ場合",
            "data": [
                ("algorithm", 10),
                ("algorithmic", 20),
                ("algebra", 30),
                ("all", 40),
            ]
        },
        {
            "name": "ケース3: 元のテストケース",
            "data": [
                ("cat", 100),
                ("cats", 200),
                ("dog", 300),
                ("dodge", 400),
                ("door", 500),
            ]
        }
    ]
    
    for test_case in test_cases:
        print("\n" + "="*70)
        print(f"{test_case['name']}")
        print("="*70)
        print(f"データ: {[item[0] for item in test_case['data']]}")
        
        # Basic Radix Tree（1文字ずつ）
        print("\n[True Basic Radix Tree - 1文字ずつのエッジ]")
        basic = TrueBasicRadixTree()
        for key, value in test_case['data']:
            basic.insert(key, value)
        basic.print_tree()
        
        # Patricia Tree（パス圧縮）
        print("\n[Patricia Tree - パス圧縮あり]")
        patricia = OptimizedPatriciaTree()
        for key, value in test_case['data']:
            patricia.insert(key, value)
        patricia.print_tree()
        
        # ノード数の比較
        basic_nodes = count_nodes(basic.root)
        patricia_nodes = count_patricia_nodes(patricia.root)
        print(f"\nノード数の比較:")
        print(f"  Basic Radix Tree: {basic_nodes} ノード")
        print(f"  Patricia Tree: {patricia_nodes} ノード")
        print(f"  圧縮率: {((basic_nodes - patricia_nodes) / basic_nodes * 100):.1f}%")


def count_nodes(node: TrueBasicRadixNode) -> int:
    """Basic Radix Treeのノード数をカウント"""
    count = 1  # 現在のノード
    for child in node.children.values():
        count += count_nodes(child)
    return count


def count_patricia_nodes(node: OptimizedPatriciaNode) -> int:
    """Patricia Treeのノード数をカウント"""
    count = 1  # 現在のノード
    for _, child in node.children.values():
        count += count_patricia_nodes(child)
    return count


def visualize_memory_usage():
    """メモリ使用量の概念的な比較"""
    print("\n" + "="*70)
    print("メモリ使用量の概念的比較")
    print("="*70)
    
    word = "testing"
    
    print(f"\n単語 '{word}' を格納する場合:")
    
    print("\n[Basic Radix Tree]")
    print("必要なノード:")
    for i, char in enumerate(word):
        print(f"  レベル {i+1}: '{char}' のためのノード")
    print(f"合計: {len(word)} ノード必要")
    
    print("\n[Patricia Tree]")
    print("必要なノード:")
    print(f"  レベル 1: 'testing' 全体を1つのエッジに圧縮")
    print(f"合計: 1 ノード必要")
    
    print("\n[結論]")
    print("Patricia Treeは単一の子しか持たないノードを圧縮することで、")
    print("メモリ使用量を大幅に削減します。")


if __name__ == "__main__":
    demonstrate_differences()
    visualize_memory_usage()