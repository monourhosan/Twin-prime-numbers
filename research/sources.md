# Verified Research Sources and Authoritative Records

**Document Version:** 1.0.0  
**Research Date (UTC):** 2026-11-12T05:15:00Z  
**Primary Auditor:** Monour Hosan Saif  
**Contributors:** Gemini and ChatGPT  

---

## 1. Registry Audit: The Largest Known Twin Primes

### 1.1 All-Time Size Record (Verified Largest Known Twin Prime Pair)
* **Form:** $2996863034895 \times 2^{1290000} \pm 1$
  * Lower member ($p$): $2996863034895 \times 2^{1290000} - 1$
  * Upper member ($p+2$): $2996863034895 \times 2^{1290000} + 1$
* **Decimal Digits:** 388,342 digits in each member of the pair.
* **Discovery Timestamp:** 2016-09-14T04:24:46Z
* **Discoverer:** Tom Greer (United States), participating in the PrimeGrid distributed computing project (Sophie Germain Prime Search subproject on BOINC).
* **Verification Timestamp:** 2016-09-19 (independent verification completed and announced).
* **Verifier:** Don Palmer (Canada), using Jean Penné's LLR (Lucas-Lehmer-Riesel / Proth testing software).
* **Sieve Software:** TwinGen (developed by Yves Gallot and contributors).
* **Authoritative Registry Listings:**
  * **The PrimePages (t5k.org):** Rank 1 on "The Top Twenty: Twin Primes" ([https://t5k.org/top20/page.php?id=1](https://t5k.org/top20/page.php?id=1)). Assigned prover code `L2035` (`Display: Greer, TwinGen, PrimeGrid, LLR`). Database last checked: 2026-11-12.
  * **Tony Forbes' Prime $k$-tuple History:** Listed as "First known with more than 300,000 digits" ([https://pzktupel.de/KTHIST/kt002.php](https://pzktupel.de/KTHIST/kt002.php), last updated 2026-01-10).
  * **PrimeGrid Official Announcement:** [http://www.primegrid.com/forum_thread.php?id=7022](http://www.primegrid.com/forum_thread.php?id=7022).

---

## 2. Chronologically Most Recent Documented Discoveries

### 2.1 Latest Top-Tier Record Entry (as of November 2026)
* **Form:** $152748736824915 \times 2^{480480} \pm 1$
* **Decimal Digits:** 144,654 digits each.
* **Discovery / Verification Date:** 2026-01-10
* **Discoverers / Contributors:** Daniel Brockwell, Göran Schmidt, Carlos Eduardo Pinho, Michael Kwok, Richard Kapek, Stephan Vink.
* **Software Stack:** TwinGen, NewPGen, Twin Prime Search (TPS), PRST (Proth / Riesel Sieve Tester by Roman Trunov).
* **Registry Status:**
  * Ranked #3 in all-time size on The PrimePages Top 20 Twin Primes under prover code `A90` (`Display: Vink, Brockwell, TwinGen, NewPGen, TPS, PRST`).
  * Documented as newest major entry on `pzktupel.de/KTHIST/kt002.php` (updated 10 January 2026).

### 2.2 Other Recent Discoveries Documented in 2024–2025
* **2025-06-23:** $15898321815 \times 2^{333645} \pm 1$ (100,448 digits) by Serge Batalov (NewPGen, OpenPFGW). Rank #7 on PrimePages.
* **2025-05-15:** $1867513233 \times 2^{266698} \pm 1$ (80,294 digits) by Bo Tornberg (TwinGen, LLR). Rank #9 on PrimePages.
* **2025-04-04:** $9955858992 \times 11^{111111} \pm 1$ (115,721 digits) by Göran Schmidt (NewPGen, PRST). Rank #6 on PrimePages.
* **2024-04-26:** $669821552^{16384} - 669821552^{8192} \pm 1$ (144,605 digits) by Roman Trunov (Cyclo, PRST). Rank #4 on PrimePages.
* **2024-03-29:** $222710306^{16384} - 222710306^{8192} \pm 1$ (136,770 digits) by Bruce Marler (Cyclo, PRST). Rank #5 on PrimePages.
* **2024-05-06:** $201926367 \times 2^{266668} \pm 1$ (80,284 digits) by Göran Schmidt (NewPGen, PRST). Rank #10 on PrimePages.

### 2.3 Scope Clarification: Size Champion vs. "Latest" Discovery
* **Size Champion ($388,342$ digits):** The pair discovered by Tom Greer in September 2016 remains the largest verified twin prime pair known to humanity as of November 2026.
* **Chronological "Latest" in Scoped Registries:** The entry $152748736824915 \times 2^{480480} \pm 1$ announced on 2026-01-10 is the latest entry appearing on the verified top-size tables.
* **Global "Latest" Twin Prime:** Cannot be defined or tracked globally. Tens of thousands of small twin primes (e.g., $10$ to $1000$ digits) are discovered routinely by amateur mathematicians, automated scripts, and hobbyist networks without being indexed in centralized databases. Therefore, claims of "the latest twin prime discovered" must always be qualified with the explicit registry and size threshold.

---

## 3. Mathematical Status of "The Last Twin Prime Ever"

* **The Twin Prime Conjecture:**
  $$\Pi_2 = \{(p, p+2) \mid p, p+2 \in \mathbb{P}\}, \quad |\Pi_2| = \infty?$$
  The question of whether $|\Pi_2|$ is infinite or finite remains one of the premier unsolved problems in number theory.
* **Open Status:**
  No proof of the infinitude of twin primes exists. Likewise, no proof of the finiteness of twin primes exists.
* **Theoretical Milestones:**
  * **Brun's Theorem (1919):** Viggo Brun proved that the sum of the reciprocals of twin primes converges:
    $$B_2 = \sum_{p, p+2 \in \mathbb{P}} \left(\frac{1}{p} + \frac{1}{p+2}\right) \approx 1.902160583104$$
    This demonstrates that twin primes, if infinite, are asymptotically much rarer than general primes (since $\sum_{p \in \mathbb{P}} 1/p = \infty$).
  * **Hardy-Littlewood Conjecture (1923):** Conjectures asymptotic density:
    $$\pi_2(x) \sim 2 C_2 \int_2^x \frac{dt}{(\ln t)^2}, \quad C_2 = \prod_{p \ge 3} \left(1 - \frac{1}{(p-1)^2}\right) \approx 0.6601618158$$
  * **Bounded Gaps Breakthroughs (2013–2014):**
    * Yitang Zhang (2013) proved $\liminf_{n \to \infty} (p_{n+1} - p_n) < 7 \times 10^7$.
    * James Maynard (2013) and Terence Tao (Polymath8b, 2014) reduced the unconditional prime gap bound to $\le 246$.
    * Under the Generalized Elliott-Halberstam (GEH) conjecture, the gap is bounded by $\le 6$. However, reaching a gap of exactly $2$ remains an open challenge not resolved by sieve methods alone (the "parity problem").
* **Epistemological Principle:**
  * A finite search, no matter how vast, cannot locate "the ultimate last twin prime" because computation over a bounded domain $[1, M]$ cannot rule out the existence of twin primes in $(M, \infty)$.
  * Conversely, for any specified closed interval $[L, U] \subset \mathbb{N}$, the question of the **largest twin-prime pair within $[L, U]$** is strictly decidable and can be mathematically proven via exhaustive segmented sieving and deterministic primality certification.

---

## 4. Primary Web and Literature Citations

1. **Caldwell, Chris K., et al.** "The Top Twenty: Twin Primes." *The PrimePages*, University of Tennessee at Martin. URL: [https://t5k.org/top20/page.php?id=1](https://t5k.org/top20/page.php?id=1). (Accessed: 2026-11-12).
2. **Forbes, Tony.** "Prime k-Tuplet History: Twin Primes (kt002)." URL: [https://pzktupel.de/KTHIST/kt002.php](https://pzktupel.de/KTHIST/kt002.php) and [https://pzktupel.de/Top10.php](https://pzktupel.de/Top10.php). (Accessed: 2026-11-12).
3. **Greer, Tom, and PrimeGrid.** "World Record Twin Primes Announced: $2996863034895 \times 2^{1290000} \pm 1$." PrimeGrid Project Forums, September 2016. URL: [http://www.primegrid.com/forum_thread.php?id=7022](http://www.primegrid.com/forum_thread.php?id=7022).
4. **Weisstein, Eric W.** "Twin Primes." *From MathWorld--A Wolfram Web Resource*. URL: [https://mathworld.wolfram.com/TwinPrimes.html](https://mathworld.wolfram.com/TwinPrimes.html).
5. **Weisstein, Eric W.** "Twin Prime Conjecture." *From MathWorld--A Wolfram Web Resource*. URL: [https://mathworld.wolfram.com/TwinPrimeConjecture.html](https://mathworld.wolfram.com/TwinPrimeConjecture.html).
6. **OEIS Foundation Inc.** "A001359: Lesser of twin primes." *The On-Line Encyclopedia of Integer Sequences*, URL: [https://oeis.org/A001359](https://oeis.org/A001359).
7. **OEIS Foundation Inc.** "A006512: Greater of twin primes." *The On-Line Encyclopedia of Integer Sequences*, URL: [https://oeis.org/A006512](https://oeis.org/A006512).
8. **Zhang, Yitang.** "Bounded gaps between primes." *Annals of Mathematics* 179.3 (2014): 1121-1174.
9. **Maynard, James.** "Small gaps between primes." *Annals of Mathematics* 181.1 (2015): 383-413.
10. **Brillhart, John, D. H. Lehmer, and J. L. Selfridge.** "New primality criteria and factorizations of $2^m \pm 1$." *Mathematics of Computation* 29.130 (1975): 620-647.
11. **Proth, François.** "Théorèmes sur les nombres premiers." *Comptes Rendus de l'Académie des Sciences Paris* 87 (1878): 926-928.
