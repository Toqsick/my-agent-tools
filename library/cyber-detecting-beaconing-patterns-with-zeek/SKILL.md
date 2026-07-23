---
name: cyber-detecting-beaconing-patterns-with-zeek
title: Detecting Beaconing Patterns With Zeek
version: '1.0'
description: 'Performs statistical analysis of Zeek conn.log connection intervals to detect C2 beaconing patterns. Uses the
  ZAT library to load Zeek logs into Pandas DataFrames, calculates inter-arrival time standard deviation, and flags periodic
  connections with low jitter. Use when hunting for command-and-control callbacks in network data.

  '
category: cybersecurity
author: kyssta-exe/skills (curated by Yuno)
license: Apache-2.0
lane: security
agent: yuno
trigger_keywords:
- detecting-
- beaconing-
- patterns-with-
- zeek
- performs
keywords:
- detecting-
- beaconing-
- patterns-with-
- zeek
- performs
- statistical
- analysis
- conn
related_skills:
- cyber-analyzing-ransomware-network-indicators
- cyber-performing-static-malware-analysis-with-pe-studio
- cyber-performing-endpoint-forensics-investigation
- cyber-implementing-network-traffic-baselining
last_curated: '2026-07-23'
curated_by: yuno-kyssta-import-2026-07-23
subdomain: security-operations
domain: cybersecurity
mitre_attack:
- T1071.001
- T1071.004
- T1573
- T1008
- T1095
nist_csf:
- DE.CM-01
- RS.MA-01
- GV.OV-01
- DE.AE-02
tags:
- network-security
- zeek
- c2-beaconing
- conn-log-analysis
- zat
- threat-hunting
- statistical-analysis
---


# Detecting Beaconing Patterns with Zeek


## When to Use

- When investigating security incidents that require detecting beaconing patterns with zeek
- When building detection rules or threat hunting queries for this domain
- When SOC analysts need structured procedures for this analysis type
- When validating security monitoring coverage for related attack techniques

## Prerequisites

- Familiarity with security operations concepts and tools
- Access to a test or lab environment for safe execution
- Python 3.8+ with required dependencies installed
- Appropriate authorization for any testing activities

## Instructions

Load Zeek conn.log data using ZAT (Zeek Analysis Tools), group connections by
source/destination pairs, and compute timing statistics to identify beaconing.

```python
from zat.log_to_dataframe import LogToDataFrame
import numpy as np

log_to_df = LogToDataFrame()
conn_df = log_to_df.create_dataframe('/path/to/conn.log')

# Group by src/dst pair and calculate inter-arrival time
for (src, dst), group in conn_df.groupby(['id.orig_h', 'id.resp_h']):
    times = group['ts'].sort_values()
    intervals = times.diff().dt.total_seconds().dropna()
    if len(intervals) > 10:
        std_dev = np.std(intervals)
        mean_interval = np.mean(intervals)
        # Low std_dev relative to mean = likely beaconing
```

Key analysis steps:
1. Parse Zeek conn.log into DataFrame with ZAT LogToDataFrame
2. Group connections by source IP and destination IP pairs
3. Calculate inter-arrival time intervals between consecutive connections
4. Compute standard deviation and coefficient of variation
5. Flag pairs with low coefficient of variation as potential beacons

## Examples

```python
from zat.log_to_dataframe import LogToDataFrame
log_to_df = LogToDataFrame()
df = log_to_df.create_dataframe('conn.log')
print(df[['id.orig_h', 'id.resp_h', 'ts', 'duration']].head())
```


