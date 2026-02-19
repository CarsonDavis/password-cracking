# Password Cracking Hardware Benchmarks - Research Log

**Topic:** Hardware benchmarks and speed metrics for password cracking across hash algorithms and hardware tiers
**Date:** 2026-02-15
**Description:** Systematic gathering of hash-rate benchmarks (hashes/second) for common password hashing algorithms across consumer GPUs, multi-GPU rigs, cloud instances, and nation-state-level clusters. Goal is to produce data suitable for a configurable crack-time estimation simulator.

## Sources

[1]: https://gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd "Hashcat v6.2.6 benchmark on the Nvidia RTX 4090 - Chick3nman GitHub Gist"
[2]: https://www.onlinehashcrack.com/tools-benchmark-hashcat-nvidia-rtx-4090.php "Benchmark Hashcat RTX 4090 - Online Hash Crack"
[3]: https://hashcat.net/forum/thread-11277.html "RTX 4090 Benchmark - Hashcat Forum"
[4]: https://gist.github.com/ZephrFish/b849331aafa015ddd7786ca20ce718d7 "Hashcat v6.2.6 benchmark on 14x Nvidia RTX 4090 - ZephrFish GitHub Gist"
[5]: https://www.onlinehashcrack.com/tools-benchmark-hashcat-gtx-1080-ti-1070-ti-rtx-2080-ti-rtx-3090-3080-4090.php "Benchmark Hashcat with RTX 5090 / 4090 / A100, H100 - Online Hash Crack"
[6]: https://gist.github.com/Chick3nman/e4fcee00cb6d82874dace72106d73fef "Hashcat v6.1.1 benchmark on the Nvidia RTX 3090 - Chick3nman GitHub Gist"
[7]: https://gist.github.com/Chick3nman/09bac0775e6393468c2925c1e1363d5c "Hashcat v6.2.6-851 benchmark on the Nvidia RTX 5090 FE - Chick3nman GitHub Gist"
[8]: https://x.com/Chick3nman512/status/1889102304717967739 "Chick3nman RTX 5090 benchmark announcement on X"
[9]: https://www.tomshardware.com/pc-components/gpus/nvidia-rtx-5090-can-crack-an-8-digit-passcode-in-just-3-hours "Tom's Hardware - RTX 5090 password cracking benchmarks"
[10]: https://gist.github.com/Chick3nman/d65bcd5c137626c0fcb05078bba9ca89 "Hashcat v6.1.1 benchmark on Nvidia Tesla A100 PCIE (4x) - Chick3nman GitHub Gist"
[11]: https://gist.github.com/Chick3nman/e1417339accfbb0b040bcd0a0a9c6d54 "Hashcat v6.2.6 benchmark on Nvidia H100 PCIe - Chick3nman GitHub Gist"
[12]: https://research.redhat.com/blog/article/how-expensive-is-it-to-crack-a-password-derived-with-argon2-very/ "Red Hat Research - How expensive is it to crack Argon2"
[13]: https://www.researchgate.net/publication/301848293_Open_Sesame_The_Password_Hashing_Competition_and_Argon2 "Open Sesame: The Password Hashing Competition and Argon2"
[14]: https://scatteredsecrets.medium.com/bcrypt-password-cracking-extremely-slow-not-if-you-are-using-hundreds-of-fpgas-7ae42e3272f6 "Scattered Secrets - bcrypt cracking with FPGAs"
[15]: https://systemoverlord.com/2021/06/05/gpu-accelerated-password-cracking-in-the-cloud.html "System Overlord - GPU Accelerated Password Cracking in the Cloud"
[16]: https://guptadeepak.com/the-complete-guide-to-password-hashing-argon2-vs-bcrypt-vs-scrypt-vs-pbkdf2-2026/ "Password Hashing Guide 2025: Argon2 vs Bcrypt vs Scrypt vs PBKDF2"
[17]: https://hackaday.com/2020/05/15/all-your-passwords-are-belong-to-fpga/ "Hackaday - All Your Passwords Are Belong To FPGA"
[18]: https://www.usenix.org/system/files/conference/woot14/woot14-malvoni.pdf "USENIX WOOT14 - Energy-Efficient Bcrypt Cracking"
[19]: https://aws.amazon.com/ec2/pricing/on-demand/ "AWS EC2 On-Demand Pricing"
[20]: https://aws.amazon.com/blogs/aws/announcing-up-to-45-price-reduction-for-amazon-ec2-nvidia-gpu-accelerated-instances/ "AWS 45% price reduction for GPU instances (June 2025)"
[21]: https://www.hivesystems.com/password-table "Hive Systems 2025 Password Table"
[22]: https://www.hivesystems.com/blog/are-your-passwords-in-the-green "Hive Systems 2025 Blog - Password Cracking Times"
[23]: https://www.nsa.gov/portals/75/documents/news-features/declassified-documents/cryptologic-quarterly/NSA_and_the_Supercomputer.pdf "NSA and the Supercomputer Industry (declassified)"
[24]: https://worldstopdatacenters.com/nsa-bumblehive/ "NSA Bumblehive Utah Data Center"
[25]: https://vast.ai/pricing/gpu/RTX-4090 "Vast.ai RTX 4090 pricing"
[26]: https://gist.github.com/epixoip/973da7352f4cc005746c627527e4d073 "GTX 1080 Ti hashcat benchmarks - epixoip GitHub Gist"
[27]: https://www.blackhillsinfosec.com/hashcat-benchmarks-nvidia-gtx-1080ti-gtx-1070-hashcat-benchmarks/ "Black Hills InfoSec - GTX 1080Ti Hashcat Benchmarks"
[28]: https://gist.github.com/epixoip/a83d38f412b4737e99bbef804a270c40 "8x GTX 1080 hashcat benchmarks - epixoip GitHub Gist"
[29]: https://specopssoft.com/blog/hashing-algorithm-cracking-bcrypt-passwords/ "Specops - How tough is bcrypt to crack?"
[30]: https://www.onlinehashcrack.com/guides/password-recovery/gpu-cluster-cracking-scale-to-millions-of-hashes.php "Online Hash Crack - GPU Cluster Cracking"

## Research Log

---

### Search: "hashcat benchmark RTX 4090 MD5 SHA1 SHA256 bcrypt NTLM hashes per second 2025"

Key RTX 4090 benchmarks from Hashcat v6.2.6 ([Chick3nman Gist][1], [Online Hash Crack][2], [Hashcat Forum][3]):

- **MD5 (mode 0):** ~164-169 GH/s
- **SHA-1 (mode 100):** ~50.9 GH/s
- **SHA-256 (mode 1400):** ~22.7 GH/s
- **NTLM (mode 1000):** ~288.5 GH/s
- **bcrypt (mode 3200):** ~184 kH/s (cost=5)

---

### Fetch: Chick3nman RTX 4090 Gist

Full single RTX 4090 (Asus Strix, stock clocks) ([Chick3nman Gist][1]):

| Mode | Algorithm | Speed |
|------|-----------|-------|
| 0 | MD5 | 164.1 GH/s |
| 100 | SHA-1 | 50,638.7 MH/s |
| 1400 | SHA2-256 | 21,975.5 MH/s |
| 1700 | SHA2-512 | 7,483.4 MH/s |
| 1000 | NTLM | 288.5 GH/s |
| 3200 | bcrypt | 184.0 kH/s |
| 8900 | scrypt | 7,126 H/s |
| 10900 | PBKDF2-HMAC-SHA256 | 8,865.7 kH/s |
| 22000 | WPA-PBKDF2-PMKID+EAPOL | 2,533.3 kH/s |
| 5600 | NetNTLMv2 | 11,764.8 MH/s |

---

### Fetch: ZephrFish 14x RTX 4090 Gist

14x RTX 4090 rig ([ZephrFish Gist][4]):

| Mode | Algorithm | 14x 4090 Speed | Scaling Efficiency |
|------|-----------|----------------|--------------------|
| 0 | MD5 | 2,009.0 GH/s | 87.4% |
| 100 | SHA-1 | 667.1 GH/s | 94.1% |
| 1400 | SHA2-256 | 288.2 GH/s | 93.7% |
| 1700 | SHA2-512 | 97.4 GH/s | 93.0% |
| 1000 | NTLM | 3,419.2 GH/s | 84.6% |
| 3200 | bcrypt | 3,180.4 kH/s | ~100%+ |
| 22000 | WPA-PBKDF2 | 34,003.2 kH/s | 95.9% |

---

### RTX 3090 benchmarks

([Chick3nman RTX 3090 Gist][6]):

| Mode | Algorithm | RTX 3090 Speed |
|------|-----------|----------------|
| 0 | MD5 | 65,079.1 MH/s |
| 100 | SHA-1 | 22,757.6 MH/s |
| 1400 | SHA2-256 | 9,713.2 MH/s |
| 1700 | SHA2-512 | 2,863.9 MH/s |
| 1000 | NTLM | 121.2 GH/s |
| 3200 | bcrypt | 96,662 H/s |
| 10900 | PBKDF2-HMAC-SHA256 | 3,785.4 kH/s |
| 22000 | WPA-PBKDF2-PMKID+EAPOL | 1,129.0 kH/s |

---

### RTX 5090 benchmarks

([Chick3nman RTX 5090 Gist][7]):

| Mode | Algorithm | RTX 5090 Speed | vs RTX 4090 |
|------|-----------|----------------|-------------|
| 0 | MD5 | 220.6 GH/s | +34.4% |
| 100 | SHA-1 | 70,245.1 MH/s | +38.7% |
| 1400 | SHA2-256 | 28,353.3 MH/s | +29.0% |
| 1700 | SHA2-512 | 10,048.6 MH/s | +34.3% |
| 1000 | NTLM | 340.1 GH/s | +17.9% |
| 3200 | bcrypt | 304.8 kH/s | +65.7% |
| 8900 | scrypt | 7,760 H/s | +8.9% |
| 10900 | PBKDF2-HMAC-SHA256 | 11,157.2 kH/s | +25.8% |
| 22000 | WPA-PBKDF2-PMKID+EAPOL | 3,409.1 kH/s | +34.6% |

---

### Cloud GPU benchmarks (A100, H100)

**4x A100 PCIE** ([A100 Gist][10]):

| Mode | Algorithm | 4x A100 Speed |
|------|-----------|---------------|
| 0 | MD5 | 258.7 GH/s |
| 1000 | NTLM | 480.3 GH/s |
| 3200 | bcrypt | 553.4 kH/s |

**Single H100 PCIe** ([H100 Gist][11]):

| Mode | Algorithm | H100 Speed |
|------|-----------|------------|
| 0 | MD5 | 87,530.6 MH/s |
| 1000 | NTLM | 158.6 GH/s |
| 3200 | bcrypt | 251.5 kH/s |

---

### Argon2, FPGA, and attack cost data

**Argon2 GPU performance** ([Password Hashing Guide][16]):

| Algorithm | Configuration | RTX 4090 H/s | GPU vs CPU Speedup |
|-----------|---------------|---------------|--------------------|
| Bcrypt | cost=12 | 95,000 | 396x |
| Scrypt | N=2^17 | 2,800 | 8x |
| Argon2id | m=128MB | 380 | 1.5x |

**Attack cost estimates (AWS p3.16xlarge)** for 8-char complex password ([Password Hashing Guide][16]):

| Algorithm | Configuration | Duration | Est. Cost |
|-----------|---------------|----------|-----------|
| PBKDF2 | 600k iter | 3 days | $5,000 |
| Bcrypt | cost=12 | 30 days | $40,000 |
| Scrypt | N=2^17 | 200 days | $300,000 |
| Argon2id | m=128MB, t=3 | 500 days | $750,000 |

**FPGA bcrypt** ([Scattered Secrets][14]): 4U FPGA cracker achieves 2.1M bcrypt H/s at 585W

---

### AWS pricing, cloud rental, nation-state estimates

**AWS post June 2025 reductions** ([AWS blog][20]):
- p3.16xlarge (8x V100): ~$24.48/hr
- p4d.24xlarge (8x A100): ~$22/hr (after 33% reduction)
- p5.48xlarge (8x H100): reduced ~44%

**Vast.ai** ([Vast.ai][25]): RTX 4090 from ~$0.16-0.18/hr

**Cloud cost analysis** ([System Overlord][15]): T4 best cost-effectiveness at $0.35/hr on GCP (2021 data). Value = hashes per dollar, not raw speed.

**Nation-state:** No public benchmarks. Modeling estimate: 10,000-100,000 equivalent top-tier GPUs.

---

### GTX 1080 Ti benchmarks (historical ~2017-2020 era)

GTX 1080 Ti stock clocks ([epixoip Gist][26]):

| Mode | Algorithm | GTX 1080 Ti Speed |
|------|-----------|-------------------|
| 0 | MD5 | 30,963.5 MH/s |
| 100 | SHA-1 | 11,518.4 MH/s |
| 1400 | SHA2-256 | 4,453.2 MH/s |
| 1700 | SHA2-512 | 1,519.6 MH/s |
| 1000 | NTLM | 53,173.6 MH/s |
| 3200 | bcrypt | 20,668 H/s |
| 10900 | PBKDF2-SHA256 | 1,727.2 kH/s |
| 2500 | WPA/WPA2 | 576.8 kH/s |

---

### bcrypt cost factor conversion

**Key math** ([Specops][29], [Wikipedia bcrypt](https://en.wikipedia.org/wiki/Bcrypt)):
- Hashcat benchmarks use cost factor 5 (2^5 = 32 iterations)
- Each +1 cost factor = 2x slower
- Cost 5 → Cost 10: 2^5 = 32x slower
- Cost 5 → Cost 12: 2^7 = 128x slower
- Cost 5 → Cost 14: 2^9 = 512x slower

So for RTX 4090 bcrypt at 184 kH/s (cost=5):
- **Cost 10:** 184,000 / 32 = **5,750 H/s**
- **Cost 12:** 184,000 / 128 = **1,437 H/s**
- **Cost 14:** 184,000 / 512 = **359 H/s**
