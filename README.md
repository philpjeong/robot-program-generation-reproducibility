# Supplementary reproducibility package

This reproducibility package accompanies the manuscript *Task Specification and Review–Revision in LLM-Based Robot Program Generation: A Cross-Model Evaluation*. It gathers saved artifacts for the reported 7,600 condition outcomes. Its assembly and verification use existing files only.

## Obtain the complete package

Download **supplementary_reproducibility.zip** from the [GitHub Releases page](https://github.com/philpjeong/robot-program-generation-reproducibility/releases/latest) and extract it. Run the verification commands below from the extracted `supplementary_reproducibility/` directory.

The repository provides this guide, verification entry points, reference verification results, and licensing notices. The Release archive contains the complete folder structure: implementation, analysis inputs, provenance, case evidence, and `saved_records.zip`. Run the scripts from the extracted Release package, not from the repository checkout alone.

## Start here

`data/outcomes.json` identifies each model, condition, task, instruction/repetition case, final-program hash, task-prompt hash, and all-states outcome. The common comparison has 6,400 outcomes; the GPT-5.4 mini contract ablation adds 400 C0 outcomes and the eight-task evaluation adds 800 outcomes. The shared C1 outcomes are counted once.

`data/paired_review.json`, `resources.json`, and `static_gate.json` provide the program-level inputs for review transitions, token/cost/time summaries, and selective-review reconstruction. `candidate_inventory.json` contains the 400 saved Qwen C1 candidates behind sequential regeneration and oracle pass@k. Analysis plans and numerical reference outputs are alongside them.

Install NumPy in a Python environment, then run from this directory:

```
python reproduce.py
```

The command verifies outcome coverage, review transitions, the common initial-code fallback, resource sums, static routing, the contract sign-flip and exact McNemar tests, all 16 main contrasts and confidence intervals, the 16 selective contrasts and confidence intervals, sequential regeneration, oracle availability, both sequential comparison intervals, and the hashes of all 7,600 final records. It writes `verification_result.json`. It neither executes generated programs nor contacts a model or service. The original contract comparison reports the two tests; it did not report a bootstrap confidence interval.

`python reproduce.py --correlations` also reproduces all 64 task-characteristic correlations, permutation tests, and bootstrap intervals using the retained numerical functions and packaged task metadata. This option imports those functions without running their historical network-based entry point.

The original analysis implementations, plans, and seeds are in `reference/`. The portable command above reads the packaged paths and leaves original analysis artifacts unchanged. Reference scripts retain their historical project layout and are supplied for inspection; some original entry points include network or generation functions and should not be used to reproduce saved numerical summaries. `reproduce.py` invokes only arithmetic and saved-record readers.

## Exact research inputs

`implementation/base/roboeval_multiagent_pilot/ROBOEVAL_EXECUTION_CONTRACT_V1.md` is the full execution contract. `prompts_v4.py` defines the four role prompts and their rendering functions. `schemas_v4.py` defines specification and review JSON schemas; `contract_validator_v4.py` defines the static checker. Earlier prompt/schema modules are included only as import dependencies of the archived adapter, while the run plans identify the selected v4.5 prompt family.

`implementation/base/code_generation/prompt_prefix.py` and `prompt_suffix.py` supply the public API context and examples. `implementation/base/benchmark/` includes the simulator, trace logic, 16 public task definitions and eight study-task definitions. The task files contain their instructions and evaluation states. The study-task helper, reference programs, and evaluator freeze/correction records are included beside the adapter sources.

`implementation/run_plans/` separates the original dataset plans. The plans pin the prompt family, model identifier, role settings, contract hash, public-context hashes, and implementation hashes where recorded. The dated original OpenAI runs, Gemini batch adapter, and subsequent common extraction/review recovery are separate source artifacts. `implementation/qwen4096/` and `implementation/qwen_recovery/` contain the fixed local runtime and final extraction recovery. This structure preserves their distinct handling rather than presenting one adapter as if it had handled every call.

## Saved model outputs and execution records

`saved_records.zip` is a storage container within the package. `provenance/case_records.json` maps every reported outcome to its retained final record and original source hash. Each model record contains the retained responses, program histories, diagnoses and usage available for that path. Qwen's `_calls` journals also include the actual request messages and schema. Cloud records retain the model outputs and their usage, while provider-specific request construction is available in the corresponding adapter source; full on-wire payloads were not retained uniformly for every historical cloud request.

The container also includes original evaluation output files, final cloud recovery traces and request records, and the Qwen final evaluation, validation and extraction journals. Final records are selected by the outcome table's `evaluated_record` pointers when present. Older, superseded run variants and smoke experiments are excluded.

Some GPT-4.1 mini intermediate review histories are unavailable in the original retained records. Their final programs and outcomes are included; the missing histories remain identified as unavailable, and affected resource figures remain lower bounds. Gemini timing retains its original job-completion basis. These are the same measurement boundaries used in the manuscript.

`reference/outputs/20260928_methods/sampling_settings_provenance.json` distinguishes the author's sampling-setting statement from the retained request evidence. It preserves the example GPT-4.1 recovery payload's field coverage and hash, the recorded Qwen settings, and the limits of the historical cloud-request records. The associated `settings_evidence.json` retains the extracted experimental metadata.

`evidence/c4_exception/` documents the interrupted eight-task C4 case. The original three rejected response bodies and their usage were not fully retained; the generation log preserves their validation errors and response previews. The restart record and reported final program are included. `evidence/weatherpoll_case/` links the reported presence-check regression to its stored programs and state traces.

## Provenance and integrity

`provenance/file_manifest.json` records original source hashes and packaged hashes. `provenance/case_records.json` does the same for final model records. Personal root paths in metadata are replaced by `WORKSPACE`, `CODEBOTLER_ROOT`, `ARCHIVE_SOURCE`, or `QWEN_RUNTIME_ROOT`; original-byte hashes remain in the manifest. Two archived evaluator isolation checks use a username-independent `/home/*/.bashrc` sentinel. The generated programs, request/response journals, evaluation traces, and numerical analysis inputs are unchanged. Authentication files, API-key setup scripts, caches, model weights, unrelated experiment bundles, and personal correspondence are excluded. Selected text is checked for recognizable credential patterns during assembly.

## Licensing

The upstream CodeBotler/RoboEval license is reproduced in `LICENSE.codebotler`; see `NOTICE` for its scope and the machine-learning-training restriction. No new blanket license is assigned to the combined materials.

The repository and Release archive provide this manuscript's reproducibility materials; no DOI has been assigned.
