# Alignment: <effort name>

Artifact directory: <dir>

## Stages entered

| Stage | Date entered | Session note |
| ----- | ------------ | ------------ |

## Purpose

- Question: <what formal methods must answer>
- Decision it informs: <what the user will do with the answer>
- Mode: find bugs | establish assurance

## Requirements

Source: \<path to prose specs, or "this file">

| ID  | Requirement (cite, or state in prose when this file is the source) |
| --- | ------------------------------------------------------------------ |

## Decision (stage 1)

- Outcome: formal verification | not a fit
- Tool and verified object: <tool>; model | shipped code | translation
- Reason: \<property kind, cost of failure, why cheaper instruments do not cover it>
- If not a fit: the instrument recommended instead, and why

## Properties and trace (stage 2)

| Property | Statement file and name | Requirement ID | Origin (user, derived from code, published spec) |
| -------- | ----------------------- | -------------- | ------------------------------------------------ |

Requirements with no property:

| Requirement ID | Reason not covered |
| -------------- | ------------------ |

Omissions from the model (what it leaves out, and why):

## Validation and approvals (stage 3)

Back-translation: <output file>

| Can-fail check | Expected | Observed | Output file |
| -------------- | -------- | -------- | ----------- |

| Statement files | Approved commit | Approver | Route (read, back-translation) | Date |
| --------------- | --------------- | -------- | ------------------------------ | ---- |

## Results (stage 4)

| ID  | Verified object | Tool and version | Command | Commit | Covered paths | Bounds | Assumptions | Output file | Audit | Status (current, stale, retired) |
| --- | --------------- | ---------------- | ------- | ------ | ------------- | ------ | ----------- | ----------- | ----- | -------------------------------- |

## Findings (find-bugs mode)

| Finding | Requirement ID | Reproduction | Output file | User decision |
| ------- | -------------- | ------------ | ----------- | ------------- |

## Connection to code (stage 5)

| Result ID | Method | Direction | Covered code paths | Output file | What it cannot see |
| --------- | ------ | --------- | ------------------ | ----------- | ------------------ |

## Elective checks

| Check | Ran (yes, no) | Output file |
| ----- | ------------- | ----------- |
