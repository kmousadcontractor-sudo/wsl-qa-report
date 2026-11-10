# Investigation - 10 November 2026

Read-only cluster/AWS investigation completed around 22:24 Cairo. No additional traffic or infrastructure changes were made. Only the local k6 journey-selection code was corrected.

## Confirmed: routes point to an absent Next.js backend

The ingress routes /api/, /_next/, /static/, and /next/ on staging.worldsurfleague.com to wsl-web-next. Its service exists, but there are no endpoints, pods, or deployment under that name. Both registered node targets fail health checks. Target-group CloudWatch metrics from 21:45-22:15 Cairo show 8,640 unsuccessful target connections: 288 per minute, including periods outside the spike. This establishes a broken route/backend state; whether Next.js was intentionally retired needs the app owner's confirmation. Restore the intended backend or remove/update obsolete routes through the app/infrastructure owner. These routes were NOT requested by our HTTP-only load script, so do not attribute its two page errors to this finding.

## Confirmed: k6 journey selection was biased during ramp-up

The script used __ITER, a per-VU iteration count. Every newly active VU starts at zero and took the returning-visitor branch. Saved spike checks show 100 completed returning-visitor checks versus only 19 completed home-to-results iterations, plus interrupted work. This was not the intended 20% returning / 80% home-to-results distribution. The local script now uses exec.scenario.iterationInTest to assign the mix across started scenario iterations. A complete block of 100 IDs assigns 20 returning and 80 home-to-results. Existing failures are preserved; the corrected script was rerun: smoke PASS (112 requests, no errors/drops); spike FAIL (562 completed HTTP requests, no HTTP errors, p95 3103.53ms, 34 dropped iterations). Peak/recovery again aborted at the unchanged limit. No rollout was observed. Completion mix can still differ if journeys fail or abort.

## Corrected-flow rerun

At 22:29-22:32 Cairo the corrected script was rerun with the same 100 preallocated/max VUs and unchanged arrival/abort limits. Smoke passed; spike still failed. This disproves the journey counter as the sole explanation for dropped iterations. No successful peak/recovery capacity is established. Cleanup at 22:32 Cairo verified two Ready nodes, desired capacity two, and zero owned resources. [Corrected-flow evidence](evidence.json).

## Earlier spike saturation: symptom established, root cause unresolved

The 100-VU limit was reached at 21:51:08 Cairo; the dropped-iteration threshold aborted at 21:51:11. There were 44 dropped iterations, 397 completed HTTP requests and no HTTP errors. Completed-iteration p95 was 6.47 seconds; at 20 arrivals/second, even this completed-sample duration corresponds to about 129 concurrent iterations, exceeding 100. This is a rough sizing comparison, not a distribution model: interrupted iterations are excluded, and the test aborted during ramp-up. Average node CPU sampled after the abort was 26%/19%; Varnish used 54m of its 125m cap, web pods 763m/569m of their 1800m caps. These coarse samples cannot rule out brief throttling, generator saturation or request queues. No historical generator CPU/throttling series was captured. Do not claim node CPU exhaustion or prove maximum server capacity. After correcting flow assignment, repeat a bounded diagnostic with per-route timings, active iterations, and fast generator/app CPU-throttling measurements before changing VUs or resource limits.

## Two page-level 502s: reproduced, exact cause unresolved

Endurance errors occurred at 22:02:45 Cairo on canonical homepage and 22:05:04 on www event-results. No rollout or pod restart was observed. The Varnish target group is currently healthy and reports no target-generated 5xx or target connection failures during the queried window. Shared ALB metrics show ELB-generated errors but are dominated by the absent Next.js backend; they cannot identify these two requests. ALB access logs are disabled. Varnish stdout had no entries; bounded and wider Apache log scans did not reveal a matching fatal/upstream diagnostic. This evidence is insufficient to choose between connection reuse/reset, invalid response or another gateway cause. Next step is owner-enabled ALB access logs and Varnish request diagnostics, followed by a correlated low-rate reproduction. No logging settings were changed.

## Evidence and reference definitions

- [Routing and resource limits](evidence.json)
- [Absent Next.js backend](evidence.json)
- [Per-target-group CloudWatch metrics](evidence.json)
- [Shared load-balancer metrics and disabled log attributes](evidence.json)
- [Application log analysis](evidence.json)
- [Original spike assessment](evidence.json)
- [AWS metric definitions](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-cloudwatch-metrics.html): ELB 502 metrics identify load-balancer-originated responses; target connection failures count unsuccessful backend connection establishment.
- [Grafana execution variables](https://grafana.com/docs/k6/latest/using-k6/execution-context-variables/) and [scenario iteration counter](https://grafana.com/docs/k6/latest/javascript-api/k6-execution/).
