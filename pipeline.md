# Activation Desk – User journey and pipelines

Read in this order: **1. User journey → 2. Login and access → 3. Rules flow**. Status is never stored: it is recalculated from the account facts after every saved change.

**Colors:** cyan = screen the user sees · purple = automatic rule or decision · blue = account status · teal = user action · yellow = Triage and Nudge lanes (no slot used) · orange = rejected input or blocked access · green = activated or saved · gray = start, end and input.

## 1. User journey

The onboarding manager is the only user of the app. Customers and the head of CS do not log in.

### Onboarding manager (Ana): unblock 2 accounts this week and verify first value

```mermaid
flowchart LR
    classDef screen fill:#9CE6FF,stroke:#4FB1D3,color:#1C4657
    classDef action fill:#81E7DE,stroke:#25B6A9,color:#0E4343
    classDef rule fill:#B8ACFB,stroke:#7D6DD4,color:#231266
    classDef error fill:#FFB575,stroke:#CA7933,color:#542700
    classDef done fill:#B3E65F,stroke:#84AC43,color:#2F440B
    classDef note fill:#DDDDD8,stroke:#A8A8A0,color:#434339

    m1(["Log in as Ana<br/>onboarding manager"]):::note
    m2["Dashboard<br/>6 accounts, computed status<br/>Activated, Stalled, On track"]:::screen
    m3["This week<br/>2 slots with reasons<br/>Triage, Nudge, Monitor"]:::screen
    m4["Account detail<br/>outcome, target, milestones<br/>evidence, blockers, log"]:::screen
    m5{{"What does the<br/>account need?"}}:::rule
    a1["Next action<br/>owner + follow-up"]:::action
    a2["Assign owner<br/>and review"]:::action
    a3["Record nudge<br/>Remind or Escalate"]:::action
    a4["Update milestone<br/>or blocker"]:::action
    a5["Record evidence<br/>who, invoice, when"]:::action
    a6["Record customer update<br/>labeled Simulated"]:::action
    m6{{"Input valid?"}}:::rule
    m7["Error says<br/>what to fix"]:::error
    m8["Saved with confirmation<br/>status recalculated"]:::done
    m9(["Dashboard updates<br/>plan, counters, filters"]):::note

    m1 --> m2
    m2 --> m3
    m3 --> m4
    m4 --> m5
    m5 -->|Slot| a1
    m5 -->|Triage| a2
    m5 -->|Nudge| a3
    m5 -->|Progress| a4
    m5 -->|Value reached| a5
    m5 -->|Customer replied| a6
    a1 --> m6
    a2 --> m6
    a3 --> m6
    a4 --> m6
    a5 --> m6
    a6 --> m6
    m6 -->|No| m7
    m7 --> m5
    m6 -->|Yes| m8
    m8 --> m9
```

### Customer finance lead: simulated, no login

The manager records customer-side blockers (side = customer) after a call or an email. When the customer delivers (for example, Beta sends the approval policy), she clicks **Record customer update (simulated)** on that blocker. It is the only way to close a customer blocker, and the log shows it as *Simulated*. Checking an internal task never closes it.

### Head of CS: the buyer, no login

Appears in the README as the buyer. Follows the outcome through the success metric: time to verified first value, plus the share of non-activated accounts that are Critical or Overdue. A read-only view for this role is a possible next step, not part of the prototype.

## 2. Login and access

### Pipeline 0 – Access and request flow (FastAPI)

One demo login: the onboarding manager. Every request checks the session, then the domain rules.

```mermaid
flowchart TD
    classDef rule fill:#B8ACFB,stroke:#7D6DD4,color:#231266
    classDef status fill:#A0C4FB,stroke:#6A8BBF,color:#14315E
    classDef action fill:#81E7DE,stroke:#25B6A9,color:#0E4343
    classDef error fill:#FFB575,stroke:#CA7933,color:#542700
    classDef note fill:#DDDDD8,stroke:#A8A8A0,color:#434339

    u1(["Manager opens the Vue app"]):::note

    subgraph L_login ["Login - one demo user"]
        l1["Login page<br/>demo credentials shown"]:::action
        l2{{"Email and password<br/>match the demo user?"}}:::rule
        lErr["401: wrong email or password"]:::error
        l3["Issue session token<br/>httpOnly cookie, short expiry"]:::rule
        l4["Clone seed into a demo<br/>workspace for this session"]:::rule
    end

    subgraph R_req ["Every API request - FastAPI"]
        r1{{"Session valid?"}}:::rule
        rErr1["401: back to login"]:::error
        r4{{"Read or write?"}}:::rule
    end

    subgraph W_write ["Write path"]
        w1{{"Domain rules pass?"}}:::rule
        wErr["422: reject and explain"]:::error
        w2["PostgreSQL transaction<br/>change + log entry<br/>actor, simulated flag"]:::action
    end

    s1["Recalculate status<br/>Pipeline 1"]:::status
    o1(["JSON response to Vue"]):::note

    u1 --> l1
    l1 --> l2
    l2 -->|No| lErr
    l2 -->|Yes| l3
    l3 --> l4
    l4 --> r1
    r1 -->|No| rErr1
    r1 -->|Yes| r4
    r4 -->|Read| s1
    r4 -->|Write| w1
    w1 -->|No| wErr
    w1 -->|Yes| w2
    w2 --> s1
    s1 --> o1
```

### Who does what (one demo user: the onboarding manager)

| Action | How it works in the app |
|---|---|
| See all 6 accounts and this week's plan | Dashboard with computed status, slots and lanes |
| Update an activity milestone | Manager records progress, even when the customer did the task |
| Record a blocker | Manager picks the side: internal or customer |
| Close an internal blocker | Manager records the internal fix |
| Close a customer blocker | Manager records the customer update, labeled Simulated. The only way to close it |
| Record next action | Owner and follow-up date required |
| Confirm first value | Manager records evidence: who approved, which invoice, when, via the agreed workflow |
| Reset demo data | Restores the 6 seeded accounts |

**Demo-only access, not production auth:** one seeded user (the onboarding manager), password hashed, credentials in the submission notes and on the login page. Each login gets its own demo workspace cloned from the seed, so reviewers never overwrite each other; reset restores the seed. Out of scope: other roles, sign-up, password reset, user management, permissions.

## 3. Rules flow

### Pipeline 1 – Status (first match wins)

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

### Pipeline 2 – Interventions and actions

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
- customer blocker closed without a recorded (simulated) customer update
- target date before start date

Resolving a blocker never activates an account. Only evidence does.