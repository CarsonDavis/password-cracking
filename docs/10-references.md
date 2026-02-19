# References

Papers, tools, and benchmark sources informing the Password Crack-Time Simulator.

---

## Academic Papers

| Citation | Venue | Year | Contribution |
|----------|-------|------|-------------|
| Weir et al., "Password Cracking Using Probabilistic Context-Free Grammars" | IEEE S&P | 2009 | PCFG approach; cracked 28--129% more than JtR |
| Bonneau, "The Science of Guessing" | IEEE S&P | 2012 | Statistical framework for password distributions |
| Kelley et al., "Guess Again (and Again and Again)" | IEEE S&P | 2012 | Guess-number methodology; 16+ chars > 8+complexity |
| Duermuth et al., "OMEN: Faster Password Guessing Using an Ordered Markov Enumerator" | ESSoS | 2015 | Level-based Markov enumeration |
| Dell'Amico & Filippone, "Monte Carlo Strength Evaluation" | ACM CCS | 2015 | Efficient guess-number estimation via sampling |
| Ur et al., "Measuring Real-World Accuracies and Biases" | USENIX Sec | 2015 | Multi-strategy comparison; min-auto ensemble |
| Wheeler, "zxcvbn: Low-Budget Password Strength Estimation" | USENIX Sec | 2016 | DP decomposition; pattern-matching meter |
| Melicher et al., "Fast, Lean, and Accurate" | USENIX Sec | 2016 | Neural network guessability; Monte Carlo estimation |
| Ur et al., "Design and Evaluation of a Data-Driven Password Meter" | ACM CCS | 2017 | NN-based meter with actionable feedback |
| Hitaj et al., "PassGAN" | ACNS | 2019 | GAN-based password generation |
| Liu et al., "Reasoning Analytically About Password-Cracking Software" | USENIX Sec | 2022 | Rule inversion for analytical guess numbers |
| Rando et al., "PassGPT" | arXiv | 2023 | LLM-based password generation |
| Wang & Ding, "No Single Silver Bullet" | USENIX Sec | 2023 | Multi-strategy PSM evaluation |

## Tools and Data Sources

| Resource | URL | Used For |
|----------|-----|----------|
| zxcvbn (Dropbox) | github.com/dropbox/zxcvbn | Pattern matching algorithms, adjacency graphs, frequency data |
| zxcvbn-ts | github.com/zxcvbn-ts/zxcvbn | Modernized TypeScript reference |
| pcfg_cracker (Weir) | github.com/lakiw/pcfg_cracker | PCFG grammar training and generation |
| OMEN (RUB-SysSec) | github.com/RUB-SysSec/OMEN | Markov model training and level enumeration |
| Password-Guessing-Framework | github.com/RUB-SysSec/Password-Guessing-Framework | Strategy comparison methodology |
| Analytic password cracking (UChicago) | github.com/UChicagoSUPERgroup/analytic-password-cracking | Rule inversion algorithm |
| CMU guess-calculator-framework | github.com/cupslab/guess-calculator-framework | Min-auto ensemble, Monte Carlo estimation |
| CMU neural_network_cracking | github.com/cupslab/neural_network_cracking | LSTM password model |
| Hashcat | hashcat.net/hashcat | Hash rate benchmarks, rule file format |
| HIBP Pwned Passwords | haveibeenpwned.com/Passwords | Breach password database |
| Hive Systems Password Table | hivesystems.com/password-table | Brute-force reference times |

## Benchmark Sources

| Source | URL |
|--------|-----|
| RTX 4090 Benchmarks (Chick3nman) | gist.github.com/Chick3nman/32e662a5bb63bc4f51b847bb422222fd |
| RTX 5090 Benchmarks (Chick3nman) | gist.github.com/Chick3nman/09bac0775e6393468c2925c1e1363d5c |
| RTX 3090 Benchmarks (Chick3nman) | gist.github.com/Chick3nman/e4fcee00cb6d82874dace72106d73fef |
| 14x RTX 4090 Benchmarks (ZephrFish) | gist.github.com/ZephrFish/b849331aafa015ddd7786ca20ce718d7 |
| H100 Benchmarks (Chick3nman) | gist.github.com/Chick3nman/e1417339accfbb0b040bcd0a0a9c6d54 |

---

See also: [Research Reports](research/) for full study write-ups.
