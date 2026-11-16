# Activation Desk – Pipeline

How the workbench turns account facts into a status, picks where to intervene this week, and validates every change. Status is never stored: it is recalculated from the facts after every saved change.

**Colors:** purple = automatic rule or decision · blue = account status · teal = manager action · yellow = Triage and Nudge lanes (no slot used) · orange = rejected input · green = activated · gray = input and output.

## Pipeline 1 – Status (first match wins)

```mermaid
flowchart LR
    classDef rule fill:#B8ACFB,stroke:#7D6DD4,color:#231266
    classDef status fill:#A0C4FB,stroke:#6A8BBF,color:#14315E
    classDef done fill:#B3E65F,stroke:#84AC43,color:#2F440B
    classDef note fill:#DDDDD8,stroke:#A8A8A0,color:#434339

    a1(["Seeded accounts<br/>facts only"]):::note
    b1{{"First value done<br/>WITH evidence?"}}:::rule
    b2{{"Customer blocker<br/>open?"}}:::rule
    b3{{"Internal blocker<br/>open?"}}:::rule
    b4{{"Target date<br/>passed?"}}:::rule
    sAct(["Activated<br/>no intervention"]):::done
    sWait["Waiting on customer<br/>to Nudge lane"]:::status
    sBlk["Blocked – internal<br/>to slot ranking"]:::status
    sOver["Overdue<br/>to slot ranking"]:::status
    sOn(["On track<br/>monitor"]):::status

    a1 --> b1
    b1 -->|Yes| sAct
    b1 -->|No| b2
    b2 -->|Yes| sWait
    b2 -->|No| b3
    b3 -->|Yes| sBlk
    b3 -->|No| b4
    b4 -->|Yes| sOver
    b4 -->|No| sOn
```

**Flags** are shown next to the status: No owner, No next action, Past target. A passed target never changes *Waiting on customer*; it only adds the Past target flag.

## Pipeline 2 – Interventions and actions

```mermaid
flowchart TD
    classDef rule fill:#B8ACFB,stroke:#7D6DD4,color:#231266
    classDef status fill:#A0C4FB,stroke:#6A8BBF,color:#14315E
    classDef action fill:#81E7DE,stroke:#25B6A9,color:#0E4343
    classDef lane fill:#FFE86D,stroke:#CBB333,color:#574900
    classDef error fill:#FFB575,stroke:#CA7933,color:#542700
    classDef note fill:#DDDDD8,stroke:#A8A8A0,color:#434339

    iBlk["Blocked – internal"]:::status
    iOver["Overdue"]:::status
    iWait["Waiting on customer"]:::status

    subgraph C_pick ["Choose where to act"]
        c1{{"Owner known?"}}:::rule
        cTri["Triage<br/>assign owner, review"]:::lane
        c2["Score and rank<br/>rule, not a prediction"]:::rule
        c4{{"In top 2?"}}:::rule
        cInt["Intervention<br/>this week"]:::action
        cCap["Waiting for<br/>capacity"]:::action
        c5{{"Target date<br/>passed?"}}:::rule
        cRem["Nudge: Remind"]:::lane
        cEsc["Nudge: Escalate"]:::lane
    end

    subgraph D_act ["Act and validate"]
        d1["Manager acts<br/>action, blocker or evidence"]:::action
        d2{{"Input valid?"}}:::rule
        dErr["Reject and explain why"]:::error
        d3["Save and log"]:::action
    end

    r1(["Recalculate status<br/>back to Pipeline 1"]):::note
    e1(["Dashboard<br/>filters and lanes"]):::note

    iBlk --> c1
    iOver --> c1
    iWait --> c5
    c1 -->|No| cTri
    c1 -->|Yes| c2
    c2 --> c4
    c4 -->|Yes| cInt
    c4 -->|No| cCap
    c5 -->|No| cRem
    c5 -->|Yes| cEsc
    cTri --> d1
    cInt --> d1
    cCap --> d1
    cRem --> d1
    cEsc --> d1
    d1 --> d2
    d2 -->|No| dErr
    dErr --> d1
    d2 -->|Yes| d3
    d3 --> r1
    d3 --> e1
```

### Priority score (0–100) – an explainable rule, not a prediction

Only accounts our team can unblock are scored. Customer-blocked accounts and accounts without an owner stop at a gate (Nudge lane or Triage) and never take an intervention slot.

| Component | Measures | Points |
|---|---|---|
| Urgency | Deadline consumption = (today − start) ÷ (target − start) | Overdue 50 · Critical (80%+ or ≤ 1 day left) 40 · Attention (50–80%) 20 · Comfortable (under 50%) 0 |
| Stagnation | Days the oldest internal blocker has been open | 0–2 days 0 · 3–5 days 10 · 6+ days 20 |
| Closeness to value | Pending activity milestones | 0 pending 20 · 1 pending 10 · 2+ pending 0 |
| Follow-up | Next action missing or follow-up date passed | 10 |

- **Tie-break:** urgency, then stagnation, then account name.
- **Unknown data** scores 0 and is shown as "not calculated", never estimated.
- **Fewer than 2 eligible accounts:** the slot stays empty with a message.

### Nudge lane

Customer-blocked accounts get a nudge level instead of points: **Remind** while the target is ahead, **Escalate** (customer owner + sponsor, propose a new target) once it has passed. The queue is ordered by deadline consumption. The app records the nudge; it never sends messages.

### Validation

Rejected with a clear message:

- activation without evidence, or not via the agreed workflow
- next action without owner or follow-up date
- customer blocker closed without a (simulated) customer update
- target date before start date

Resolving a blocker never activates an account. Only evidence does.
