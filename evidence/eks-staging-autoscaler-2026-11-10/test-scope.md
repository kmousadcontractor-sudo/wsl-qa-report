# Confirmed staging autoscaler test

Cluster: eks-staging, us-west-2, account 107275182030. This supersedes the earlier WSL_STAGING account/cluster discovery.

All created resources are in ca-test. Nodes and kube-system are observed read-only; no Secret resource is read. No AWS capacity, autoscaler configuration, real application deployment or HPA is edited.

A temporary Node.js HTTP workload has CPU request 100m, limit 500m and one replica per node via required pod anti-affinity. Its HPA ranges from one to three replicas. In-cluster k6 sends 2 to 20 requests/sec for six minutes. A third replica cannot fit on the original two nodes, allowing the cluster autoscaler to provision a third node. This verifies HPA-to-pending-pod-to-node-autoscaler behavior in a sandbox, not WSL Pro response capacity.

After the load, the test Job, HPA, Deployment, ClusterIP Service and ConfigMap are deleted by exact name. Node return to two is observed rather than forced. AWS keys remain only in the execution environment, not in manifests or reports. The key disclosed in chat should be rotated.

The linked www.staging.worldsurfleague.com event-results page receives no load from this test.

Permission preflight: create deployments in ca-test=yes, create deployments in default=no. The permission-only check for get secrets in ca-test returned yes, broader than the supplied screenshot; no Secret objects were requested or read.
