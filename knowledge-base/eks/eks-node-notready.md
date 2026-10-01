# EKS Node NotReady Troubleshooting Runbook

## Purpose

This runbook describes the troubleshooting procedure used by the
CloudOps team when an Amazon EKS worker node enters the NotReady state.

## Step 1 - Check Node Status

Run:

kubectl get nodes

Identify nodes reporting the NotReady status.

Then inspect the affected node:

kubectl describe node <node-name>

Review the Conditions section for MemoryPressure, DiskPressure,
PIDPressure, Ready status, and network-related errors.

## Step 2 - Check Kubelet

Connect to the worker node using the approved access method.

Check the kubelet service:

systemctl status kubelet

Review recent kubelet logs:

journalctl -u kubelet --since "30 minutes ago"

Look for authentication, certificate, networking, runtime, or resource
errors.

## Step 3 - Check EC2 Health

Verify that the EC2 instance backing the EKS node is running.

Review:

- EC2 instance status checks
- CPU utilization
- Memory pressure
- Disk availability
- Network connectivity

## Step 4 - Check EKS Networking

Verify that the node can communicate with the Kubernetes API server.

Review:

- Security groups
- Network ACLs
- Route tables
- DNS resolution
- VPC CNI status

Check the aws-node pods:

kubectl get pods -n kube-system -l k8s-app=aws-node

## Step 5 - Check Node Resources

Review node resource usage.

Check:

kubectl describe node <node-name>

Look for:

- MemoryPressure
- DiskPressure
- PIDPressure

Resource exhaustion can cause kubelet and container runtime failures.

## Step 6 - Check Kubernetes System Components

Review system pods:

kubectl get pods -n kube-system -o wide

Pay particular attention to:

- aws-node
- kube-proxy
- CoreDNS

## Escalation Rule

If the node remains NotReady after kubelet, networking, EC2 health,
and resource checks have been completed, collect the node description,
kubelet logs, relevant CloudWatch logs, and EC2 health information
before escalating the incident.
