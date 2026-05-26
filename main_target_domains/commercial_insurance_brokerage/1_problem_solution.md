## Problem: split client files

The first problem is that the broker’s official client record may sit in the BMS, while the live working file is scattered across Outlook, Teams, SharePoint, OneDrive, insurer portals, PPL records, PDFs, spreadsheets and personal folders. The stated impact is search time, duplicate work, missed instructions, slower file review and E&O/audit risk. 

For a **50-person commercial broking team**, this is a strong candidate for AI-assisted automation because the cost is largely fixed, while the benefit scales across every account handler, executive, claims handler, renewals colleague and compliance reviewer affected by fragmented files.

## Proposed solution: AI-assisted client file control

Create a **single client file control layer** that automatically gathers, labels and reconciles key documents and messages from the places staff already use.

The goal is **not** to replace the BMS. The BMS remains the official policy, client and accounting record. The AI-supported workflow sits around it and makes sure that important working documents and communications are visible, correctly filed and traceable.

For a 50-person team, the solution should be priced as:

| Cost item                     |           Amount |
| ----------------------------- | ---------------: |
| One-time implementation price |      **£35,000** |
| Monthly maintenance           | **£1,200/month** |
| First-year maintenance        |      **£14,400** |
| **Total year-one cost**       |      **£49,400** |
| Year-two onward cost          | **£14,400/year** |

This is a fixed-scope project model, not a large recurring integration programme.

## What the solution would do

| Function                                                                               | Practical outcome                                                                                                                 |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Identify client, policy and renewal references in emails, documents and portal outputs | Documents are attached to the right client/policy file or sent to the correct review queue                                        |
| Classify documents                                                                     | Quote, schedule, statement of fact, client instruction, underwriter clarification, certificate, endorsement, claim evidence, etc. |
| Detect “important but unfiled” items                                                   | Example: client acceptance in an email thread or underwriter subjectivity in Outlook                                              |
| Produce a file timeline                                                                | Shows what happened, who sent it, when, and where the evidence sits                                                               |
| Flag inconsistencies                                                                   | Example: latest schedule in SharePoint differs from the schedule stored in the BMS                                                |
| Create missing-evidence alerts                                                         | Example: “client acceptance found in email but not saved to official file”                                                        |
| Support search in plain English                                                        | Example: “show the latest underwriter clarification for ABC Manufacturing renewal”                                                |
| Produce team-level exception reports                                                   | Shows unresolved filing gaps, uncertain matches and missing-evidence risks by team                                                |

## Recommended operating model

Use a **controlled automation workflow as the core**, with **narrow AI support for interpretation**.

A fully autonomous AI agent is not the right primary design for this problem because the broker needs predictable control, auditability and low operational risk. The process involves regulated records, client instructions, policy evidence and potential E&O exposure. A controlled workflow is better because each step is measurable, repeatable and auditable.

AI support is still useful, but only for judgement-heavy tasks such as reading documents, recognising client instructions, spotting conflicting versions and summarising file history. The final record movement, alerts and approvals should follow a fixed workflow.

**Best-fit design:**
**85% structured workflow + 15% AI interpretation.**

This gives the business the benefit of AI without allowing it to make uncontrolled file-management decisions.

## Target workflow

### 1. Trigger

A new email, document, Teams file, SharePoint upload or portal output appears.

Examples:

| Source             | Example item                                                             |
| ------------------ | ------------------------------------------------------------------------ |
| Outlook            | Client acceptance, underwriter clarification, quote revision             |
| SharePoint / Teams | Updated property schedule, fleet list, claims history, statement of fact |
| OneDrive           | Locally saved client document that should be in the working file         |
| Portal output      | Quote, endorsement, revised schedule, certificate                        |
| BMS reference list | Client name, policy number, renewal date, insurer, handler               |

### 2. AI review

The AI reads the item and identifies:

| Data point       | Example                                                                             |
| ---------------- | ----------------------------------------------------------------------------------- |
| Client name      | ABC Manufacturing Ltd                                                               |
| Policy reference | COM/123456                                                                          |
| Insurer          | Aviva, AXA, Zurich, etc.                                                            |
| Document type    | Quote, schedule, certificate, instruction, endorsement                              |
| Transaction type | Renewal, MTA, new business, claim, complaint                                        |
| Importance       | Client instruction, underwriter condition, acceptance, declinature, material change |

### 3. Automatic filing recommendation

The item is matched to the likely client and policy file.

The system should not initially make unrestricted changes to the official BMS record. Instead, it should:

| Action                        | When used                                                                         |
| ----------------------------- | --------------------------------------------------------------------------------- |
| Recommend filing              | Standard items with a clear client/policy match                                   |
| Auto-route to review queue    | Items that look important but need human confirmation                             |
| Flag missing evidence         | Where an instruction, acceptance or subjectivity exists outside the official file |
| Create a file note suggestion | Where a summary would help the handler or reviewer                                |

### 4. Confidence check

| Confidence level | Action                                                                                 |
| ---------------- | -------------------------------------------------------------------------------------- |
| **90%+**         | File automatically or prepare for one-click confirmation, depending on internal policy |
| **70–89%**       | Send to handler for one-click confirmation                                             |
| **Below 70%**    | Leave unfiled and place in a review queue                                              |

This keeps the process controlled and avoids incorrect filing.

### 5. Risk flags

The system highlights items such as:

| Risk flag                                          | Example                                                              |
| -------------------------------------------------- | -------------------------------------------------------------------- |
| Client instruction not stored in the official file | Client confirms reduced cover by email, but BMS file has no evidence |
| Underwriter clarification outside the BMS          | Underwriter confirms a subjectivity in Outlook only                  |
| Newer document version outside the BMS             | SharePoint schedule is newer than BMS schedule                       |
| Missing evidence for acceptance                    | Quote accepted in Teams/email but not visible to reviewer            |
| Changed cover not clearly evidenced                | Renewal terms differ from expiring policy but explanation is missing |
| File close to renewal with weak evidence           | Renewal approaching with incomplete exposure update                  |

### 6. Daily exception report

Account handlers and team leads receive only exceptions, not another general inbox.

For a 50-person team, the report should show:

| Report item                     | Purpose                                                           |
| ------------------------------- | ----------------------------------------------------------------- |
| Unmatched documents             | Prevents evidence being lost                                      |
| Medium-confidence matches       | Allows fast human confirmation                                    |
| High-risk items                 | Focuses attention on instructions, acceptances and subjectivities |
| Files with conflicting versions | Prevents staff relying on outdated documents                      |
| Missing-evidence alerts         | Supports file review and compliance                               |
| Team-level statistics           | Helps managers spot process problems                              |

## Implementation scope for a 50-person team

### Included in the fixed project

| Workstream              | Included                                                                                       |
| ----------------------- | ---------------------------------------------------------------------------------------------- |
| Workflow design         | Define document categories, file-matching rules and exception logic                            |
| Source setup            | Outlook, SharePoint, Teams and a client/policy reference list from the BMS                     |
| AI document reading     | Identify client name, policy reference, insurer, document type and instruction type            |
| Filing recommendation   | Suggest the right client/policy location                                                       |
| Exception queue         | Send uncertain or high-risk items to handlers                                                  |
| Missing-evidence alerts | Flag client acceptance, underwriter subjectivity, changed terms and important unfiled evidence |
| Basic reporting         | Weekly count of filed items, exceptions and unresolved evidence gaps                           |
| Staff training          | Practical training for handlers, executives and team leads                                     |
| Testing and tuning      | Accuracy testing on real broker documents                                                      |

### Excluded from the first version

| Excluded item                      | Reason                                            |
| ---------------------------------- | ------------------------------------------------- |
| Full BMS write-back                | Higher cost and higher audit risk                 |
| Insurer portal integrations        | Adds complexity; not needed to prove value        |
| Historic file clean-up             | High volume, weak immediate ROI                   |
| Complex management dashboards      | Start with simple exception reporting             |
| Fully autonomous document movement | Too risky before accuracy is proven               |
| All process areas at once          | Start with renewals, MTAs and client instructions |

This keeps the project fixed in scope and commercially credible.

## Cost estimate for 50-person team

| Cost area                               | One-time estimate |
| --------------------------------------- | ----------------: |
| Process mapping and document categories |          Included |
| Client/policy matching rules            |          Included |
| AI document/email classification setup  |          Included |
| Review queue and exception alerts       |          Included |
| Testing, tuning and staff training      |          Included |
| Light governance/compliance review      |          Included |
| **Fixed implementation price**          |       **£35,000** |

Monthly maintenance:

| Maintenance item                              |     Monthly cost |
| --------------------------------------------- | ---------------: |
| Accuracy checks                               |         Included |
| Rule adjustments                              |         Included |
| User support                                  |         Included |
| Exception review                              |         Included |
| Monthly report                                |         Included |
| Minor changes to folders, labels or templates |         Included |
| **Monthly maintenance**                       | **£1,200/month** |

Year-one total:

| Item                    |        Cost |
| ----------------------- | ----------: |
| Fixed implementation    |     £35,000 |
| 12 months’ maintenance  |     £14,400 |
| **Total year-one cost** | **£49,400** |

## Expected efficiency impact

Assumptions for a 50-person commercial broking team:

| Metric                                           |                       Assumption |
| ------------------------------------------------ | -------------------------------: |
| Users                                            |                               50 |
| Average working days per year                    |                              220 |
| Current time lost searching/reconstructing files | 20–40 minutes per person per day |
| Target time saved after automation               |    20 minutes per person per day |
| Fully loaded staff cost                          |                         £45/hour |
| One-time implementation cost                     |                          £35,000 |
| Monthly maintenance                              |                           £1,200 |

### Annual time recovered

50 users × 220 days × 20 minutes = **220,000 minutes saved per year**

220,000 minutes ÷ 60 = **3,667 hours saved per year**

3,667 hours × £45/hour = **£165,000 annual labour value**

## ROI and payback

### Base case: 20 minutes saved per user per day

| Item                         |          Value |
| ---------------------------- | -------------: |
| Annual labour saving         |   **£165,000** |
| One-time implementation cost |        £35,000 |
| First-year maintenance       |        £14,400 |
| **Total year-one cost**      |    **£49,400** |
| **Year-one net benefit**     |   **£115,600** |
| **Year-one ROI**             |       **234%** |
| **Payback period**           | **3.6 months** |

Calculation:
£115,600 net benefit ÷ £49,400 year-one cost = **234% ROI**

Payback calculation:
£49,400 ÷ £165,000 × 12 months = **3.6 months**

## Conservative case

If the system saves only **15 minutes per user per day**:

| Item                 |          Value |
| -------------------- | -------------: |
| Annual hours saved   |    2,750 hours |
| Annual labour saving |       £123,750 |
| Year-one cost        |        £49,400 |
| Year-one net benefit |    **£74,350** |
| Year-one ROI         |       **151%** |
| Payback period       | **4.8 months** |

Even in the conservative case, the project pays back within the first year.

## Strong case

If the system saves **25 minutes per user per day**:

| Item                 |          Value |
| -------------------- | -------------: |
| Annual hours saved   |    4,583 hours |
| Annual labour saving |       £206,250 |
| Year-one cost        |        £49,400 |
| Year-one net benefit |   **£156,850** |
| Year-one ROI         |       **318%** |
| Payback period       | **2.9 months** |

## Year-two economics

The year-two case is stronger because the implementation has already been paid.

| Item                                |        Value |
| ----------------------------------- | -----------: |
| Annual labour saving at 20 mins/day |     £165,000 |
| Annual maintenance cost             |      £14,400 |
| **Year-two net benefit**            | **£150,600** |
| ROI on annual maintenance           |   **1,046%** |

## Break-even test

The project only needs to save a small amount of time per user to cover its year-one cost.

| Metric                                         |         Value |
| ---------------------------------------------- | ------------: |
| Year-one cost                                  |       £49,400 |
| Cost per user                                  |          £988 |
| Required annual saving per user                |          £988 |
| Required hours saved per user/year at £45/hour |      22 hours |
| Required minutes saved per user/day            | **6 minutes** |

So the project breaks even if each person saves only **about 6 minutes per working day**.

That is a credible threshold for a split-file problem where staff currently search across BMS, email, Teams, SharePoint, portals and local folders.

## Additional rework reduction

The direct time saving is the main financial driver. However, the workflow should also reduce duplicate work and file reconstruction.

If the 50-person team avoids only **500 hours per year** of rework from duplicate document creation, missing evidence and file review failures:

500 hours × £45/hour = **£22,500 additional annual value**

| Item                 |          Value |
| -------------------- | -------------: |
| Search-time saving   |       £165,000 |
| Rework saving        |        £22,500 |
| Total annual benefit |   **£187,500** |
| Year-one cost        |        £49,400 |
| Year-one net benefit |   **£138,100** |
| Payback period       | **3.2 months** |

## Risk and compliance benefit

If the workflow prevents just **two material file-quality escalations per year**, and each escalation requires 25 internal hours at an average £70/hour:

2 × 25 × £70 = **£3,500**

That is not the main ROI driver, but it strengthens the operational risk case. The main financial value remains:

| Main value driver           | Impact                                                              |
| --------------------------- | ------------------------------------------------------------------- |
| Less search time            | Faster client service and less internal waste                       |
| Less duplicate work         | Fewer repeated document requests and recreated schedules            |
| Better file review          | Fewer missing-evidence queries                                      |
| Faster renewal/MTA handling | Less reconstruction before action                                   |
| Lower E&O exposure          | Better visibility of client instructions and underwriter conditions |

## Why this should not be a fully autonomous AI agent

A fully autonomous AI agent could search, decide, move files, update records and create summaries with limited human intervention. That is attractive in theory, but not ideal here.

For broker file control, the risk is not just operational efficiency. The system is handling evidence around advice, client instructions, subjectivities, acceptances, changed terms and policy documentation. A wrong decision could affect file quality, compliance review or E&O exposure.

| Option                                  | Fit        | Reason                                                                                  |
| --------------------------------------- | ---------- | --------------------------------------------------------------------------------------- |
| Fully autonomous AI agent               | Low-medium | Too much judgement risk for client instructions, policy evidence and audit trails       |
| Simple automation only                  | Medium     | Reliable for filing rules, but weak at reading messy emails, PDFs and version conflicts |
| Controlled workflow + narrow AI support | High       | Combines predictable process control with AI document understanding                     |

The best solution is therefore a **controlled file-control workflow** where AI assists with reading, matching, classifying and flagging, but staff retain approval over uncertain or high-risk items.

## Recommended AI-agent position

Use AI only where it adds clear value:

| AI-supported task                                | Control mechanism                          |
| ------------------------------------------------ | ------------------------------------------ |
| Read email/document content                      | Confidence score and review queue          |
| Identify client, policy and document type        | Match against client/policy reference list |
| Flag client instruction or underwriter condition | Handler confirms importance                |
| Detect possible missing evidence                 | Exception report routes to owner           |
| Summarise file timeline                          | Staff can verify source documents          |
| Identify conflicting document versions           | Workflow asks for confirmation             |

Recommended model:

**85% controlled workflow + 15% AI interpretation**

That is cheaper, easier to govern and more acceptable for compliance than a fully autonomous agent.

## Success metrics

Use clear before/after measures:

| Measure                                      |             Current baseline |         Target after 6 months |
| -------------------------------------------- | ---------------------------: | ----------------------------: |
| Average time to find key renewal evidence    |                10–20 minutes |               Under 3 minutes |
| Documents correctly classified               |               Not consistent |                       70–80%+ |
| Correct client/policy matching               |        Manual / inconsistent |                       75–85%+ |
| High-risk unfiled items detected             |    Not consistently measured | 90%+ detection queue coverage |
| File review failures due to missing evidence |      Baseline from QA sample |              30–50% reduction |
| Duplicate document creation                  | Baseline from staff sampling |              25–40% reduction |
| Handler time spent reconstructing files      |               20–40 mins/day |                10–15 mins/day |
| Break-even saving required                   |                          N/A |               6 mins/user/day |
| Target saving                                |                          N/A |              20 mins/user/day |

## Recommended rollout

### Phase 1: controlled deployment

Implement the workflow across one 50-person commercial team or one 50-person group split across commercial handling, account executives, renewals and compliance review.

Duration: **8–10 weeks**

Focus areas:

| Use case                           | Reason                                                                                |
| ---------------------------------- | ------------------------------------------------------------------------------------- |
| Renewals                           | Highest document volume and strongest evidence requirement                            |
| MTAs                               | Frequent risk of revised schedules, endorsements and client confirmations being split |
| Client instructions                | High E&O relevance                                                                    |
| Underwriter subjectivities         | Often buried in email                                                                 |
| Quote and schedule version control | Common source of rework                                                               |

### Phase 2: tune and stabilise

After go-live, use the monthly maintenance period to:

| Activity                      | Purpose                    |
| ----------------------------- | -------------------------- |
| Review false matches          | Improve accuracy           |
| Add document wording patterns | Improve classification     |
| Refine exception categories   | Reduce noise               |
| Track time saved              | Confirm ROI                |
| Compare file review outcomes  | Measure compliance benefit |

### Phase 3: optional expansion

Only after the first 50-person deployment proves value, consider:

| Expansion                 | When justified                                            |
| ------------------------- | --------------------------------------------------------- |
| Another team              | When classification and matching accuracy are stable      |
| Claims documents          | When renewal/MTA process is proven                        |
| BMS write-back            | When governance and audit controls are mature             |
| Portal-specific workflows | When document volume justifies the extra cost             |
| Historic file clean-up    | Only where there is a clear risk or client-service reason |

## Decision rule for rollout success

Proceed to wider rollout only if the 50-person deployment achieves at least:

| Criterion                                        |     Minimum target |
| ------------------------------------------------ | -----------------: |
| Time saved per user per day                      |     **15 minutes** |
| Correct document classification                  |           **70%+** |
| Correct client/policy matching                   |           **75%+** |
| Reduction in “where is the evidence?” queries    |           **25%+** |
| Reduction in missing-evidence file review issues |           **30%+** |
| Payback period                                   | **Under 6 months** |

## Recommendation

Implement a **fixed-price AI-assisted document control workflow** for a 50-person team.

The commercial model should be:

| Item                          | Recommendation   |
| ----------------------------- | ---------------- |
| Fixed implementation          | **£35,000**      |
| Monthly maintenance           | **£1,200/month** |
| Year-one total                | **£49,400**      |
| Year-two onward               | **£14,400/year** |
| Expected annual labour value  | **£165,000**     |
| Expected year-one net benefit | **£115,600**     |
| Expected payback              | **3.6 months**   |

This is a strong candidate for AI-assisted automation because the problem is repetitive, document-heavy, high-volume and costly, but still needs controlled human approval where client instructions or regulated records are involved.

The best design is **not** a fully autonomous AI agent. The right approach is a **controlled automation workflow with narrow AI support**, because it preserves auditability, keeps implementation cost under control and focuses the AI on the parts where it adds most value: reading documents, identifying key evidence, matching files and flagging exceptions.