# Operational Exception Escalation SOP

## 1. Purpose
This procedure defines the operational lifecycle and escalation hierarchy for resolving data quality exceptions and reconciliation variances detected by the automated banking pipeline.

## 2. Exception Lifecycle States
1. **OPEN**: Exception newly logged by automated PySpark / Python DQ engines.
2. **UNDER_REVIEW**: Assigned to a Data/Information Operations Analyst for root-cause analysis.
3. **RESOLVED**: Corrective patch applied or transaction re-processed.
4. **REJECTED**: Exception marked as false positive or within acceptable business tolerance.

## 3. Escalation Tiers & Response Timelines
[ Automated Pipeline Engine ]
│
▼
(audit.dq_exception_log)
│
┌──────────┴──────────┐
▼                     ▼
[ HIGH Severity ]    [ MEDIUM / LOW Severity ]
│                     │
▼                     ▼
Tier 2 Support       Tier 1 Support
(SLA: 2 Hours)       (SLA: 24 Hours)


### Tier 1: Operations Analyst (SLA: 24 Hours)
* **Scope**: Medium and Low severity exceptions (e.g., `DQ_003` missing non-critical customer metadata, minor amount variances < \$10.00).
* **Action**: Verify source landing file formatting, notify source system owner, and update `resolution_status` to `RESOLVED` once rectified.

### Tier 2: Senior Data Operations & Risk Lead (SLA: 2 Hours)
* **Scope**: High severity exceptions (e.g., `DQ_001` duplicate transaction batches, `DQ_002` missing foreign keys, settlement variances > \$1,000.00).
* **Action**: Pause downstream batch processing if batch corruption exceeds 1% threshold. Issue incident ticket and perform manual ledger reconciliation.