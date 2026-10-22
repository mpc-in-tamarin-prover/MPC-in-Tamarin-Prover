# Findings from an external review pass (22 Oct 2026)

Reviewer: Krzysztof Kanciak's agent (models only — the manuscript is not in this
repository). Scope: commit `83bf06b`, all 21 `.spthy` files, `tests.py`,
`results.txt`, `complexity_measures/*/results.txt`.

Everything below was re-checked in this tree with the command shown, so it can be
disagreed with by running the same command. Nothing here was inferred from the
paper text.

## How to reproduce the checks

```bash
grep -rn "Use_A" --include=*.spthy .                 # F1
grep -rn "Corruption_Party\|Input_Party" --include=*.spthy . | grep -v "\[" # F3b
grep -n "Dep()\|Ind()" complexity_measures/4_party/*.spthy   # F2
grep -n -A2 "rule Eval_m:" complexity_measures/4_party/MPC.spthy  # F3
grep -n -A6 "rule Independence_of_inputs_3" complexity_measures/3_party/MPC.spthy  # F4
grep -n -A8 "rule RCV:" complexity_measures/2_party/MPC.spthy      # F5
grep -n "T_init(" */MPC.spthy complexity_measures/*/MPC.spthy | grep restriction -A2  # F6
python3 scripts/lemma_index.py && cat docs/LEMMA_INDEX.md          # F9
```

## Checked and found sound (so the list above is not read as "everything is broken")

* `_restrict(P << G)` in `Honest_MPC_input` is satisfiable: `Input_reachability`
  (`H_in` reachable) is verified in all three complexity runs
  (`results.txt:7,82,175`), so the honest-input rule does fire. A reviewer
  suspicion that this rule was dead is **refuted by the recorded runs**.
* `sources` is a legitimate source lemma and should stay, even though it is not a
  privacy theorem.
* The 2-party and 3-party models use consistent action names (`Ind()`, `Use_P`,
  `P_Corrupted`); the slips in F1/F2/F3b are local, not a house style.
* `Sanity_checks.spthy` is the right idea (reachability witnesses exist for most
  branches); what is missing is a *joint* multi-party witness, not the concept.


## P0 — lemmas that cannot be false (vacuity)

**F1. Six lemmas reference an action that no rule emits.**
`output_delivery_a_party_without_output` uses `Use_A(X)`, but the only result-use
action in the tree is `Use_P(P)` (`rule Party_receive_result`). A lemma over an
action that never occurs is verified for structural reasons and says nothing
about non-delivery.

Affected: `GOD/violation_lemmas.spthy:66`, `fairness/…:66`, `sec_with_abort/…:6`,
`complexity_measures/2_party/…:83`, `…/3_party/…:104`, `…/4_party/…:127`.

Suggested change (needs re-proving, may fail — that is the point):

```tamarin
lemma output_delivery_a_party_without_output[heuristic={All_lemmas}]:
"All X R #i #j
    .O_mal(X)@i & Result(X, R)@j
    ==> (not Ex #k. Use_P(X)@k)"
```

This needs a `Result(receiver, result)` action emitted by `Send_result`, so the
denial can be attached to a concrete delivery attempt.

**F2. `independence_of_inputs_hold` in the 4-party model checks the wrong action.**
The 4-party models emit `Dep()` (`complexity_measures/4_party/MPC.spthy:153,164,175,186`)
but the lemma is stated over `Ind()`
(`complexity_measures/4_party/violation_lemmas.spthy:81-83`). `Ind()` does not
exist in that theory, so the lemma is vacuous. Rename the action or the lemma —
whichever the paper actually argues. The 2-party and 3-party trees are consistent
here, so this is a local slip, not a methodological one.

**F3. Privacy/correctness/independence `*_hold` lemmas are conditional on "no
corruption in the whole trace", while the only way to break those attributes is an
explicitly modelled violation rule.** That is a legitimate fault-injection design,
but then the paper must not call the result "MPC security": it is "the fault rule
is unreachable without corruption". Two cheap additions close most of the gap:

1. an attribution lemma — `Ind()/Dep() ⇒ some party corrupted in the same session`;
2. a non-vacuity lemma — an all-honest, same-session run exists where both parties
   submit exactly one input and use the ideal result.

**F3b. Two restrictions guard actions that no rule emits.** `only_one_corruption_per_party`
uses `Corruption_Party(X1)` (`complexity_measures/2_party/MPC.spthy:232`,
`3_party/…:278`, `4_party/…:313`) and `one_input_per_party` uses `Input_Party(X)`
(`3_party/…:281`, `4_party/…:316`); the rules emit `P_Corrupted` and `Inx`
instead. Both restrictions are therefore vacuous in every model — the "one input
per party" and "one corruption per party" guarantees are not enforced at all.
Either emit the actions from the rules or delete the restrictions; leaving them
in gives a false sense of enforcement.

## P1 — modelling bugs that affect the scaling claim

**F4. The 4-party corruption threshold ignores the fourth party.**
`complexity_measures/4_party/MPC.spthy:100` guards `Eval_m` with
`_restrict(mal + mal << hmA + hmB + hmC)` — `hmD` is missing from the sum while
`HM(hmA, hmB, hmC, hmD)` and the argument tuple carry it. The honest/malicious
partition is therefore wrong exactly in the model used for the largest timing.
Two consequences worth stating explicitly in the paper:

* the enforced threshold is **two** corrupted parties in the 4-party model, not
  `n-1 = 3` as `README.md` claims ("we always assume that the adversary has to
  corrupt n-1 parties"); the 3-party model is consistent with `n-1`, the 4-party
  one is not, so the "same experiment at n=2,3,4" framing does not hold;
* with the `hmD` term missing, the "honest majority" configuration (D the only
  corrupted party) cannot reach `Eval_m` at all.


**F5. `Independence_of_inputs_3` puts the third tag in the second party's slot.**
`complexity_measures/3_party/MPC.spthy:164` matches `<B, dataB, hmA>`; every other
rule of that model matches `<B, dataB, hmB>`. As written the rule fires when A's
tag is copied into B's record, which is not the intended "B is dishonest" branch.

**F6. Endpoint binding: `RCV` accepts a trusted party unrelated to the one that
was initialised.** `complexity_measures/2_party/MPC.spthy:61-69` reads
`[T_RCV(TP, G), RcvS(A, TT, …), RcvS(B, TT, …)]` — `TT` is a fresh variable not
tied to `TP`. Either bind `TT = TP` or drop the argument; otherwise the model
allows two trusted parties in one computation.

**F7. A restriction with the wrong action arity.**
`restriction adversary_cannot_corrupt_trusted_party` uses `T_init(TP)@i`, but the
init rule emits the nullary `T_init()` (`GOD/MPC.spthy:58` and `semi_honest/MPC.spthy:58`).
The restriction therefore never matches. Use `T_init_TP(TP)@i` if the intent is to
protect the trusted party of a concrete session.

## P2 — evidence and tooling

**F8. Two of the three recorded runs report a failed wellformedness check.**
`results.txt:75-76` and `results.txt:162-163` contain
`WARNING: 1 wellformedness check failed!` before the 628.78 s and 1477.73 s
timings. Numbers from those runs should not enter the paper's table until the
warning is diagnosed and the run repeated.

**F9. `complexity_measures/3_party/results.txt` is stale.**
It says `analyzed: Sec_MPC.spthy` and `processing time: 1424.42s` — a different
file name from `3_party/MPC.spthy`, and 1424 s versus 628.78 s in `results.txt`.
Two incompatible timings for the "3 parties" row exist in the repository; keep one,
with the command line that produced it.

**F10. `tests.py` ran the GOD model under the `semi-honest` label.**
`tests.py:83-84` (old) mapped `semi-honest` to `models[4]`, which is `GOD/MPC.spthy`;
`semi_honest/MPC.spthy` was never benchmarked. Fixed in this PR, together with a
non-zero exit code on falsified lemmas so the script can gate CI.

**F11. The complexity numbers are single runs.**
`results.txt` holds one run per model, on an unrecorded CPU, without the Tamarin
and Maude versions. For a claim of the form "cost grows by roughly an order of
magnitude per added party", record at least 5 runs per model and report median +
spread, plus `tamarin-prover --version` and `maude --version`.

**F12. A quantifier in the fairness sanity lemma is malformed.**
`fairness/Sanity_checks.spthy:59` reads `==> not Ex #j Use_P(P)@j` — the dot after
`#j` is missing, and `P` is not bound in that lemma. Either it fails to parse or
`P` is treated as a free term; both make the lemma say something other than
"some party never uses a result". Compare with the same lemma in `GOD/`.

**F13. Positional typos inside lemmas make them test a different party.**
`complexity_measures/4_party/violation_lemmas.spthy:114` binds `Inx(D,G,dataB)`
while the lemma is about `dataD` (the `Use_r` on the next line uses `dataD`);
`complexity_measures/2_party/violation_lemmas.spthy:72` writes
`P_Corrupted(inA)` where `inA` is data, not a party. In both cases the lemma still
verifies, because it now constrains a different term than the prose claims.

**F14. Cost is not assurance — the most expensive lemma in the 4-party run is the
vacuous one.** `output_delivery_a_party_without_output` takes 15 / 170 / 1060 steps
in the 2- / 3- / 4-party runs (`results.txt:33,119,208`), i.e. it dominates the
scaling curve, and it is exactly the lemma that cannot fail (F1). Any table that
presents "steps" or "time" as a proxy for strength must exclude or fix it first.

## Checked and refuted (claims that did not survive the source)

* The 4-party output rules **do** bind the trusted party: `!TP(TP, G)` in
  `complexity_measures/4_party/MPC.spthy:218,236`. A claim that they accept
  injected messages as outputs is not supported by the rules.
* There is **no drift** between lemma names in `results.txt` and the sources — the
  generator reports "None" in `docs/LEMMA_INDEX.md`. The stale artifact is the
  separate file `complexity_measures/3_party/results.txt` (F9), not the names.
* `Eavesdrop` being guarded by `!Corrupted(receiver)` is defensible as a
  secure-channel model; what it does mean (F3) is that the privacy `*_hold`
  lemmas rest on that assumption rather than on protocol logic.


## What this PR changes (and does not)

Changed: `tests.py` (F10), `scripts/lemma_index.py` + `docs/LEMMA_INDEX.md`
(generated index: lemma counts 34/36/17/10 for the four attribute models,
35/47/50 for the 2/3/4-party complexity models, plus the recorded timings),
`README.md` (reproduction and artifact section), this file.

Deliberately **not** changed: any `.spthy` model or lemma. Every fix in P0/P1
changes either the model's semantics or the set of provable lemmas, so it must be
applied by the author with Tamarin at hand and the proofs re-run. The snippets
above are proposals, not patches.

This pass was made without a Tamarin binary (the reviewer's sandbox has none), so
every statement above is either a reading of the source or a quotation from the
recorded runs in `results.txt` — none of it is a fresh verification result.
