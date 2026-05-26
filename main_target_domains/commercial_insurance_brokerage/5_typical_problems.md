Below are the **5 biggest document-related workflow problems** I would expect in a UK mid-size commercial insurance broker. This is not a formal market ranking, because public sources rarely rank document problems at that granularity. It is a realistic ranking based on broker operating models, public broker/insurer technology evidence, FCA/BIBA material, and the uploaded stack note. 

## Context

A typical mid-market UK commercial broker is still **BMS-centred**, but much of the live document traffic sits in **Outlook, Teams, SharePoint, OneDrive, insurer portals, e-trade platforms, PPL, PDFs and spreadsheets**, rather than in one clean end-to-end workflow. The uploaded stack describes the BMS as the regulated client/policy/accounting record, while Microsoft 365, email, portals and placement systems handle much of the day-to-day document flow.  BIBA’s sector data also underlines the scale and operational importance of brokers: UK general insurance brokers arrange 77% of general insurance, £105.5bn of premium, and 94% of commercial insurance business. ([BIBA][1])

---

## 1. Split client files across BMS, Outlook, SharePoint, Teams, portals and personal folders

**Problem:** The “official” file may be in the BMS, but the real working file is often spread across email threads, SharePoint folders, Teams chats, insurer portals, PPL records, Excel schedules, signed PDFs and sometimes individual OneDrive folders.

**What this looks like in practice:**
A commercial account handler may have the final schedule in the BMS, the latest property schedule in SharePoint, the underwriter’s subjectivity buried in Outlook, a revised quote in an insurer portal, and the client’s acceptance in a Teams/email exchange. When a renewal, MTA, claim or complaint comes up, staff spend time reconstructing the file instead of servicing the client.

**Why it slows brokers down:**
Search time increases, duplicate document creation becomes common, staff ask clients or underwriters for information they already have, and file review becomes slower. It also creates E&O risk: a key underwriter clarification or client instruction may not be visible to the person issuing advice or binding cover.

**Evidence:**
The uploaded broker stack specifically flags the operational risk of a “split file”: the BMS may say one thing, SharePoint another, while Outlook contains the key underwriter clarification.  This also fits the public direction of travel in placement technology: PPL says its platform is designed to connect market participants, streamline electronic placing and reduce administration costs, while its API integrations aim to reduce re-keying and enable straight-through processing. ([The London Market’s ePlacing Platform][2])

**Severity:** Very high. This is the root cause behind many downstream delays.

---

## 2. Manual re-keying from emails, PDFs, spreadsheets and portal forms

**Problem:** Commercial risks still arrive and move through the market as mixed-format information: proposal forms, exposure schedules, claims histories, surveys, valuations, spreadsheets, PDFs, photos and email answers. These documents often have to be manually translated into BMS fields, portal questions, quote comparison sheets, submissions and client letters.

**What this looks like in practice:**
A broker receives a fleet list in Excel, property details in a PDF, claims history from an insurer portal, and turnover/payroll updates in an email. The handler then re-enters the same information into the BMS, insurer portal, market presentation, premium finance form and renewal letter. Each re-entry point can introduce a typo or inconsistency.

**Why it slows brokers down:**
Re-keying consumes account-handler time, creates avoidable errors, and forces second-person checking. Errors in turnover, sums insured, business description, vehicle details, claims history or policy dates can delay quote issuance, cause referral loops, or require policy reissue after bind.

**Evidence:**
LexisNexis Risk Solutions’ commercial insurance survey found that, in underwriting and pricing, only 16% of brokers were all or mostly digitised, while 60% still performed all or most processes manually; it also found that claims remained highly manual, with about 64% of brokers handling claims manually. ([LexisNexis Risk Solutions][3]) Open GI makes the same operational point from a broker-system perspective: brokers spend time on disjointed, manual and repetitive activities including data entry, document processing and issuing policies. ([opengi.co.uk][4]) Aviva’s e-trading page is useful evidence of the opposite target state: it promotes “enter once” comparative panel access and back-office trading “without rekeying,” which implies re-keying remains a real problem where such integration is absent. ([connect.avivab2b.co.uk][5])

**Severity:** Very high. This is one of the most direct causes of lost productivity.

---

## 3. Renewal document chasing and weak fair-presentation evidence

**Problem:** Renewals require updated exposure data, claims experience, fair-presentation prompts, market review evidence, quote comparisons, client decisions and changed-cover explanations. In commercial insurance, especially mid-market risks, this data rarely arrives in one complete, structured package.

**What this looks like in practice:**
The broker needs updated turnover, payroll, ERN, locations, business activities, property values, security details, vehicle schedules, contract changes, claims updates and risk improvements. The client sends partial information late, underwriters ask follow-up questions, and the broker has to rebuild the presentation while the renewal deadline approaches.

**Why it slows brokers down:**
Incomplete renewal files create chasing loops: client → broker → underwriter → broker → client. If exposure data is stale or unclear, underwriters may not quote, may refer the risk, or may issue terms with assumptions and subjectivities that need further explanation. Internally, file reviewers may also reject a file because the demands-and-needs record, marketing evidence or client instruction is incomplete.

**Evidence:**
The uploaded stack identifies renewal as the most important document-control point and notes that weak renewal files commonly show missing updated exposure data, unclear client instructions, poor evidence of alternative marketing, or unclear explanation of changed cover terms.  The legal/regulatory context makes this operationally important: the Insurance Act 2015 requires a fair presentation of the risk before commercial insurance is entered into, and AXA’s broker guidance says firms must record demands and needs and specify them to the customer before conclusion of the contract. ([Legislation.gov.uk][6]) BIBA’s 2025 disclosure guidance also points to a live market issue: misunderstandings over what should have been disclosed can lead to claims being repudiated or reduced, and BIBA is pushing clearer, more consistent question sets. ([BIBA][7])

**Severity:** High. It directly affects renewal timeliness, client retention and E&O exposure.

---

## 4. Compliance evidence and file-quality workload

**Problem:** Commercial brokers must produce and retain evidence that advice, placement, remuneration, product governance, client classification, demands-and-needs, fair value, complaints handling and client-money processes were handled properly. This is document-heavy and often not fully automated.

**What this looks like in practice:**
A file may need a fact-find, TOBA, demands-and-needs statement, quote letter, recommendation note, market exercise evidence, insurer declinatures, target market/fair value checks, commission/fee disclosure, client acceptance, policy documents, invoice, premium finance documents, and QA checklist. If these are stored inconsistently, a compliance review can trigger rework after the client-facing work appears “done.”

**Why it slows brokers down:**
Handlers and executives spend time proving the process rather than only executing it. Compliance teams may return files for missing evidence, wrong templates, unsigned TOBAs, incomplete client instructions or unclear rationale. This creates internal queues and can delay bind, renewal invites or post-bind documentation.

**Evidence:**
BIBA-commissioned research published in 2025 found that regulation costs amount to 5.2% of insurance premiums collected, including 3.3% for brokers; BIBA also says indirect regulatory costs include internal staff time, broker time, management time, procured compliance services, regulator visits and compliance enquiries. ([BIBA][8]) The FCA’s 2024 product governance review found that many insurance firms were not fully meeting product governance obligations; it also said many manufacturers were not adequately evidencing fair value and that most distributors did not fully understand their responsibilities around remuneration, services and product value. ([FCA][9]) For mid-size brokers, this means more evidence-gathering, more MI requests and more file review pressure.

**Severity:** High. It does not always delay the first client interaction, but it slows completion and creates rework.

---

## 5. Claims and post-bind documentation delays: endorsements, certificates, evidence packs and insurer responses

**Problem:** After bind, document work continues: policy schedules, certificates, endorsements, debit/credit notes, premium finance agreements, claims evidence, adjuster correspondence, settlement letters and repudiation records. These documents often sit across insurer portals, email, the BMS and claims systems.

**What this looks like in practice:**
A client asks for urgent evidence of cover, an EL certificate, a motor certificate, an amended schedule, or confirmation that a claim has been accepted. The broker may need to chase the insurer, check portal output, correct a schedule, issue an invoice, update the BMS and send the final document to the client. In claims, the broker may need to gather photos, invoices, witness statements, contracts and insurer correspondence before the claim can move.

**Why it slows brokers down:**
Post-bind document defects are expensive because the sale is already complete but the work is not. Each incorrect endorsement, missing certificate or incomplete claim evidence pack creates client follow-up, insurer chasing and rework. Claims are especially sensitive because document delays directly affect client perception of service.

**Evidence:**
The uploaded stack lists MTAs as requiring insurer endorsements, revised schedules/certificates, additional or return premium invoices and client confirmations, and notes that MTAs need tight workflow because they affect both policy coverage and client-money accounting.  It also lists claims documentation as FNOL records, claim forms, evidence packs, insurer/adjuster correspondence, settlement or repudiation letters and complaint records.  Public broker-service evidence supports the issue: the 2025 Gracechurch-BIBA survey reported that claims still lagged, with the UK Claims Monitor’s commercial insurer service NPS still in negative territory at -3 despite improvement. ([BIBA][10]) LexisNexis also found claims remained highly manual for brokers, with about 64% handling claims manually. ([LexisNexis Risk Solutions][3])

**Severity:** Medium-high to high. It is especially damaging where clients need urgent contractual evidence or claim progress.

---

## Summary ranking

| Rank | Problem                                                           | Main efficiency impact                                            |
| ---: | ----------------------------------------------------------------- | ----------------------------------------------------------------- |
|    1 | Split files across BMS, Outlook, SharePoint, portals and Teams    | Search time, duplicated work, missed instructions, audit risk     |
|    2 | Manual re-keying from emails, PDFs, spreadsheets and portal forms | Errors, slow quote/renewal turnaround, repeated checks            |
|    3 | Renewal document chasing and weak fair-presentation evidence      | Late renewals, referral loops, incomplete advice evidence         |
|    4 | Compliance evidence and file-quality workload                     | Internal rework, QA failures, delayed completion                  |
|    5 | Claims and post-bind documentation delays                         | Chasing, schedule/certificate corrections, poor client experience |

The realistic core issue is not simply “paperwork.” It is that commercial broking still depends on **document-heavy, multi-party workflows where the authoritative record, working documents, communications and portal outputs are often not the same thing**.

[1]: https://www.biba.org.uk/press-releases/biba-launches-national-insurance-broker-advertising-campaign/ "BIBA launches national insurance broker advertising campaign"
[2]: https://placingplatformlimited.com/ "Home - The London Market’s ePlacing Platform"
[3]: https://risk.lexisnexis.com/insights-resources/blog-post/commercial-insurance-brokers-digitally-minded-facing-challenges "Commercial Insurance Brokers Digitally-Minded, Facing Challenges with Data Enrichment Flowing into Prices - Insurance Insights"
[4]: https://www.opengi.co.uk/news/how-automation-is-transforming-insurance-for-brokers "How Automation Is Revolutionising Insurance for Brokers"
[5]: https://connect.avivab2b.co.uk/broker/support/online-services/integrated-trading/ "Aviva Broker: Integrated Trading - Aviva - Aviva"
[6]: https://www.legislation.gov.uk/ukpga/2015/4/part/2?utm_source=chatgpt.com "Insurance Act 2015"
[7]: https://www.biba.org.uk/press-releases/new-guidance-from-biba-seeks-a-clearer-approach-to-disclosure/ "New guidance from BIBA seeks a clearer approach to disclosure"
[8]: https://www.biba.org.uk/press-releases/regulation-costs-5-2-of-insurance-premiums/ "Regulation costs 5.2% of insurance premiums"
[9]: https://www.fca.org.uk/publications/thematic-reviews/tr24-2-general-insurance-pure-protection-product-governance "TR24/2: General insurance and pure protection product governance thematic review | FCA"
[10]: https://www.biba.org.uk/press-releases/gracechurch-biba-survey-insurers-focusing-on-service-over-price/ "Gracechurch-BIBA Survey"