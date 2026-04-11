# Git Commands Before Reading Code

Source: [piechowski.io/post/git-commands-before-reading-code](https://piechowski.io/post/git-commands-before-reading-code/) — Ally Piechowski, April 2026

Run these commands to diagnose project health before diving into code.
They reveal churn, risk hotspots, team dynamics, and stability patterns.

## 1. High-Churn Files

```sh
git log --format=format: --name-only --since="1 year ago" | sort | uniq -c | sort -nr | head -20
```

The 20 most-modified files in the past year.
Excessive churn often signals problematic code.
Cross-reference with bug hotspots for highest-risk areas.
A 2005 Microsoft Research study found churn-based metrics predicted defects more reliably than complexity metrics alone.

## 2. Team Composition

```sh
git shortlog -sn --no-merges
```

Ranks contributors by commit count. 60%+ concentration from one person indicates bus factor risk.
Add `--since="6 months ago"` to assess current maintenance capacity.

## 3. Bug Clusters

```sh
git log -i -E --grep="fix|bug|broken" --name-only --format='' | sort | uniq -c | sort -nr | head -20
```

Maps defect density by filtering bug-related commit messages.
Files appearing on both churn and bug lists are highest-risk.

## 4. Project Momentum

```sh
git log --format='%ad' --date=format:'%Y-%m' | sort | uniq -c
```

Commit counts by month.
Declining curves indicate momentum loss; sharp drops often correlate with key personnel departures.

## 5. Firefighting Patterns

```sh
git log --oneline --since="1 year ago" | grep -iE 'revert|hotfix|emergency|rollback'
```

Frequent reverts and hotfixes signal deployment process failures and underlying reliability issues.

## When to Use

- Reviewing an unfamiliar codebase or module for the first time.
- Assessing overall project health as context for a review.
- Identifying which files in a large diff deserve the most scrutiny.
- Commit message discipline affects reliability of these commands.
