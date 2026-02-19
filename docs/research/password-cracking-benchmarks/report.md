# Password Cracking Hardware Benchmarks: Data for a Crack-Time Simulator

**Date:** 2026-02-15

## Executive Summary

This report provides benchmark data for estimating password crack times across hash algorithms and attacker hardware tiers. The core reference point is the NVIDIA RTX 4090 running Hashcat -- the most widely benchmarked configuration in the password-cracking community. All data is sourced from published Hashcat benchmarks by Chick3nman (Sam Croley), community-submitted multi-GPU results, and secondary analysis from security researchers.

The key takeaway for simulator design: the difference between the fastest algorithm (NTLM at 288 billion H/s) and the slowest (Argon2id at ~380 H/s) on identical hardware spans **nine orders of magnitude**. The choice of hash algorithm matters far more than the attacker's hardware budget.

---

## 1. Single-GPU Benchmarks (Hashcat)

All values are hashes per second on a single GPU at stock clocks. Hashcat uses optimized kernels. bcrypt benchmarks use cost factor 5 unless noted.

### Fast Hashes (Unsalted/Simple)

| Algorithm | Hashcat Mode | GTX 1080 Ti | RTX 3090 | RTX 4090 | RTX 5090 |
|-----------|-------------|-------------|----------|----------|----------|
| **MD5** | 0 | 31.0 GH/s | 65.1 GH/s | 164.1 GH/s | 220.6 GH/s |
| **SHA-1** | 100 | 11.5 GH/s | 22.8 GH/s | 50.6 GH/s | 70.2 GH/s |
| **SHA-256** | 1400 | 4.5 GH/s | 9.7 GH/s | 22.0 GH/s | 28.4 GH/s |
| **SHA-512** | 1700 | 1.5 GH/s | 2.9 GH/s | 7.5 GH/s | 10.0 GH/s |
| **NTLM** | 1000 | 53.2 GH/s | 121.2 GH/s | 288.5 GH/s | 340.1 GH/s |

Sources: [GTX 1080 Ti](https://gist.github.com/epixoip/973da7352f4cc005746c627527e4d073), [RTX 3090](https://gist.github.com/Chick3nman/e4fcee00cb6d82874dace72106d73fef), [RTX 4090](https://gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd), [RTX 5090](https://gist.github.com/Chick3nman/09bac0775e6393468c2925c1e1363d5c)

### Slow/Adaptive Hashes

| Algorithm | Config | GTX 1080 Ti | RTX 3090 | RTX 4090 | RTX 5090 |
|-----------|--------|-------------|----------|----------|----------|
| **bcrypt** (cost=5) | Mode 3200 | 20,668 H/s | 96,662 H/s | 184,000 H/s | 304,800 H/s |
| **scrypt** | Mode 8900 | -- | -- | 7,126 H/s | 7,760 H/s |
| **PBKDF2-SHA256** | Mode 10900 | 1,727 kH/s | 3,785 kH/s | 8,866 kH/s | 11,157 kH/s |
| **WPA/WPA2** | Mode 22000 | 577 kH/s | 1,129 kH/s | 2,533 kH/s | 3,409 kH/s |
| **NetNTLMv2** | Mode 5600 | -- | 5,032 MH/s | 11,765 MH/s | 16,018 MH/s |

Note on scrypt: The hashcat scrypt benchmark uses specific N/r/p parameters that may differ between hashcat versions. Values across GPU generations may not be directly comparable due to parameter changes.

### Argon2 (Estimated, from secondary sources)

Hashcat does not natively support Argon2 as of v6.2.6. These figures come from a [2025 password hashing guide](https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/) analysis benchmarking on RTX 4090:

| Algorithm | Configuration | RTX 4090 H/s | GPU vs CPU Advantage |
|-----------|---------------|---------------|---------------------|
| Argon2id | m=19 MiB, t=2, p=1 (OWASP min) | ~1,500 | ~2x |
| Argon2id | m=64 MiB, t=3, p=1 (recommended) | ~600 | ~1.5x |
| Argon2id | m=128 MiB, t=4, p=1 (high-sec) | ~380 | ~1.5x |

The near-parity between GPU and CPU performance is the entire point of Argon2's memory-hard design. Each hash computation requires the full memory allocation (e.g., 128 MiB), which saturates GPU memory and eliminates the parallelism advantage.

---

## 2. bcrypt Cost Factor Conversion Table

Hashcat benchmarks bcrypt at cost factor 5 (32 iterations). Real-world deployments use higher cost factors. Each +1 to the cost factor doubles computation time.

**Formula:** `speed_at_cost_N = benchmark_speed / 2^(N - 5)`

| Cost Factor | Iterations | RTX 4090 H/s | RTX 5090 H/s | 8x RTX 4090 H/s |
|-------------|-----------|---------------|---------------|------------------|
| 5 (benchmark) | 32 | 184,000 | 304,800 | ~1,380,000 |
| 8 | 256 | 23,000 | 38,100 | ~172,500 |
| 10 | 1,024 | 5,750 | 9,525 | ~43,125 |
| 12 (OWASP recommended) | 4,096 | 1,437 | 2,381 | ~10,781 |
| 13 | 8,192 | 719 | 1,191 | ~5,391 |
| 14 (high security) | 16,384 | 359 | 595 | ~2,695 |

For simulator use: store the cost=5 benchmark value and derive other cost factors dynamically using the formula above.

---

## 3. Multi-GPU Scaling

### Empirical Scaling Data (14x RTX 4090)

From a [14x RTX 4090 benchmark](https://gist.github.com/ZephrFish/b849331aafa015ddd7786ca20ce718d7):

| Algorithm | 1x Speed | 14x Speed | Actual Scaling | Efficiency |
|-----------|----------|-----------|----------------|------------|
| MD5 | 164.1 GH/s | 2,009.0 GH/s | 12.24x | 87% |
| SHA-1 | 50.6 GH/s | 667.1 GH/s | 13.17x | 94% |
| SHA-256 | 22.0 GH/s | 288.2 GH/s | 13.12x | 94% |
| SHA-512 | 7.5 GH/s | 97.4 GH/s | 13.02x | 93% |
| NTLM | 288.5 GH/s | 3,419.2 GH/s | 11.85x | 85% |
| bcrypt | 184.0 kH/s | 3,180.4 kH/s | ~100% | ~100% |
| WPA/WPA2 | 2,533 kH/s | 34,003 kH/s | 13.42x | 96% |

### Scaling Model for Simulators

Based on the empirical data, a reasonable scaling model:

```
effective_speed = single_gpu_speed * num_gpus * scaling_factor

where scaling_factor depends on algorithm type:
  - Fast hashes (MD5, NTLM): 0.85-0.90 per GPU (PCIe bandwidth limited)
  - Medium hashes (SHA-*, PBKDF2): 0.90-0.95 per GPU
  - Slow hashes (bcrypt, scrypt): 0.95-1.00 per GPU (compute-bound, minimal data transfer)
```

The pattern: algorithms with higher throughput saturate PCIe bandwidth sooner, reducing multi-GPU scaling efficiency. Slow, compute-intensive algorithms scale nearly perfectly because each GPU works independently with minimal host communication.

For rigs with more than ~8 GPUs, expect an additional 2-5% efficiency loss per doubling of GPU count due to system-level bottlenecks (memory bus, thermal throttling, driver overhead).

---

## 4. Hardware Tiers for Simulator Configuration

### Tier Definitions

| Tier | Description | Reference Hardware | Multiplier vs 1x RTX 4090 |
|------|-------------|--------------------|---------------------------|
| **Budget** | Single older consumer GPU | GTX 1080 Ti | 0.19x (MD5), 0.11x (bcrypt) |
| **Consumer** | Single current-gen GPU | RTX 4090 | 1.0x (baseline) |
| **Enthusiast** | Single latest-gen GPU | RTX 5090 | 1.34x (MD5), 1.66x (bcrypt) |
| **Small Rig** | 4x current-gen GPUs | 4x RTX 4090 | ~3.6x |
| **Large Rig** | 8x current-gen GPUs | 8x RTX 4090 | ~7.0x |
| **Dedicated Cluster** | 14x GPUs (documented) | 14x RTX 4090 | ~12.2x (MD5), ~13.4x (WPA) |
| **Cloud Small** | 1 cloud GPU instance | 1x H100 PCIe | 0.53x (MD5), 1.37x (bcrypt) |
| **Cloud Large** | 8x A100 cluster | p4d.24xlarge equiv. | ~3.2x (MD5) |
| **Well-Funded** | 100 GPUs (est.) | 100x RTX 4090 | ~85x |
| **Nation-State** | 10,000-100,000 GPUs (est.) | Theoretical | ~8,500-85,000x |

### Cloud GPU Performance Note

A critical finding: datacenter GPUs (H100, A100) are **not** superior to consumer GPUs for password cracking. The H100 PCIe achieves only 87.5 GH/s on MD5 versus the RTX 4090's 164.1 GH/s. Datacenter GPUs are optimized for tensor operations and floating-point throughput -- password hashing relies on integer arithmetic and memory operations where consumer GPUs have the edge.

**Implication for cloud-based cracking:** Renting consumer GPUs on platforms like Vast.ai ($0.16-0.18/hr for RTX 4090) is more cost-effective than AWS datacenter GPU instances for password cracking workloads.

---

## 5. Cloud Cracking Cost Estimates

### Per-Hour Cloud GPU Costs (as of early 2026)

| Platform | Instance / GPU | GPUs | Hourly Cost | Best For |
|----------|---------------|------|-------------|----------|
| Vast.ai | RTX 4090 | 1 | $0.16-0.18 | Best value per hash |
| Vast.ai | RTX 3090 | 1 | $0.10-0.14 | Budget cracking |
| AWS | p3.16xlarge (8x V100) | 8 | ~$24.48 | Legacy, overpriced |
| AWS | p4d.24xlarge (8x A100) | 8 | ~$22.00 | After 33% reduction |
| AWS | p5.48xlarge (8x H100) | 8 | Reduced ~44% | AI workloads, not ideal for hashing |
| GCP | T4 single | 1 | $0.35 | Best mainstream cloud value |

### Cost to Exhaust a Keyspace (8-character password, all printable ASCII)

Keyspace: 95^8 = 6.63 x 10^15 candidates

Using Vast.ai RTX 4090 at $0.17/hr:

| Algorithm | Config | Speed (1 GPU) | Time to Exhaust | Cost (1 GPU) | Cost (100 GPUs) |
|-----------|--------|---------------|-----------------|--------------|-----------------|
| MD5 | -- | 164.1 GH/s | 11.2 hours | $1.91 | $19.10 |
| SHA-256 | -- | 22.0 GH/s | 3.5 days | $14.21 | $142 |
| NTLM | -- | 288.5 GH/s | 6.4 hours | $1.08 | $10.84 |
| bcrypt | cost=10 | 5,750 H/s | 36,600 years | $54.5M | $545K |
| bcrypt | cost=12 | 1,437 H/s | 146,300 years | $218M | $2.18M |
| Argon2id | m=64MiB | ~600 H/s | 350,500 years | $522M | $5.22M |
| PBKDF2-SHA256 | 600k iter | 8,866 kH/s | 8.7 days | $35.43 | $354 |

These are worst-case full-keyspace exhaustion times. Real attacks use dictionaries, rules, and masks that dramatically reduce the search space for non-random passwords.

### Cost Estimates from Security Researchers

From a [2025 password hashing analysis](https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/) using AWS p3.16xlarge ($24.48/hr) for an 8-character complex password:

| Algorithm | Configuration | Duration | Estimated Cost |
|-----------|---------------|----------|----------------|
| PBKDF2 | 600k iterations | 3 days | $5,000 |
| Bcrypt | cost=12 | 30 days | $40,000 |
| Scrypt | N=2^17 | 200 days | $300,000 |
| Argon2id | m=128MB, t=3 | 500 days | $750,000 |

---

## 6. FPGA and ASIC Considerations

### FPGA bcrypt Performance

From [Scattered Secrets' FPGA research](https://scatteredsecrets.medium.com/bcrypt-password-cracking-extremely-slow-not-if-you-are-using-hundreds-of-fpgas-7ae42e3272f6):

| Metric | FPGA Cracker (4U) | RTX 4090 Equivalent |
|--------|-------------------|---------------------|
| bcrypt H/s (cost=5) | 2,100,000 | ~184,000 |
| Power consumption | 585W | ~450W (per GPU) |
| Equivalent GPUs | ~75x RTX 2080 Ti | 1x RTX 4090 |
| Performance/Watt | ~3,590 H/W | ~409 H/W |

Key points:
- FPGAs are **4-5x more efficient per watt** than GPUs for bcrypt
- A single quad-FPGA board outperforms a top-tier GPU by 4-5x for bcrypt
- FPGAs matter most for algorithms where GPUs are already slow (bcrypt, scrypt)
- For fast hashes (MD5, SHA-*), GPUs remain more practical due to easier programming and availability

### ASIC Threat Model

No widely available ASICs exist specifically for password hashing as of 2026. Bitcoin ASICs compute SHA-256d (double-SHA-256) but are not directly applicable to password cracking because:
- Password hashing requires different input formatting per candidate
- bcrypt, scrypt, and Argon2 are specifically designed to resist ASIC implementation through memory-hardness

For simulator purposes: treat ASIC as equivalent to a large FPGA cluster for the specific algorithms they target (primarily bcrypt). Memory-hard algorithms (scrypt, Argon2) remain effectively ASIC-resistant.

---

## 7. Memory-Hard Function Bottlenecks

### Why Memory-Hard Algorithms Resist GPU Acceleration

| Algorithm | Memory per Hash | GPU Memory Available | Max Parallel Hashes | Bottleneck |
|-----------|----------------|---------------------|---------------------|------------|
| MD5 | ~0 bytes | N/A | Millions | Compute only |
| bcrypt | 4 KB | 24 GB (RTX 4090) | ~6M (but compute-limited) | Compute (Blowfish rounds) |
| scrypt (N=2^17) | 128 MB | 24 GB | ~192 | Memory bandwidth |
| Argon2id (m=64MB) | 64 MB | 24 GB | ~375 | Memory capacity + bandwidth |
| Argon2id (m=128MB) | 128 MB | 24 GB | ~187 | Memory capacity + bandwidth |

The GPU advantage over CPUs for each algorithm:

| Algorithm | GPU/CPU Speedup Ratio |
|-----------|-----------------------|
| MD5 | ~620,000x |
| SHA-256 | ~80,000x |
| PBKDF2 (600k) | ~4,700x |
| bcrypt (cost=12) | ~396x |
| scrypt (N=2^17) | ~8x |
| Argon2id (m=128MB) | ~1.5x |

The progression is clear: as memory requirements increase, GPUs lose their parallelism advantage. At 128 MB per hash, a GPU can only compute ~187 hashes simultaneously instead of the millions possible with MD5. This is exactly the design intent of memory-hard functions.

---

## 8. Generational Performance Trends

### GPU Generation Comparison (Single GPU, MD5 baseline)

| GPU | Release Year | MD5 H/s | vs GTX 1080 Ti | Price at Launch |
|-----|-------------|---------|----------------|-----------------|
| GTX 1080 Ti | 2017 | 31.0 GH/s | 1.0x | $699 |
| RTX 3090 | 2020 | 65.1 GH/s | 2.1x | $1,499 |
| RTX 4090 | 2022 | 164.1 GH/s | 5.3x | $1,599 |
| RTX 5090 | 2025 | 220.6 GH/s | 7.1x | $1,999 |

### Algorithm-Specific Generational Gains (RTX 3090 to RTX 5090)

| Algorithm | RTX 3090 | RTX 5090 | Improvement |
|-----------|----------|----------|-------------|
| MD5 | 65.1 GH/s | 220.6 GH/s | 3.4x |
| SHA-256 | 9.7 GH/s | 28.4 GH/s | 2.9x |
| NTLM | 121.2 GH/s | 340.1 GH/s | 2.8x |
| bcrypt (cost=5) | 96.7 kH/s | 304.8 kH/s | 3.2x |
| PBKDF2-SHA256 | 3.8 MH/s | 11.2 MH/s | 2.9x |
| scrypt | -- | 7,760 H/s | -- |

For simulator forecasting: consumer GPU password-cracking throughput has been roughly doubling every 2-3 years for compute-bound algorithms, and slightly less for memory-bound algorithms.

---

## 9. Recommended Simulator Parameters

### Default Hash Rates (RTX 4090 baseline, per GPU)

For a configurable simulator, use the RTX 4090 as the baseline unit and apply multipliers:

```
HASH_RATES_PER_GPU = {
    # Fast hashes (unsalted)
    "md5":              164_100_000_000,    # 164.1 GH/s
    "sha1":              50_638_700_000,    # 50.6 GH/s
    "sha256":            21_975_500_000,    # 22.0 GH/s
    "sha512":             7_483_400_000,    # 7.5 GH/s
    "ntlm":             288_500_000_000,    # 288.5 GH/s

    # Adaptive hashes (with standard parameters)
    "bcrypt_cost5":             184_000,    # Hashcat benchmark default
    "bcrypt_cost10":              5_750,    # 184000 / 2^5
    "bcrypt_cost12":              1_437,    # 184000 / 2^7
    "bcrypt_cost14":                359,    # 184000 / 2^9

    # Memory-hard hashes
    "scrypt_default":             7_126,    # Hashcat mode 8900
    "argon2id_19m_t2":            1_500,    # Estimated
    "argon2id_64m_t3":              600,    # Estimated
    "argon2id_128m_t4":             380,    # Estimated

    # Protocol-specific
    "pbkdf2_sha256_iterations": 8_865_700,  # Raw; divide by (iterations/1)
    "wpa_wpa2":               2_533_300,    # Mode 22000
    "netntlmv2":         11_764_800_000,    # 11.8 GH/s
}
```

### Hardware Tier Multipliers

```
HARDWARE_TIERS = {
    "single_gtx1080ti":    {"gpus": 1, "multiplier": 0.19},   # ~2017 era
    "single_rtx3090":      {"gpus": 1, "multiplier": 0.40},   # ~2020 era
    "single_rtx4090":      {"gpus": 1, "multiplier": 1.00},   # Baseline
    "single_rtx5090":      {"gpus": 1, "multiplier": 1.34},   # 2025
    "rig_4x_rtx4090":      {"gpus": 4, "multiplier": 3.60},
    "rig_8x_rtx4090":      {"gpus": 8, "multiplier": 7.00},
    "cloud_h100":          {"gpus": 1, "multiplier": 0.53},   # Datacenter
    "cloud_4x_a100":       {"gpus": 4, "multiplier": 1.58},   # ~4x A100
    "dedicated_100gpu":    {"gpus": 100, "multiplier": 85.0},
    "nation_state_10k":    {"gpus": 10000, "multiplier": 8_500},
    "nation_state_100k":   {"gpus": 100000, "multiplier": 85_000},
}
```

### Scaling Formula

```
def estimate_crack_time(keyspace_size, algorithm, hardware_tier):
    base_rate = HASH_RATES_PER_GPU[algorithm]
    tier = HARDWARE_TIERS[hardware_tier]
    effective_rate = base_rate * tier["multiplier"]
    seconds = keyspace_size / effective_rate
    return seconds
```

For bcrypt with variable cost factors:
```
def bcrypt_rate(base_cost5_rate, cost_factor):
    return base_cost5_rate / (2 ** (cost_factor - 5))
```

---

## 10. Important Caveats for Simulator Design

1. **Hashcat benchmarks use cost=5 for bcrypt.** This is unrealistically low. Always convert to the target cost factor before calculating crack times. Most production systems use cost 10-14.

2. **Argon2 benchmarks are estimates.** Hashcat does not support Argon2. The figures come from secondary analysis and should be treated as approximate.

3. **These are brute-force rates.** Real attacks combine dictionary words, rules, and masks that make common passwords fall orders of magnitude faster than keyspace math suggests. A simulator should offer both "random password" and "dictionary attack" modes.

4. **Cloud GPUs are not ideal for hashing.** The H100 underperforms the RTX 4090 for password cracking. Simulator users selecting "cloud" hardware should not assume datacenter = faster.

5. **scrypt benchmarks are parameter-sensitive.** The N, r, and p parameters dramatically affect speed. The hashcat default may differ from real-world deployments. Always specify parameters alongside the hash rate.

6. **Multi-GPU scaling is not linear** but is close (85-95% for most algorithms). The model above accounts for this, but extreme GPU counts (>1000) may see further degradation that is difficult to model without empirical data.

7. **FPGA threat exists for bcrypt** but not for memory-hard algorithms. If modeling sophisticated attackers, consider FPGA multipliers for bcrypt specifically (roughly 10x efficiency over consumer GPUs in performance per watt, or 4-5x raw speed per board).

8. **Nation-state estimates are speculative.** No public benchmarks exist. The 10,000-100,000 GPU range is a modeling assumption based on known infrastructure scale, not confirmed capability.

---

## Sources

- [Hashcat v6.2.6 RTX 4090 Benchmark - Chick3nman](https://gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd)
- [Hashcat v6.2.6 RTX 5090 Benchmark - Chick3nman](https://gist.github.com/Chick3nman/09bac0775e6393468c2925c1e1363d5c)
- [Hashcat v6.1.1 RTX 3090 Benchmark - Chick3nman](https://gist.github.com/Chick3nman/e4fcee00cb6d82874dace72106d73fef)
- [GTX 1080 Ti Benchmark - epixoip](https://gist.github.com/epixoip/973da7352f4cc005746c627527e4d073)
- [14x RTX 4090 Benchmark - ZephrFish](https://gist.github.com/ZephrFish/b849331aafa015ddd7786ca20ce718d7)
- [4x A100 Benchmark - Chick3nman](https://gist.github.com/Chick3nman/d65bcd5c137626c0fcb05078bba9ca89)
- [H100 PCIe Benchmark - Chick3nman](https://gist.github.com/Chick3nman/e1417339accfbb0b040bcd0a0a9c6d54)
- [Password Hashing Guide 2025 - Deepak Gupta](https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/)
- [FPGA bcrypt Cracking - Scattered Secrets](https://scatteredsecrets.medium.com/bcrypt-password-cracking-extremely-slow-not-if-you-are-using-hundreds-of-fpgas-7ae42e3272f6)
- [GPU Cracking in the Cloud - System Overlord](https://systemoverlord.com/2021/06/05/gpu-accelerated-password-cracking-in-the-cloud.html)
- [Hive Systems 2025 Password Table](https://www.hivesystems.com/password-table)
- [How Expensive is Argon2 to Crack - Red Hat Research](https://research.redhat.com/blog/article/how-expensive-is-it-to-crack-a-password-derived-with-argon2-very/)
- [AWS GPU Price Reductions (June 2025)](https://aws.amazon.com/blogs/aws/announcing-up-to-45-price-reduction-for-amazon-ec2-nvidia-gpu-accelerated-instances/)
- [Vast.ai RTX 4090 Pricing](https://vast.ai/pricing/gpu/RTX-4090)
- [Tom's Hardware - RTX 5090 Password Cracking](https://www.tomshardware.com/pc-components/gpus/nvidia-rtx-5090-can-crack-an-8-digit-passcode-in-just-3-hours)
