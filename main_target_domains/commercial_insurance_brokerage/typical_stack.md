## Scope assumed

Mid-market UK commercial broker here means a regional or national commercial broker serving SME-to-mid-market corporate clients, with some simple risks e-traded and more complex commercial risks placed manually with underwriters, MGAs, wholesale brokers, or the London Market. Insurer definitions vary, but AXA’s public mid-market proposition, for example, describes commercial business with premiums around **£10,000–£250,000**. ([AXA Connect][1])

The typical stack is **BMS-centred**: the broker management system is the regulated client/policy/accounting record; Microsoft 365 and email handle much of the document traffic; insurer portals, e-trade platforms, and placement systems handle market access.

---

## 1. Core software stack

| Layer                                        | Typical systems                                                                                                                              | Main purpose                                                                                                                                   |
| -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| **Broker Management System / Policy Admin**  | Acturis, Open GI, SSP; legacy Applied/TAM/RiskHandler estates in some firms                                                                  | Client record, policy record, quotes, renewals, MTAs, cancellations, claims diary, task workflow, document generation, accounting, audit trail |
| **CRM / Sales pipeline**                     | Native BMS CRM, Microsoft Dynamics, Salesforce, HubSpot, sector-specific pipeline tools                                                      | Prospecting, opportunity tracking, cross-sell, sector campaigns, producer activity, renewal pipeline                                           |
| **Market connectivity / e-trade**            | Acturis eTrade, Polaris/iMarket, insurer portals such as Aviva Fast Trade, Allianz QuoteSME, AXA Connect, MGA portals                        | Quote, bind, amend, renew, compare panel quotes, access insurer documentation                                                                  |
| **Complex placement / London Market**        | PPL, insurer/MGA portals, wholesale broker platforms, email-led submission packs                                                             | Larger commercial, specialty, facultative, scheme, delegated-authority, and London Market placements                                           |
| **Document management and collaboration**    | BMS document store, Microsoft SharePoint, OneDrive, Teams, Outlook/Exchange; larger firms may add iManage, M-Files, NetDocuments or similar  | Client file, correspondence, policy documents, proposal forms, submissions, versioning, collaboration                                          |
| **E-signature**                              | DocuSign, Adobe Sign, OneSpan, insurer/premium-finance e-sign flows                                                                          | Terms of business, declarations, proposal forms, premium-finance agreements, client authorities                                                |
| **Finance / client money / premium finance** | BMS accounting module, Sage, Xero, NetSuite or finance system; Close Brothers Premium Finance, Premium Credit, payment platforms, bank feeds | Client money, insurer statements, bordereaux, commission, fees, reconciliations, direct debit, premium instalments                             |
| **Claims**                                   | BMS claims module, insurer claims portals, FNOL forms, loss adjuster portals, document store                                                 | Claims notification, evidence, reserves, insurer correspondence, settlement and repudiation records                                            |
| **Compliance / conduct risk**                | BMS QA module, file-review tools, complaints logs, SMCR/HR tools, FCA RegData, policy governance repositories                                | File audits, complaints, Consumer Duty evidence, product governance, training and competence, breach records                                   |
| **BI / MI / data warehouse**                 | Power BI, Excel, SQL/Azure/Snowflake, BMS reporting, bordereaux reporting tools                                                              | GWP, retention, pipeline, insurer performance, producer performance, claims, complaints, conduct MI                                            |
| **Security / IT operations**                 | Microsoft Entra ID, MFA, Defender, Intune, Purview, backup, endpoint protection, email security, Cyber Essentials controls                   | Identity, device control, data loss prevention, retention, eDiscovery, cyber-risk management                                                   |

Acturis, Open GI, and SSP all position their platforms around the BMS/PAS core: policy administration, insurer connectivity, renewals, claims, accounts, document/template handling, audit trails, and broker workflow. Acturis also states that more than **£18.5bn** of UK premium is transacted annually on its platform. ([Acturis][2])

One 2025–2026 planning point: **Applied Epic should not be treated as a default UK target-state BMS**. Applied announced in June 2025 that it would withdraw Applied Epic from the UK broker management system market, with a multi-year transition for existing customers, while continuing to support other UK products such as TAM, Rating Hub, and RiskHandler. ([Applied Systems][3])

---

## 2. Placement and trading pattern

For most mid-market brokers, placement splits into three channels.

**Simple commercial / SME e-trade:** package, tradesman, shops, offices, small fleet, straightforward property owners, simple liability, trades, and some PI or cyber products. These are usually quoted through Acturis, iMarket, insurer portals, or software-house integrations. Aviva, for example, supports online quote/buy/amend flows, documentation, comparative panel access, and integration without rekeying via Acturis eTrade and Fast Trade. ([Aviva B2B][4])

**Mid-market underwriter-led placement:** property, casualty, fleet, motor trade, contractors, manufacturing, logistics, care, leisure, and professional risks with higher values or unusual exposures. These often start in the BMS but move into submission packs, insurer emails, underwriter portals, branch trading teams, or MGA platforms.

**London Market / specialty placement:** marine, construction, energy, D&O, excess liability, high-value property, binding authorities, or non-standard risks. PPL describes itself as the digital backbone for London Market placement and says more than 400 firms use the platform across simple and complex risks. ([The London Market’s ePlacing Platform][5])

---

## 3. Document stack by lifecycle

### A. Prospecting and onboarding

Typical documents:

| Document                                        | Purpose                                                                                                   |
| ----------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Client fact-find / onboarding form              | Business identity, structure, locations, activities, turnover, employees, assets, current policies        |
| Broker Terms of Business Agreement              | Scope of service, status of broker, remuneration, client money terms, cancellation terms, complaint route |
| Letter of appointment / broker of record        | Authority to act for the client and request information from insurers                                     |
| Privacy notice / data-processing wording        | GDPR transparency and lawful basis                                                                        |
| Sanctions / financial crime screening record    | Evidence of screening and referral where needed                                                           |
| Contact preferences / vulnerable customer notes | Conduct and service records, especially where retail or small-business treatment applies                  |

For UK insurance distribution, the client file should distinguish consumer, micro-enterprise, small business, and larger commercial clients because conduct, complaints, disclosure, and Consumer Duty treatment can differ. FOS eligibility thresholds include micro-enterprises and certain SMEs, including businesses with annual turnover below £6.5m and fewer than 50 employees or a balance sheet below £5m. ([Financial Ombudsman][6])

---

### B. Risk discovery and fair presentation

Typical documents:

| Document                                  | Purpose                                                                                               |
| ----------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| Demands and needs statement               | Records the customer’s insurance requirements before contract                                         |
| Proposal form / statement of presentation | Formal risk presentation to insurers                                                                  |
| Exposure schedules                        | Property, vehicles, plant, locations, payroll, turnover, contracts, travel, equipment                 |
| Claims history                            | Usually 3–5 years, sometimes longer for complex risks                                                 |
| Risk surveys / photos / valuations        | Evidence for property, security, fire, flood, business interruption, fleet, or liability underwriting |
| Client declarations                       | Accuracy, material facts, fair presentation, no-known-claims declarations                             |
| Contract review notes                     | Insurance obligations in leases, customer contracts, funding agreements, or tender requirements       |

The FCA’s ICOBS rules require firms to specify the customer’s demands and needs before contract and to give appropriate information in good time and in a comprehensible form. Separately, the Insurance Act 2015 requires commercial insureds to make a fair presentation of the risk before contract. ([FCA Handbook][7])

---

### C. Market submission and quotation

Typical documents:

| Document                                      | Purpose                                                                      |
| --------------------------------------------- | ---------------------------------------------------------------------------- |
| Market presentation / underwriting submission | Consolidated risk pack sent to insurers or MGAs                              |
| Quote request / slip                          | Coverage required, limits, excesses, sums insured, basis of cover            |
| Underwriter Q&A log                           | Audit trail of clarifications, subjectivities, and disclosures               |
| Quote comparison                              | Premiums, excesses, conditions, exclusions, insurer security, commission/fee |
| Declined / no-quote record                    | Evidence of market exercise                                                  |
| Subjectivities and warranties log             | Security conditions, surveys, risk improvements, premium payment conditions  |
| Internal referral / placement approval        | Escalation for large, unusual, or E&O-sensitive placements                   |

For e-traded business, many of these records sit partly inside the BMS or insurer portal. For larger commercial placements, the same information often exists as emails, Excel schedules, PDFs, presentation decks, and portal records, which creates a document-control problem unless the broker has a disciplined client-file taxonomy.

---

### D. Recommendation, bind, and policy issue

Typical documents:

| Document                                       | Purpose                                                                                                   |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Recommendation letter / suitability-style note | Why the selected policy meets the client’s demands and needs                                              |
| Quote letter                                   | Premium, taxes, fees, commission disclosure where relevant, cover summary, assumptions                    |
| Statement of demands and needs                 | Usually included with the recommendation or quote pack                                                    |
| Product information / summary                  | Key features, exclusions, conditions, optional covers                                                     |
| IPID where applicable                          | Required for consumer non-investment insurance; commercial customers still need clear product information |
| Policy schedule and wording                    | Contract terms                                                                                            |
| Cover note / evidence of cover                 | Temporary or immediate evidence pending final documents                                                   |
| Certificate                                    | Employers’ liability, motor, travel, marine, or other certificate where relevant                          |
| Invoice / debit note                           | Premium, IPT, fees, payment terms                                                                         |
| Client acceptance instruction                  | Written acceptance, call note, e-signature, or portal confirmation                                        |

The FCA confirmed the formal IPID requirement was not extended to commercial customers, but commercial customers must still receive appropriate product information in a relevant and comprehensible form. ([Pinsent Masons][8])

Electronic signatures are usually part of the practical document stack. The UK government’s position, following the Law Commission, is that electronic signatures can be used to execute documents, including where a statutory signature is required, and are a viable alternative to handwritten signatures in most cases. ([GOV.UK][9])

---

### E. Renewal

Typical documents:

| Document                     | Purpose                                                                                  |
| ---------------------------- | ---------------------------------------------------------------------------------------- |
| Renewal diary / trigger      | Starts renewal activity, typically 90–120 days before renewal for complex accounts       |
| Updated fact-find            | Captures changed exposures, turnover, payroll, vehicles, contracts, acquisitions, claims |
| Fair presentation reminder   | Prompts client to disclose material circumstances                                        |
| Claims experience            | Insurer or loss-run data                                                                 |
| Market review evidence       | Incumbent terms, alternatives, declinatures, comparison                                  |
| Renewal invitation           | Terms, premium, changes, assumptions, payment options                                    |
| Lapsed / not-taken-up record | Evidence where client does not proceed                                                   |

Renewal is usually the most important document-control point. Weak renewal files often show missing updated exposure data, unclear client instructions, poor evidence of alternative marketing, or no clear explanation of changed cover terms.

---

### F. Mid-term adjustments

Typical documents:

| Document                            | Purpose                                                                     |
| ----------------------------------- | --------------------------------------------------------------------------- |
| MTA request                         | Change in exposure, vehicle, address, limits, employees, activity, contract |
| Insurer endorsement                 | Contractual change to policy                                                |
| Revised schedule / certificate      | Updated policy evidence                                                     |
| Additional / return premium invoice | Accounting and client money record                                          |
| Client confirmation                 | Evidence that the client requested or accepted the change                   |

MTAs need tight workflow because they affect both policy coverage and client-money accounting.

---

### G. Claims

Typical documents:

| Document                          | Purpose                                                                           |
| --------------------------------- | --------------------------------------------------------------------------------- |
| FNOL record                       | First notification, date of loss, cause, circumstances                            |
| Claim form                        | Formal claim submission                                                           |
| Evidence pack                     | Photos, invoices, witness statements, contracts, police reports, medical evidence |
| Insurer / adjuster correspondence | Coverage position, reserve, liability, quantum                                    |
| Settlement / repudiation letter   | Outcome and rationale                                                             |
| Complaint record if disputed      | Complaint trigger, acknowledgements, final response, FOS rights where applicable  |

Claims documentation should link back to policy conditions, notification requirements, warranties, endorsements, and any advice given at placement.

---

### H. Finance, client money, and bordereaux

Typical documents and records:

| Document / record                  | Purpose                                                                                 |
| ---------------------------------- | --------------------------------------------------------------------------------------- |
| Premium invoice / debit note       | Premium, IPT, broker fee, due date                                                      |
| Client-money ledger                | Client money received, paid, held, reconciled                                           |
| Insurer statement                  | Amounts due to insurers, commission deductions, settlement date                         |
| CASS reconciliation                | Evidence of segregation and reconciliation                                              |
| Premium finance agreement          | Credit agreement, direct debit, e-signature, cancellation implications                  |
| Bordereaux                         | Premium, risk, claims, commission, and tax reporting for delegated authority or schemes |
| Commission / fee disclosure record | Evidence of remuneration disclosure and client agreement where required                 |

FCA CASS 5 applies to client money in insurance distribution, and premium-finance providers remain a common part of the broker operating stack. Close Brothers Premium Finance says it works with more than 1,600 brokers across over 2,000 offices and supports digital integration, e-signature, and online premium finance. ([FCA Handbook][10])

---

## 4. Regulatory and governance overlay for 2025–2026

The 2025–2026 stack should account for FCA rule changes and the continued emphasis on outcomes evidence. In December 2025, the FCA finalised insurance-rule simplifications covering areas such as which rules apply to commercial insurance, lead-firm responsibility for product design and approval, bespoke-contract exclusions, product-review frequency, employers’ liability reporting, and removal of the minimum 15-hour CPD rule for employees. Consumer Duty remains a live supervisory priority, with the FCA saying it will rely on the Duty rather than adding new prescriptive rules where possible. ([FCA][11])

A practical governance stack therefore needs:

| Control area               | Typical records                                                                                          |
| -------------------------- | -------------------------------------------------------------------------------------------------------- |
| Product governance         | Target market, fair value assessment, manufacturer/distributor responsibilities, review dates            |
| Client segmentation        | Consumer, micro-enterprise, SME, large commercial, wholesale, delegated-authority client                 |
| File quality               | QA checklist, advice quality, disclosure, client instruction, demands and needs, recommendation evidence |
| Complaints                 | Acknowledgement, investigation, final response, root-cause analysis, FOS eligibility                     |
| Training and competence    | Role profile, competence assessment, CPD evidence, supervision, sign-off                                 |
| Conflicts and remuneration | Commission, fees, contingent commission, placement strategy, TOBA terms                                  |
| Breaches and E&O           | Breach log, incident report, remedial action, insurer notification where needed                          |
| Appointed representatives  | Oversight file, audits, AR agreements, monitoring MI                                                     |

---

## 5. Microsoft 365 and document-control reality

Most mid-market brokers run a large portion of their practical document stack through **Outlook, Teams, SharePoint, and OneDrive**, even where the BMS is the official system of record. Microsoft 365 Business plans include Exchange, Outlook, OneDrive and SharePoint; Business Premium adds security and management capabilities such as Entra ID, Intune, Defender, and Purview. SharePoint supports document libraries, versioning, access control, co-authoring, and secure file sharing. ([Microsoft][12])

The common target model is:

| Repository                       | Use                                                                                                          |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **BMS document store**           | Final client-file documents, regulated correspondence, quotes, schedules, policies, invoices, claims records |
| **SharePoint / Teams**           | Collaboration, draft submissions, shared schedules, team folders, project work                               |
| **Outlook / Exchange**           | Client and insurer correspondence; should be filed or linked back to BMS                                     |
| **OneDrive**                     | Personal working drafts only; not ideal as a permanent client-file repository                                |
| **E-signature platform**         | Signed TOBAs, declarations, premium-finance forms, appointment letters                                       |
| **Retention / eDiscovery layer** | Legal hold, audit, investigation, data subject access, retention policies                                    |

The operational risk is a split file: the BMS says one thing, SharePoint has another version, and Outlook contains the key underwriter clarification. Mature brokers reduce that risk with naming conventions, metadata, retention labels, automatic email filing, and clear rules on what must be stored in the BMS.

---

## 6. Security baseline

For 2025–2026, the expected baseline is MFA, conditional access, endpoint protection, email filtering, immutable or tested backups, least-privilege permissions, supplier access control, incident response, and Cyber Essentials or Cyber Essentials Plus. The UK National Cyber Security Centre describes Cyber Essentials as the government-recommended minimum cyber-security standard for organisations of all sizes, built around five technical controls to prevent common internet-based attacks. ([National Cyber Security Centre][13])

Insurance brokers are attractive targets because they hold identity data, claims data, financial data, business interruption information, and renewal/payment records. Security controls should therefore be treated as part of the document stack, not just IT infrastructure.

---

## 7. Typical maturity patterns

| Broker type                                  | Likely stack                                                                                                                                                                                    |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Smaller mid-market / regional broker**     | Acturis/Open GI/SSP, Microsoft 365, insurer portals, premium finance, basic Power BI or Excel MI, manual compliance file checks                                                                 |
| **Larger independent broker**                | Core BMS, separate CRM, structured SharePoint, e-signature, API/data warehouse, Power BI dashboards, formal QA workflow, central compliance repository                                          |
| **Consolidator / national broker**           | Multiple legacy BMS platforms, integration layer, central data warehouse, standard document templates, central placement teams, group compliance tooling, stronger cyber and retention controls |
| **Specialist / London Market-facing broker** | BMS plus PPL and specialty placement workflows, richer submission packs, bordereaux tooling, wholesale/MGA portals, more complex slip/evidence-of-cover document handling                       |
| **Scheme / delegated-authority broker**      | BMS plus product/rating configuration, bordereaux, insurer reporting, claims authority controls, binder governance, audit-ready underwriting files                                              |

---

## Target-state stack for 2025–2026

A robust mid-market UK commercial broker stack would usually look like this:

1. **Core BMS/PAS:** Acturis, Open GI, SSP, or a managed legacy platform as the system of record.
2. **Microsoft 365:** Outlook, Teams, SharePoint, OneDrive, Entra ID, Defender, Intune, Purview.
3. **Trading layer:** Acturis/iMarket/insurer portals/MGA portals; PPL where London Market placement is material.
4. **Document layer:** BMS templates, SharePoint taxonomy, e-signature, retention labels, email filing, client-file rules.
5. **Finance layer:** BMS accounts, client-money controls, premium finance, payment platform, GL integration.
6. **Data layer:** BMS reporting plus Power BI/data warehouse for GWP, retention, claims, conduct, pipeline, and insurer MI.
7. **Compliance layer:** file QA, complaints, product governance, Consumer Duty evidence, CASS controls, SMCR, training and competence.
8. **Security layer:** MFA, endpoint protection, backup, DLP, access reviews, Cyber Essentials, incident response.

The main design principle is that **the BMS owns the regulated client and policy record; SharePoint/Teams support collaboration; portals support placement; finance systems support reconciliation; compliance and BI systems evidence control and outcomes**.

[1]: https://www.axaconnect.co.uk/commercial-lines/axa-vantage-mid-market/?utm_source=chatgpt.com "Mid-Market - Vantage"
[2]: https://www.acturis.com/ "Insurance Software Solutions for Brokers, Insurers and MGAs | Acturis"
[3]: https://www1.appliedsystems.com/en-uk/news/press-releases/2025/applied-systems-announces-plan-to-withdraw-applied-epic-from-the-uk-market/ "Applied Systems Announces Plan to Withdraw Applied Epic from the UK Broker Management System Market"
[4]: https://connect.avivab2b.co.uk/broker/support/online-services/integrated-trading/ "Aviva Broker: Integrated Trading - Aviva - Aviva"
[5]: https://placingplatformlimited.com/ "Home - The London Market’s ePlacing Platform"
[6]: https://www.financial-ombudsman.org.uk/consumers/expect/who-we-can-help "Who we can help – Financial Ombudsman service"
[7]: https://handbook.fca.org.uk/handbook/ICOBS/5/2.html?utm_source=chatgpt.com "ICOBS 5.2 Demands and needs"
[8]: https://www.pinsentmasons.com/out-law/legal-updates/fca-outlines-insurance-distribution-directive-changes-for-all-insurance-firms?utm_source=chatgpt.com "FCA outlines Insurance Distribution Directive changes for ..."
[9]: https://www.gov.uk/government/publications/electronic-execution-of-documents "Electronic execution of documents - GOV.UK"
[10]: https://handbook.fca.org.uk/handbook/cass5?utm_source=chatgpt.com "CASS 5 Client money: insurance distribution activity"
[11]: https://www.fca.org.uk/publications/policy-statements/ps25-21-simplifying-insurance-rules "PS25/21: Simplifying the insurance rules | FCA"
[12]: https://www.microsoft.com/en-gb/microsoft-365/sharepoint/collaboration "Collaborative Content Management, and Secure File Sharing | Microsoft SharePoint"
[13]: https://www.ncsc.gov.uk/cyberessentials/overview "Cyber Essentials | National Cyber Security Centre"
