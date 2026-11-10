# Latest investigation

See [investigation/findings.md](investigation/findings.md). Confirmed absent wsl-web-next backend behind active routes, with 288 target connection errors/minute, and a per-VU journey-selection bias in the test script. Local flow counter corrected; not load-retested. Do not equate absent Next.js with the two tested-page 502s: exact request attribution unavailable because ALB access logs are disabled. No infrastructure changes or extra load.

# Retest completed ? 10 November 2026

User requested retesting failed and incomplete load cases. Cluster credentials were used only in child-process environment, not saved in test files.

- Recovery smoke before spike: PASS, 90 requests, zero errors/drops.
- Same bounded 100-VU spike: FAIL again, 397 completed HTTP requests, zero HTTP errors, p95 3034.83 ms, 44 dropped iterations. Full peak/recovery aborted; do not claim successful capacity or a known root cause. No template rollout observed.
- Recovery smoke before endurance: PASS, 94 requests, zero errors/drops.
- Full endurance retest: PASS configured thresholds, 7,017 HTTP requests, p95 2280.56 ms, zero drops, two HTTP 502s (0.0285%). Homepage at 20:02:45 UTC / 22:02:45 Cairo; event-results at 20:05:04 UTC / 22:05:04 Cairo. No observed deployment-template changes or pod restarts; cause unconfirmed. Limited recent app logs did not show matching upstream diagnostics.
- Both failed behavior and intermittent 502s reproduced. Further work is diagnosis/fix and a subsequent retest; no ticket created or app/config changes made.
- Postflight 20:11:05 UTC: two Ready nodes, AWS desired=2, zero owned workloads; temporary own Basic Secret removed. All writes ca-test only, no Secret-value reads.

Evidence: [Retest outcome](retest/status.json), [502 diagnostics](retest/502-diagnostics.json), [Spike attempt](website-inregion/attempt-retest-spike/results.json), [Endurance attempt](website-inregion/results.json), [Postflight](postflight.json). Previous endurance evidence preserved in website-inregion/attempt-before-retest/. Latest table combines separate attempts, not a fresh full suite.

## Earlier completed run (historical)

# Current completed load-test outcome — 10 November 2026

Target: https://www.staging.worldsurfleague.com (redirecting to staging.worldsurfleague.com), legacy staging on eks-staging / us-west-2 / account 107275182030. The user authorized continuing with deployment overlap recorded.

| Profile | Result | HTTP requests | p95 ms | HTTP errors | Dropped iterations |
|---|---|---:|---:|---:|---:|
| smoke | PASS | 94 | 2365.94 | 0 | 0 |
| flows | PASS | 1504 | 2274.81 | 0 | 2 |
| spike | FAIL | 414 | 2757.94 | 0 | 47 |
| endurance | PASS | 7016 | 2286.47 | 1 | 0 |

Endurance completed the full 15-minute steady stage plus warm-up and cooldown (17 minutes overall). Its single homepage HTTP 502 occurred at 19:22:51 UTC / 21:22:51 Cairo; no deployment-template change was observed during this endurance attempt, so its cause remains unconfirmed. It passed the configured limits, not a zero-error requirement. This bounded run does not establish hours-long soak reliability.

The bounded spike failed at 100 preallocated/max VUs and 47 dropped iterations. It did not sustain the intended offered rate or complete the peak/recovery stages. Completed-request p95 does not include interrupted in-flight work. Do not infer full stress capacity or claim the spike passed.

Earlier baseline 502s overlapped two Varnish image rollouts (12342 to 12343 and 12343 to 12344). Those attempts and the initial generator-allocation failure are preserved separately; no raw failure was changed to PASS. The combined report selects latest results per profile across separate attempts/builds, not one fresh isolated suite run.

Namespace sandbox autoscaler verification separately passed: automatic 2 to 3 to 2 node cycle, 4,199 requests, zero errors, p95 62.77ms. Actual website-test nodes stayed at two; observed wsl-web replicas increased from two to three and later returned to two. No application HPA or autoscaler configuration was edited.

Postflight 2026-11-10T19:30:59.117Z: two Ready nodes, AWS desired capacity 2, no owned workload resources remain. Temporary test Basic Secret deletion was confirmed without a get/read of Secret values. All Kubernetes writes were limited to ca-test. No Jira or public publication changes.

Evidence: index.html, website-inregion/combined-results.json, individual raw result/summary/log files, resource samples, postflight.json and validation.json. Test source: ../../tests/performance/eks-autoscaler/legacy-website.js and ../../scripts/performance/run-legacy-staging-jobs.mjs. The AWS key disclosed in chat should be rotated after testing.

## Historical checkpoints below

# Load-test continuation status

## Verified
- eks-staging / us-west-2 / account 107275182030 access works.
- Isolated ca-test sandbox: 4,199 HTTP requests, no failures, p95 62.77ms. Autoscaler event and logs prove automatic node-group 2 to 3 scaling; two Ready nodes returned at 18:34:16 UTC.
- Latest in-region website smoke: 104 requests, no HTTP errors, p95 2241.09ms.
- Latest completed browsing flows: 1,504 requests, no HTTP errors, p95 2274.81ms, 2 dropped iterations (under configured threshold).
- Postflight 18:57 UTC: two Ready nodes, AWS desired=2, no owned ca-test workload resources remaining; owned temporary Basic Secret deletion confirmed without reading Secret values.

## Not yet validated
- Full spike peak and recovery: interrupted before completion. Two separate Varnish rollouts overlapped baseline requests and coincided with 502s. First rollout changed build 12342 to 12343 around 18:41 UTC; latest rollout changed 12343 to 12344 around 18:55 UTC. Latest request count 59, two errors, p95 632.41ms; raw FAIL retained. Do not describe this as demonstrated spike-induced capacity failure.
- One intervening spike attempt had 355 requests, zero HTTP errors, p95 2341.96ms, but 21 dropped iterations during dynamic VU allocation. Preallocate 100 spike VUs in the current script; this retains the same request-rate and abort thresholds. See Grafana arrival-rate allocation documentation.
- The 15-minute steady-load endurance stage has NOT RUN.

## Next step
The user was asked whether deployments can be paused for 25 minutes or whether testing should continue with deployment overlap reported. That answer is pending. Do not increase traffic merely to manufacture node growth. Keep all Kubernetes writes in ca-test and all application namespaces/nodes read-only. Preserve original attempts and use combined-results.json only as the latest-per-profile assessment across separate runs/builds.

After the user confirms the window/mode, rerun the website sequence with scripts/performance/run-legacy-staging-jobs.mjs. AWS credentials belong only in the execution environment; website Basic credentials are in ignored local secrets.properties (legacyStagingBasicUser / legacyStagingBasicPassword). The kubeconfig is isolated at .local/eks-tools/kubeconfig.json. The helper signs EKS tokens using the active process AWS credentials. No keys or passwords belong in artifacts.

Prepared profiles are in tests/performance/eks-autoscaler/legacy-website.js. Website target is https://www.staging.worldsurfleague.com, redirecting to the canonical staging host; both hosts are verified in cluster ingress. Public homepage-to-event-results and return-visitor flows only, no UI rendering or asset/video load.

No Jira issue, app configuration, HPA/autoscaler configuration, node-group configuration or public publication was changed. Temporary test resources were created and removed in ca-test only. Rotate the AWS key exposed in chat after testing.

## User decision and resumed run
The user chose to continue and report deployment overlap. Spike and endurance were resumed on the existing staging target with unchanged abort thresholds and 100 preallocated spike VUs. Earlier attempts remain archived. See the current website-inregion/results.json and combined-results.json for live status; the earlier pending-window section is historical.

## Latest bounded spike result
The resumed spike used 100 preallocated VUs and stopped at 47 dropped iterations, 414 HTTP requests, zero HTTP errors, completed-request p95 2757.94ms. Full peak hold/recovery was not completed. Raw results and assessment are preserved in website-inregion/attempt-spike-100vus/. A recovery smoke and independent endurance run were queued without relaxing thresholds.

## Corrected-flow rerun completed

22:29-22:32 Cairo: smoke PASS (112 requests, zero errors/drops); corrected-flow spike FAIL (562 completed requests, zero HTTP errors, p95 3103.53ms, 34 dropped iterations). Same 100-VU limit and arrival/abort settings; full peak/recovery aborted. No rollout observed. Cleanup verified two Ready nodes and zero owned resources. Previous endurance preserved in website-inregion/attempt-endurance-retest/.

## Root-cause follow-up

See investigation/root-causes.json and findings.md. Diagnostic spike 588 requests, 39 drops, zero HTTP errors; generator CPU below 0.1 sampled cores, canonical response waits occupy 100 VUs. Live Varnish idle close 5.003s vs ALB120s confirmed; probable 502 connection-reuse cause, not historically request-proven. Next.js routes lack backend; no deletion record in 30-day audit. Temporary diagnostic resources removed; two Ready nodes remain.
