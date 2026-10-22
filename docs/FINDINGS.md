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
grep -n "Dep()\|Ind()" complexity_measures/4_party/*.spthy   # F2
grep -n -A2 "rule Eval_m:" complexity_measures/4_party/MPC.spthy  # F3
grep -n -A6 "rule Independence_of_inputs_3" complexity_measures/3_party/MPC.spthy  # F4
grep -n -A8 "rule RCV:" complexity_measures/2_party/MPC.spthy      # F5
grep -n "T_init(" */MPC.spthy complexity_measures/*/MPC.spthy | grep restriction -A2  # F6
python3 scripts/lemma_index.py && cat docs/LEMMA_INDEX.md          # F9
```

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

## P1 — modelling bugs that affect the scaling claim

**F4. The 4-party corruption threshold ignores the fourth party.**
`complexity_measures/4_party/MPC.spthy:100` guards `Eval_m` with
`_restrict(mal + mal << hmA + hmB + hmC)` — `hmD` is missing from the sum while
`HM(hmA, hmB, hmC, hmD)` and the argument tuple carry it. The honest/malicious
partition is therefore wrong exactly in the model used for the largest timing.

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

## What this PR changes (and does not)

Changed: `tests.py` (F10), `scripts/lemma_index.py` + `docs/LEMMA_INDEX.md`
(generated index: lemma counts 34/36/17/10 for the four attribute models,
35/47/50 for the 2/3/4-party complexity models, plus the recorded timings),
`README.md` (reproduction and artifact section), this file.

Deliberately **not** changed: any `.spthy` model or lemma. Every fix in P0/P1
changes either the model's semantics or the set of provable lemmas, so it must be
applied by the author with Tamarin at hand and the proofs re-run. The snippets
above are proposals, not patches.
