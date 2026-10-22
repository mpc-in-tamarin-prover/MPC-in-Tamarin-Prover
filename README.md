# MPC_symbolic_model_in_tamarin


### attribute based models
We show here how to capture MPC attributes. Parties try to check whether their values are the same or not. The values are always fresh, so they are always different. Therefore, secure MPC should evaluate to false. However, if an adversary violates security attributes, they are able to force MPC to return true.

We created four similar models, three for a specific output delivery attribute with a malicious adversary and one for a semi-honest adversary. 

#### output delivery attributes
Fairness and GOD models differ only in how they approach the output delivery attribute; they capture privacy, correctness and independence of inputs in the same way. The security with abort model is different. This approach is used to obtain schemes which preserve attributes in the presence of a malicious adversary in a dishonest majority setting. Therefore, the adversary controls who gets the output; however, he can't achieve anything more.

#### semi-honest adversary
This model captures a semi-honest adversary. Meaning, he can only violate privacy and nothing more. 


### Complexity measures
In the file __complexity measures__ we focused on measuring the models' complexity. There we facilitate an abstract functionality — just a function f(x1, ..., xn). Then, the not-correct function is cf(x1, ..., xn), and the dependent input is captured by evaluating the dependent(x) function on honest input. We always assume that the adversary has to corrupt n-1 parties to violate the security attributes. The goal is to check how much time we need to prove that the model is built properly. We covered MPC with group sizes of {2,3,4}.

Please note that complexity in Tamarin is somewhat random and strongly depends on what the lemmas state, and on heuristics. The tests, rather than providing exact timings, provide their order of magnitude.


### tests
The tests.py file contains a script that runs models and provides CPU and RAM measurements. The script takes one argument which points to a specific benchmark.

__argument list:__
1. C2 - run complexity model test, the group contains 2 parties.
2. C3 - run complexity model test, the group contains 3 parties.
3. C4 - run complexity model test, the group contains 4 parties.
4. AllC - run all complexity model tests.
5. semi-honest - run model with semi-honest adversary
6. GOD - run setup model with guaranteed output delivery
7. Fairness - run setup model with fairness
8. Abort - run setup model with security with abort

`tests.py` exits non-zero when Tamarin reports a falsified lemma or the run
fails, so it can be used as a CI gate:

```bash
python3 tests.py            # every model
python3 tests.py AllC       # only the complexity models
```

### Repository layout

```
GOD/                  guaranteed output delivery (malicious adversary)
fairness/             fairness variant of the output delivery attribute
sec_with_abort/       security with abort
semi_honest/          semi-honest adversary (privacy only)
complexity_measures/  the same experiment for 2, 3 and 4 parties
scripts/              tooling (lemma index generator)
docs/                 generated lemma index and the review findings
results.txt           recorded `tamarin-prover --prove` runs (2/3/4 parties)
tests.py              benchmark runner
```

Each model directory holds `MPC.spthy` (rules), `Sanity_checks.spthy`
(executability/reachability witnesses) and `violation_lemmas.spthy`
(the properties), plus a `tactics` file included by the main theory.

### Reproducing the numbers

```bash
tamarin-prover --version && maude --version      # record both in the paper
python3 scripts/lemma_index.py                   # refresh docs/LEMMA_INDEX.md
python3 tests.py C2                              # 2 parties
python3 tests.py C3                              # 3 parties
python3 tests.py C4                              # 4 parties
```

Numbers currently recorded in `results.txt` (processing time as printed by
Tamarin): 2 parties 16.82 s, 3 parties 628.78 s, 4 parties 1477.73 s. Two of
those runs also print `WARNING: 1 wellformedness check failed!` — see
`docs/FINDINGS.md`, item F8, before quoting them in a paper.

### Artifact notes for a submission

* Pin the tool versions: `tamarin-prover --version`, `maude --version`, CPU model
  and core count. Tamarin's search is sensitive to both.
* Record at least 5 runs per model and report the median; the README already says
  the timings are order-of-magnitude, and a single run cannot support even that
  claim (see `docs/FINDINGS.md`, F11).
* `docs/LEMMA_INDEX.md` is generated from the sources, so the counts quoted in
  the paper (lemmas per model, `all-traces` vs `exists-trace`) can be re-derived
  with one command instead of being transcribed by hand.
