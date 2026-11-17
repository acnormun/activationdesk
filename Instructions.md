# Customer activation workbench – Instructions

## Customer, users and situation

Your fictional customer sells invoice-approval software to business finance teams. The buyer is the head of customer success. The primary user is an onboarding manager with six new accounts and capacity to actively unblock two this week. A customer's finance lead owns some dependencies, simulated through recorded updates. Today a shared checklist says tasks are complete but does not show whether customers have actually reached a useful outcome.

For a starting definition, **first value** means the customer's finance owner has successfully approved a representative invoice through the agreed workflow. You can propose another concrete definition if you explain it. Importing data or finishing a training session alone does not establish first value. You are building the onboarding team's workbench, not the customer's invoice-processing product.

## Starting cases

Seed six accounts; dates and days are relative to the sample day.

- **Alpha:** target in 3 days, setup/training done, no representative invoice approved; needs an internal specialist to fix a sample-data mapping issue.
- **Beta:** target in 2 days, import done, customer's finance lead has not provided the required approval policy; internal team cannot resolve this alone.
- **Gamma:** target today, first representative invoice approved by finance owner yesterday; activation evidence is recorded.
- **Delta:** target in 7 days, setup incomplete, an internal owner has work scheduled tomorrow and no current blocker.
- **Epsilon:** target missed 5 days ago, no first value, owner and next action unknown.
- **Zeta:** target tomorrow, training done, customer disputes whether the sample workflow matches their real approval process; activation is not verified.

Use milestones, owners and meaningful evidence, not a percentage checklist alone. Choose an explainable approach to prioritizing two interventions.

## Core workflow to build

1. Inspect each account's desired outcome, target, value milestone, evidence, owner and blocker/dependency; distinguish first value from activity completed.
2. Decide where to intervene and record a next action, owner and follow-up.
3. Update a milestone, record/resolve a blocker or confirm first value with evidence. Make the resulting state and remaining dependencies clear.
4. Preserve changes after reload; activated accounts should be distinguishable from stalled accounts, including when no accounts match a chosen filter.

## Decisions and checks we want to see

- Explain urgency, unblockability and the customer's responsibilities.
- Avoid labeling Beta's external dependency as fixed simply because an internal task was checked.
- Check an activation claim without evidence, a missing action owner and an account that becomes activated.
- Demonstrate Alpha versus Beta, then verify Gamma does not look like unfinished onboarding.
- A proposed metric could be time to verified first value; define its start/end and explain why completed task count is insufficient.

## Outside scope

- No real customer invoice engine
- CRM/calendar integration
- Messaging
- Multi-user permissions
- Implementation of the customer-owned dependency

## Shared scope and delivery

Aim for 3–5 focused hours within the 48-hour submission window. Build one small, finished workflow, not a full enterprise product. Choose any stack. AI tools and coding agents are encouraged; explain their contribution, your changes and your personal checks. An AI feature, predictive model or paid external API is optional. Simple, explainable rules are sufficient. No prior industry expertise is expected.

Use the fictional scenario and sample cases as a starting point. You may clarify assumptions, add records or simplify secondary details, but retain the competing priorities and incomplete information. State your rules and assumptions so a reviewer can distinguish an intentional product decision from an implementation error. There is no prescribed ranking or visual layout. Do not turn missing information into a fabricated fact or present a rule-based score as a prediction.

Provide a public, deployed prototype and a public repository. A reviewer should be able to open the app, explore seeded records and complete the core workflow without importing data or configuring external services. Include the useful context, an understandable decision/action and visible confirmation. Handle a meaningful exception and an empty or no-matching-results state. Use readable hierarchy, labeled controls, keyboard-accessible actions and clear validation. Prioritize a usable core experience over extra screens or elaborate branding.

Changes must survive a page reload; browser storage is acceptable if explained. Authentication, real multi-user permissions, billing, integrations and production-scale infrastructure are outside scope. You may simulate a second actor or an approval; clearly label the simulation. If login is present, provide demo-only credentials in submission notes. Use synthetic data, never real customer records, production passwords or API secrets. A short walkthrough recording is optional.

## README and verification

Briefly explain the buyer, primary user, business outcome, workflow replaced, important trade-off, one proposed success metric and what you deliberately left out. Explain how you would measure the metric; do not claim actual revenue, savings or customer research that the prototype has not demonstrated.

Include local setup, key engineering choices, what you tested, known limitations and next steps. Provide a short reviewer walkthrough using the seeded cases. Check the deployed core flow, saved changes after reload, invalid input and the important rule/calculation boundaries. Relevant automated checks are welcome; a concise, reproducible manual checklist is also useful. State what remains untested. We review the working product, product judgment, engineering judgment, verification and ownership, not code volume or the number of tools used.