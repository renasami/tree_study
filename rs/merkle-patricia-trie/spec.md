# MPT SPEC

## 1. Core Structure

### 1.1. Node Types

#### Empty Node

- This node contains nothing
- In general, it is represented as None or null

#### Leaf Node

- Structure: `[path, value]`
- Represents the end of a key
- `path`: Remaining path (nibble array)
- `value`: The actual stored value

#### Extension Node

- Structure: `[path, next_node]`
- Compresses common prefixes
- `path`: Common path (nibble array)
- `next_node`: Reference to the next node

#### Branch Node

- Structure: `[v0, v1, ..., v15, value]`
- This type of node contains 17 elements
- `v0-v15`: Child nodes for each hex character (0-F)
- `value`: The value of this node itself (if it has one)

### 1.2. Path Encoding

```rust
struct CompactEncoding {
    // Hex Prefix (HP) encoding
    // First nibble indicates node type and path odd/even
}
```

- Features:

  - Efficiently encode odd-length paths
  - Represent node type (Leaf/Extension) with 1 bit
  - Represent whether path length is odd or even with 1 bit

- Encoding rules:
  - `0x0`: Extension node with even length
  - `0x1`: Extension node with odd length
  - `0x2`: Leaf node with even length
  - `0x3`: Leaf node with odd length

### 1.3. RLP (Recursive Length Prefix) Encoding

```rust
struct RLPEncoder {
    // Standard serialization pattern in Ethereum
}
```

- Features:
  - Encodes arbitrary nested byte arrays
  - Compact with clear boundary detection
  - No ambiguity when decoding

## 2. Main Structures and Features

### 2.1. TrieNode Structure

```rust
enum TrieNode {
    Empty,
    Leaf {
        path: NibblePath,
        value: Vec<u8>,
    },
    Extension {
        path: NibblePath,
        node: NodeReference,
    },
    Branch {
        branches: [Option<NodeReference>; 16],
        value: Option<Vec<u8>>,
    }
}
```

### 2.2. NodeReference Structure

```rust
enum NodeReference {
    Hash(H256),
    Inline(TrieNode),
}
```

- Features:
  - Insert directly when the node's data size is under 32 bytes
  - Reference with hash when the node's data size is over 32 bytes
  - Good balance between storage efficiency and access speed

### 2.3. TrieDB Structure

```rust
struct TrieDB {
    root: H256,                     // Root hash
    db: Box<dyn Database>,          // Persistence layer
    cache: HashMap<H256, TrieNode>, // Memory cache
}
```

## 3. Core Functionality

### 3.1. Basic Operations

**Insert**

```rust
fn insert(&mut self, key: &[u8], value: &[u8]) -> Result<(), Error>
```

- Convert keys to nibbles
- Select and insert the appropriate node type
- Split and join nodes as needed

**Get**

```rust
fn get(&self, key: &[u8]) -> Result<Option<Vec<u8>>, Error>
```

- Follow a path to find a value
- Resolve hash references

**Remove**

```rust
fn remove(&mut self, key: &[u8]) -> Result<Option<Vec<u8>>, Error>
```

- Delete node
- Join nodes as needed (optimization)

### 3.2. Merkle Features

**Root Hash**

```rust
fn root_hash(&self) -> H256
```

- A 32-byte hash representing the state of the entire trie
- Enables efficient validation of state changes

**Merkle Proof**

```rust
struct MerkleProof {
    path: Vec<ProofNode>, // Path to root
}

fn generate_proof(&self, key: &[u8]) -> Result<MerkleProof, Error>
fn verify_proof(root: H256, key: &[u8], value: &[u8], proof: &MerkleProof) -> bool
```

### 3.3. Persistence and Caching

```rust
trait Database {
    fn get(&self, key: &H256) -> Result<Option<Vec<u8>>, Error>;
    fn put(&mut self, key: H256, value: Vec<u8>) -> Result<(), Error>;
}

struct CachedDB {
    underlying: Box<dyn Database>,
    cache: LruCache<H256, Vec<u8>>,
    write_batch: HashMap<H256, Vec<u8>>,
}
```

## 4. Ethereum-Specific Requirements

### 4.1. State Trie

```rust
struct StateAccount {
    nonce: u64,
    balance: U256,
    storage_root: H256,
    code_hash: H256,
}
```

### 4.2. Storage Trie

- Every account has its own storage trie
- Key: 32-byte storage position
- Value: 32-byte storage value

### 4.3. Transaction Trie

- Stores transactions in a block
- Key: Transaction index (RLP encoded)
- Value: Transaction data

### 4.4. Receipt Trie

- Stores transaction execution results
- Key: Transaction index
- Value: Receipt data (e.g., gas used, logs, etc.)

## 5. Optimization Features

### 5.1. Compressed Patricia Merkle Tree

```rust
struct CompressedPath {
    nibbles: Vec<u8>,
}
```

### 5.2. Reference Counting

```rust
struct RefCountedNode {
    node: TrieNode,
    ref_count: u32,
}
```

### 5.3. Snapshots

```rust
struct TrieSnapshot {
    root: H256,
    timestamp: u64,
}
```

## 6. Security Features

### 6.1. Hash Integrity

- All nodes are hashed with Keccak-256
- Hash chaining prevents tampering

### 6.2. DoS Attack Countermeasures

- Depth limits
- Appropriate gas cost settings
- Memory usage limits
