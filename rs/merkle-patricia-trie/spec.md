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
enum NodeReference {
    Hash(H256),
    Inline(TrieNode)
}
```

- ## Features
  - insert directry when the node's data size under 32 bites
  - reference with hash when the node's data size over 32 bites
  - the good balance between strage efficiency and accecc speed

### 2.3 TrieDB Structure

```rust
struct TrieDB {
    root: H256,                     // root hash
    db: Box<dyn Database>,          // perciste rayer
    cache: HashMap<H256, TrieNode>, // memory cache
}
```

## 3. Neccesary Features

### 3.1 basic operation

**Insert**

```rust
fn insert(&mut self, key: &[u8], value: &[u8]) -> Result<(), Error>
```

- convert keys to nibbles
- select and insert the appropriate node type
- split and join nodes as needed

**Get**

```rust
fn get(&self, key: &[u8]) -> Result<Option<Vec<u8>>, Error>
```

- follow a path to find a value
- resolve a hash reference

**Remove**

```rust
fn remove(&mut self, key: &[u8]) -> Result<Option<Vec<u8>, Error>
```

- delete node
- join node as needed (Optimize)

### 3.2 Markle

**Root Hash**

```rust
fn root_hash(&self) -> H256
```

- a 32-byte hash representing the state of the entire trie,
- efficiently validating state changes

**Markle Proof**

```rust
struct MarkleProof {
    path: Vec<ProofNode>, // path to root
}

fn generate_proof(&self, key: &[u8]) -> Result<MarkleProof, Error>
fn verify_proor(root: H256, key: &[u8], value: &[u8], proof: &MarkleProof) -> bool
```

### 3.3 Persistence and Caching

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

## 4. specific requirement of etherium

### 4.1. State Trie

```rust
struct StateAccount {
    nonce: u64,
    banlance: U256,
    storage_root: H256,
    code_hash: H256
}
```

### 4.2 Storage Trie

- every accounts have storage trie
- key: 32 bites storage position
- value: 32 bites storage value

### 4.3 Transaction Trie

- stores transactions in a block
- key: transaction index (RLP encoded)
- value: transaction data

### 4.4 Receipt Trie

- store transaction execution data
- key: transaction index
- value recipiet data (ex, usage amout of gas, logs etc...)

## 5. Optimization Feature

### 5.1 compress patricia marcle tree

```rust
struct CompressedPath {
    nibbles: Vec<u8>,
}
```

### 5.2 reference count

```rust
struct RefCountedNode {
    node: TrieNode,
    ref_count: u32
}
```

### 5.3 snapshot

```rust
struct TrieSnapshot {
    root: H256,
    timestamp: u64
}
```

## 6. Security Features

### 6.1 Hash integrity

- all nodes are hashed with Keccak-256
- hash chaining prevents tampering

### 6.2 DoS attack countermeasures

- depth limit
- appropriate gas cost setting
- memory usage limit
