# Use Cases

Seven use cases for the Password Crack-Time Simulator, covering individual evaluation, batch auditing, strategy comparison, and programmatic integration.

---

## UC-1: Single Password Evaluation

**Actor:** End user (developer, security analyst, or curious individual)

**Preconditions:**
- Simulator is installed and configured with default data assets
- User has a password to evaluate

**Main Flow:**
1. User invokes CLI: `crack-time estimate "MyPassword123" --hash bcrypt_cost12 --hardware consumer`
2. System runs shared password analysis (tokenization, pattern detection, dictionary matching)
3. System runs all applicable estimators against the analyzed password
4. System applies DP decomposition to find optimal segmentation
5. System computes `min(all_strategy_times)` using hardware hash rate
6. System displays crack time, winning attack, per-strategy breakdown, strength rating, and explanation

**Postconditions:**
- User receives a complete crack-time report for their password

**Example:**
```
$ crack-time estimate "Summer2024!" --hash bcrypt_cost12 --hardware rig_8x_rtx4090

Crack Time:   ~1.4 hours
Rating:       WEAK (1/4)
Winner:       Hybrid attack (dictionary + mask ?d?d?d?d?s)
```

---

## UC-2: Batch Password Audit

**Actor:** Security auditor or IT administrator

**Preconditions:**
- Simulator is installed with full data assets (including larger wordlists)
- User has a file containing passwords to audit (one per line)

**Main Flow:**
1. User invokes CLI: `crack-time batch passwords.txt --hash bcrypt_cost12 --hardware professional --output results.json`
2. System reads password file
3. System evaluates each password through the full pipeline
4. System writes JSON results for each password (crack time, rating, winning attack)
5. System displays summary statistics (distribution of ratings, most common weaknesses)

**Postconditions:**
- JSON output file contains per-password analysis
- Console shows aggregate summary (e.g., "72% rated CRITICAL or WEAK; most common weakness: dictionary + rules")

**Example:**
```
$ crack-time batch company_passwords.txt --hash bcrypt_cost12 --hardware professional

Evaluated 1,247 passwords:
  CRITICAL (0): 412 (33.0%)
  WEAK (1):     489 (39.2%)
  FAIR (2):     218 (17.5%)
  STRONG (3):    87 (7.0%)
  VERY STRONG:   41 (3.3%)

Top weaknesses: dictionary+rules (38%), breach match (27%), keyboard walk (12%)
```

---

## UC-3: Passphrase Strategy Comparison

**Actor:** Security researcher or policy designer

**Preconditions:**
- Simulator is installed
- User wants to compare passphrase construction strategies

**Main Flow:**
1. User evaluates a set of passphrases with varying strategies:
   - 3-word passphrase: `correct horse battery`
   - 3-word with random caps: `correct Horse battery`
   - 3-word with mid-word punctuation: `cor!rect horse battery`
   - 4-word passphrase: `correct horse battery staple`
2. System evaluates each under identical hash/hardware settings
3. User compares crack times and winning attacks across strategies

**Postconditions:**
- User can quantitatively answer: "Is a 4th word better than random capitalization?" (Motivating Question #1 from [PROJECT.md](../PROJECT.md))

**Example:**
```
$ crack-time estimate "correct horse battery" --hash bcrypt_cost12 --hardware professional
Crack Time: ~18 minutes (PRINCE 3-word, 7776^3 keyspace)

$ crack-time estimate "correct horse battery staple" --hash bcrypt_cost12 --hardware professional
Crack Time: ~3.2 days (PRINCE 4-word, 7776^4 keyspace)

$ crack-time estimate "cor!rect horse battery" --hash bcrypt_cost12 --hardware professional
Crack Time: ~4.1 hours (hybrid: dictionary + inserted symbol)
```

---

## UC-4: Hash Algorithm Impact Assessment

**Actor:** Application developer choosing a password hashing scheme

**Preconditions:**
- Simulator is installed
- User wants to understand how hash algorithm choice affects security

**Main Flow:**
1. User evaluates the same password under different hash algorithms:
   - MD5
   - SHA-256
   - bcrypt cost=10
   - bcrypt cost=12
   - Argon2id
2. System returns crack times for each, demonstrating the ~9 orders of magnitude difference
3. User compares results to make an informed hashing decision

**Postconditions:**
- User sees concrete wall-clock times showing hash algorithm impact (Motivating Question #4)

**Example:**
```
Password: "Summer2024!" with 8x RTX 4090

  MD5:           ~0.003 seconds
  SHA-256:       ~0.02 seconds
  bcrypt (10):   ~2.6 hours
  bcrypt (12):   ~10.5 hours
  Argon2id:      ~25 hours
```

---

## UC-5: Attacker Profile Comparison

**Actor:** Security analyst preparing a threat model

**Preconditions:**
- Simulator is installed with attacker profile presets

**Main Flow:**
1. User evaluates a password under different attacker profiles:
   - Script kiddie: single GPU, basic wordlist, best64 rules
   - Professional: 8 GPUs, large wordlists, multiple rule sets, all Phase 1-3 techniques
   - Nation-state: 10K+ GPUs, all techniques including neural
2. System applies profile-specific estimator selection and hardware configuration
3. User sees how the same password holds up against escalating threat levels

**Postconditions:**
- User understands password strength relative to different threat actors

**Example:**
```
Password: "Tr0ub4dor&3" against bcrypt cost=12

  Script kiddie:   ~47 days   (dictionary + best64 rules only)
  Professional:    ~2.3 hours (full rule inversion, 8 GPUs)
  Nation-state:    ~1.2 seconds (massive parallelism)
```

---

## UC-6: Library Integration (Programmatic API)

**Actor:** Application developer integrating strength estimation into their app

**Preconditions:**
- Simulator is installed as a Python package (`pip install crack-time-simulator`)

**Main Flow:**
1. Developer imports the simulator in their Python code
2. Developer calls the API with a password, hash algorithm, and hardware tier
3. API returns a structured result object with all estimates
4. Developer uses the result to enforce password policy or provide feedback

**Postconditions:**
- Application has access to crack-time estimates programmatically

**Example:**
```python
from crack_time import Simulator

sim = Simulator()
result = sim.estimate(
    password="Summer2024!",
    hash_algorithm="bcrypt_cost12",
    hardware_tier="professional"
)

print(result.crack_time_seconds)   # 5040
print(result.rating)               # 1 (WEAK)
print(result.winning_attack)       # "hybrid"
print(result.explanation)          # "Dictionary word 'Summer' + year+symbol suffix"

if result.rating < 2:
    raise ValueError("Password too weak")
```

---

## UC-7: Targeted Attack Simulation (with Personal Context)

**Actor:** Security-conscious user evaluating their own password

**Preconditions:**
- Simulator is installed
- User is willing to provide personal context for targeted analysis

**Main Flow:**
1. User provides their password plus optional context:
   - Username, email address, site name
   - Birthdate, pet names, other personal info
2. System adds context items as rank-1 dictionary entries
3. System evaluates with all estimators, including semantic/targeted matching
4. System flags any password components that match personal context
5. System reports whether the password is vulnerable to a targeted attack

**Postconditions:**
- User knows whether personal information makes their password weaker

**Example:**
```
$ crack-time estimate "fluffy2019!" --hash bcrypt_cost12 --hardware professional \
    --context-name "fluffy" --context-type "pet_name"

Crack Time:   ~0.8 seconds
Rating:       CRITICAL (0/4)
Winner:       Targeted dictionary (personal context match)

WARNING: "fluffy" matches your pet name. An attacker with basic personal
information would add this to their targeted wordlist as a priority-1 entry.
```

---

## Use Case Summary

| UC | Name | Primary Actor | Key Question Answered |
|----|------|--------------|----------------------|
| UC-1 | Single password evaluation | End user | "How long would this take to crack?" |
| UC-2 | Batch password audit | Security auditor | "How weak is our password corpus?" |
| UC-3 | Passphrase strategy comparison | Researcher | "Which passphrase strategy is strongest?" |
| UC-4 | Hash algorithm impact | Developer | "How much does hash choice matter?" |
| UC-5 | Attacker profile comparison | Analyst | "Who can crack this, and who can't?" |
| UC-6 | Library integration | Developer | "How do I use this in my application?" |
| UC-7 | Targeted attack simulation | Security-conscious user | "Am I vulnerable to personal info attacks?" |

---

See also: [Requirements](02-requirements.md) | [Project Overview](01-project-overview.md) | [Validation Strategy](08-validation-strategy.md)
