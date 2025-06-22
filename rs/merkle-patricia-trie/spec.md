# MPC SPEC

## 1. core structure

### 1-1. Node Type

#### Leaf Node

- thie node contains nothing
- In general, it is explained as None or null

#### Leaf Node

- structure: `[path, value]`
- it express the end of key
- `path` : remaining pathes (nibble array)
- `value` : the value that is stored actually

#### Extension Node

- structure: `[path, next_node]`
- it compress common prefix
- `path` : common path (nibble array)
- `next_node` : next node's reference

#### Branch Node

- structure: ``[v0, v1 ..., v15, value]
- this type of node contains 17 element
- `v0-v15`: child nodes for each hex character
- `value`: the value of this node itself if it has a value

### 1-2. Path Encoding

```rust
struct ComactEncoding {
    // Hex Prefix (HP) encoding
    // First nibble indicates node type and path odd/even
}
```

- Features

  - efficiently encode odd-length paths
  - represent node type (Leaf/Extension) with 1 bit
  - represent whether path length is odd or even with 1 bit

- rule of encoding
  - `0x0` : extension node and even length
  - `0x1` : extension node and odd length
  - `0x2` : reaf node and even length
  - `0x3` : reaf node and odd length

### 1-3. RLP (Recursive Length Prefix) Encoding

```rust
struct RLPEncoder {
    // Etandard serialize pattern in etherium
}
```

- Features
  - Encodes arbitrary nested byte arrays
  - Compact and easy to understand boundaries
  - No resolution when decoding

## 2. Main Struct And Features

### 2.1 TrieNode Structure

```rust
enum TrieNode {
    Empty,
    Leaf {
        path: NibblePath,
        value: Vec<u8>
    },
    Extension {
        path: NibblePath,
        node: NodeReference,
    },
    Branch {
        branches: [Option<NodeReference>; 16]m
        value: Option<Vec<u8>>,
    }
}
```

### 2.2 NoodeReference Structure

```rust
enume NodeReference {
    Hash(H256),
    Inline(TrieNode)
}
```

- Features
  -
