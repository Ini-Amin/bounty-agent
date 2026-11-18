# QUANTUM MODE — POST-QUANTUM CRYPTOGRAPHY & QUANTUM ATTACKS
# 10 CATEGORIES | 250+ TECHNIQUES
# TRIGGERS: quantum, post-quantum, lattice, shor, grover, kyber, dilithium, rainbow, hash-based, code-based

---

## Section 1: QUANTUM CRYPTOGRAPHY FUNDAMENTALS (30+ concepts)

### 1.1 Quantum Computing Basics
- Qubit vs classical bit
- Superposition (|0⟩ + |1⟩)
- Entanglement (Bell states)
- Quantum gates (Hadamard, CNOT, Toffoli)
- Quantum circuits
- Quantum parallelism
- Decoherence and error correction
- NISQ (Noisy Intermediate-Scale Quantum) era
- Fault-tolerant quantum computing
- Quantum supremacy/advantage

### 1.2 Quantum Algorithms
- Shor's algorithm (integer factorization — breaks RSA)
- Shor's algorithm (discrete logarithm — breaks ECC/DH)
- Grover's algorithm (quadratic speedup for search — weakens AES)
- Quantum phase estimation
- HHL algorithm (linear systems)
- Quantum walk algorithms
- Variational Quantum Eigensolver (VQE)
- Quantum Approximate Optimization Algorithm (QAOA)
- Deutsch-Jozsa algorithm
- Simon's algorithm

### 1.3 Quantum Threat Timeline
- "Harvest now, decrypt later" attacks
- Current quantum computer capabilities (IBM, Google, IonQ, Rigetti)
- Timeline to cryptographically relevant quantum computer (CRQC)
- NIST post-quantum standardization timeline
- Risk assessment for current cryptographic systems
- Migration planning frameworks

---

## Section 2: POST-QUANTUM ALGORITHMS (40+ techniques)

### 2.1 Lattice-Based Cryptography
- CRYSTALS-Kyber (KEM — NIST standard)
- CRYSTALS-Dilithium (digital signature — NIST standard)
- FALCON (digital signature — NIST standard)
- NTRU (lattice-based encryption)
- NTRU-HRSS (variant)
- NewHope (key exchange)
- FrodoKEM (lattice KEM)
- SABER (lattice KEM)
- CRYSTALS-Kyber-512/768/1024 (parameter sets)
- CRYSTALS-Dilithium-2/3/5 (parameter sets)
- FALCON-512/1024 (parameter sets)
- Lattice-based homomorphic encryption (BFV, CKKS, BGV)
- Lattice-based zero-knowledge proofs
- Lattice-based attribute-based encryption
- Lattice-based functional encryption

### 2.2 Hash-Based Cryptography
- SPHINCS+ (stateless hash-based signature — NIST standard)
- XMSS (eXtended Merkle Signature Scheme)
- LMS (Leighton-Micali Signature)
- Merkle signature scheme
- Hash-based key exchange
- Hash-based commitment schemes
- WOTS+ (Winternitz One-Time Signature)
- Merkle tree construction and verification
- Merkle tree authentication paths
- Post-quantum HMAC

### 2.3 Code-Based Cryptography
- Classic McEliece (NIST standard — code-based KEM)
- BIKE (Bit-flipping Key Encapsulation)
- HQC (Hamming Quasi-Cyclic)
- McEliece encryption/decryption
- Niederreiter cryptosystem
- Code-based signature schemes
- Goppa code construction
- Syndrome decoding problem
- Code-based zero-knowledge proofs

### 2.4 Other Post-Quantum
- SIKE/SIDH (isogeny-based — broken in 2022)
- CSIDH (commutative SIDH)
- Supersingular isogeny key exchange
- Multivariate cryptography (Rainbow — broken in 2022)
- Geometric cryptography
- Supersingular graph-based cryptography
- Post-quantum TLS 1.3
- Post-quantum SSH
- Post-quantum VPN (WireGuard post-quantum)
- Post-quantum Signal protocol (PQXDH)

---

## Section 3: SHOR'S ALGORITHM ATTACKS (35+ techniques)

### 3.1 RSA Attacks via Shor's
- RSA-2048 factorization (future CRQC)
- RSA-4096 factorization
- RSA key generation analysis
- RSA small exponent attacks (with Shor's)
- RSA multi-prime attacks
- RSA CRT attacks
- RSA timing attacks (post-quantum)
- RSA fault attacks (post-quantum)
- RSA side-channel attacks (post-quantum)
- RSA padding oracle (post-quantum)

### 3.2 ECC Attacks via Shor's
- ECDLP (Elliptic Curve Discrete Log Problem) solution
- P-256 key recovery
- P-384 key recovery
- Ed25519 key recovery
- Curve25519 key recovery
- Brainpool key recovery
- SECP key recovery
- ECDSA signature forgery (post-quantum)
- ECDH key recovery
- ECIES decryption (post-quantum)

### 3.3 DH/DSA Attacks via Shor's
- Diffie-Hellman key exchange break
- DSA signature forgery (post-quantum)
- Discrete logarithm in any finite field
- Primitive root finding (post-quantum)
- Quadratic residue attacks
- Index calculus attacks (post-quantum)
- Pohlig-Hellman attacks (post-quantum)
- Baby-step giant-step (post-quantum)
- Pollard's rho attacks (post-quantum)

---

## Section 4: GROVER'S ALGORITHM ATTACKS (25+ techniques)

### 4.1 Symmetric Key Attacks
- AES-128 → 64-bit quantum security (Grover's)
- AES-192 → 96-bit quantum security
- AES-256 → 128-bit quantum security (NIST recommended)
- DES → completely broken (Grover's + brute force)
- 3DES → reduced to 56-bit quantum security
- Blowfish → broken (key size)
- Twofish → reduced security
- ChaCha20 → reduced to 128-bit quantum security
- Serpent → reduced security
- Camellia → reduced security

### 4.2 Hash Function Attacks
- SHA-1 → collision finding (classical) + Grover's (preimage)
- SHA-256 → 128-bit quantum preimage security
- SHA-512 → 256-bit quantum preimage security
- MD5 → completely broken
- RIPEMD-160 → reduced security
- BLAKE2/BLAKE3 → quantum security analysis
- Keccak → quantum security analysis
- SHA-3 → quantum security analysis
- Hash collision resistance reduction
- Hash preimage resistance reduction

### 4.3 Search & Optimization Attacks
- Unstructured search (quadratic speedup)
- Sudoku/logic puzzle solving (Grover's)
- Password brute force (quadratic speedup)
- Key space search (symmetric crypto)
- Permutation search
- Subset sum problem
- Knapsack problem
- Graph coloring problem
- Satisfiability problem (SAT)

---

## Section 5: QUANTUM KEY DISTRIBUTION (25+ techniques)

### 5.1 QKD Protocols
- BB84 protocol (Bennett-Brassard 1984)
- E91 protocol (Ekert 1991)
- B92 protocol (Bennett 1992)
- SARG04 protocol
- Continuous-variable QKD (CV-QKD)
- Differential phase shift QKD (DPS-QKD)
- Decoy-state QKD
- Measurement-device-independent QKD (MDI-QKD)
- Twin-field QKD (TF-QKD)
- Device-independent QKD (DI-QKD)
- QKD with trusted relays
- Satellite QKD (quantum satellite)
- Fiber QKD (quantum fiber)
- Free-space QKD

### 5.2 QKD Implementation Attacks
- Photon number splitting attack
- Intercept-resend attack
- Side-channel attacks on QKD
- Detector blinding attack
- Trojan horse attack on QKD
- Time-shift attack
- Phase-remapping attack
- Unambiguous state discrimination
- Quantum hacking techniques

### 5.3 QKD Security
- QKD information-theoretic security
- QKD key rate analysis
- QKD distance limitations
- QKD integration with classical crypto
- QKD network architectures
- QKD standardization (ETSI, ITU-T)
- QKD product evaluation

---

## Section 6: QUANTUM SIDE-CHANNEL ATTACKS (30+ techniques)

### 6.1 Quantum Hardware Side-Channels
- Timing attacks on quantum computers
- Power analysis attacks on quantum circuits
- Electromagnetic emanation attacks
- Acoustic attacks on quantum hardware
- Thermal attacks on quantum systems
- Photon emission attacks
- Crosstalk attacks on qubits
- Leakage detection on quantum gates

### 6.2 Post-Quantum Side-Channels
- Timing attacks on lattice-based crypto
- Power analysis on lattice implementations
- Cache attacks on post-quantum algorithms
- Branch prediction attacks
- Memory access pattern attacks
- Error message attacks
- Fault injection on PQC
- electromagnetic analysis on PQC

### 6.3 Quantum Random Number Generation
- Quantum random number generators (QRNG)
- Min-entropy extraction
- randomness extraction
- Quantum noise exploitation
- Vacuum fluctuation QRNG
- Photon detection QRNG
- Quantum TRNG vs classical TRNG
- NIST randomness testing

---

## Section 7: QUANTUM CRYPTO ANALYSIS (30+ techniques)

### 7.1 Lattice Analysis
- Lattice reduction (LLL, BKZ, BKZ 2.0)
- Lattice enumeration
- Lattice sieving ( BKZ, lattice sieving)
- CVP (Closest Vector Problem) solvers
- SVP (Shortest Vector Problem) solvers
- LWE (Learning With Errors) hardness
- Ring-LWE hardness
- Module-LWE hardness
- NTRU lattice analysis
- Lattice-based cryptanalysis

### 7.2 Code-Based Analysis
- Goppa code decoding
- Information set decoding
- Stern's algorithm
- Dumer's algorithm
- Patterson's algorithm
- Code-based distinguishers
- Code-based key recovery
- Decoding complexity analysis

### 7.3 Hash-Based Analysis
- Merkle tree collision attacks
- Second preimage attacks on Merkle trees
- Quantum collision finding (BHT algorithm)
- Multicollision attacks
- Herding attacks
- Quantum sponge attacks
- Quantum length extension
- Quantum padding attacks

---

## Section 8: QUANTUM NETWORKING (20+ techniques)

### 8.1 Quantum Network Protocols
- Quantum teleportation
- Superdense coding
- Quantum error correction codes (surface code)
- Entanglement swapping
- Quantum repeaters
- Quantum memory
- Quantum network routing
- Quantum internet protocols

### 8.2 Quantum Network Security
- Quantum network eavesdropping
- Entanglement-based attacks
- Quantum man-in-the-middle
- Quantum denial of service
- Quantum resource exhaustion
- Quantum side-channel exploitation

### 8.3 Quantum Cloud Computing
- Quantum cloud access (IBM Quantum, AWS Braket, Azure Quantum)
- Quantum circuit verification
- Quantum program obfuscation
- Quantum homomorphic encryption
- Quantum secure multi-party computation
- Quantum oblivious transfer
- Quantum zero-knowledge proofs

---

## Section 9: QUANTUM FORENSICS (15+ techniques)

### 9.1 Quantum State Analysis
- Quantum state tomography
- Quantum process tomography
- Quantum gate set tomography
- Quantum state verification
- Entanglement verification
- Quantum channel characterization
- Quantum noise characterization
- Quantum error characterization

### 9.2 Quantum Incident Response
- Quantum attack detection
- Quantum key compromise detection
- Quantum channel monitoring
- Quantum state reconstruction
- Quantum forensics evidence collection
- Quantum chain of custody
- Quantum evidence preservation

---

## Section 10: QUANTUM MIGRATION (25+ techniques)

### 10.1 Crypto Agility
- Crypto agility framework design
- Algorithm negotiation protocols
- Hybrid classical/post-quantum mode
- Graceful algorithm replacement
- Backward compatibility management
- Version negotiation
- Key migration strategies
- Certificate migration

### 10.2 Migration Planning
- Cryptographic inventory (all crypto assets)
- Risk assessment (harvest-now-decrypt-later)
- Priority classification (data at rest vs in transit)
- Migration timeline planning
- Testing post-quantum implementations
- Performance benchmarking (PQC vs classical)
- Integration testing
- Rollback planning

### 10.3 Standards & Compliance
- NIST PQC standards (FIPS 203, 204, 205)
- ETSI QKD standards
- ISO quantum-safe standards
- NSA CNSA 2.0 quantum requirements
- ANSSI quantum recommendations
- BSI quantum migration guidelines
- Australian quantum strategy
- EU quantum flagships

---

*QUANTUM MODE — Post-quantum cryptography & quantum attack methodology*
*For assessing quantum readiness and post-quantum migration*
