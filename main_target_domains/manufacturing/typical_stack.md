Assumption: **mid-size UK MTO/ETO manufacturer** means roughly 50–500 staff, discrete or fabricated products, customer-specific orders, project/job costing, engineering change, supplier-heavy build, and ISO-style quality control. “Typical” means what is commonly seen or expected, not necessarily best-in-class.

## 1. Core 2025–2026 application stack

| Layer                                                    | Role in MTO/ETO manufacturing                                                                                                                                                                                                               | Typical software families                                                                                                                                                                   | Main records/documents                                                                                                |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Identity, email, productivity, collaboration**         | Daily working layer; Teams/SharePoint often becomes the informal document backbone.                                                                                                                                                         | Microsoft 365, Teams, SharePoint, OneDrive, Entra ID; sometimes Google Workspace.                                                                                                           | Emails, meeting notes, file shares, project folders, controlled/uncontrolled documents, policies.                     |
| **CRM + enquiry / bid management**                       | Tracks prospects, RFQs, customer communications, bid/no-bid, pipeline and quote status.                                                                                                                                                     | Dynamics 365 Sales, Salesforce, HubSpot, Zoho, ERP CRM modules.                                                                                                                             | RFQ, NDA, enquiry log, bid pack, requirements matrix, quote assumptions, proposal.                                    |
| **CPQ / estimating**                                     | Critical for MTO/ETO because margin is won or lost before order acceptance.                                                                                                                                                                 | ERP estimating module, Excel models, Configure-Price-Quote tools, bespoke calculators.                                                                                                      | Cost estimate, labour hours, materials take-off, risk allowance, margin approval, quote.                              |
| **ERP / MRP / finance**                                  | Central commercial and operational system of record: sales orders, jobs, purchasing, inventory, WIP, costing, invoicing.                                                                                                                    | Microsoft Dynamics 365 Business Central / Finance & Supply Chain, Epicor Kinetic, Infor CloudSuite Industrial, IFS Cloud, SAP Business One / S/4HANA, Sage X3/200, Access, EFACS, NetSuite. | Sales order, job/project, item master, BOM, routing, purchase orders, stock records, WIP, invoices, cost-to-complete. |
| **CAD / CAE / CAM**                                      | Engineering design and manufacturing preparation. More central in ETO than MTO.                                                                                                                                                             | SolidWorks, Autodesk Inventor/Fusion/Vault, Siemens NX, Solid Edge, CATIA, PTC Creo, AutoCAD, Mastercam, Fusion CAM, Alphacam, Bystronic/Trumpf nesting, Altium for electronics.            | 3D models, 2D drawings, simulations, CNC programs, nesting files, design calculations.                                |
| **PDM / PLM**                                            | Controls engineering data, revisions, approvals, product structure and change. Essential where drawings drive purchasing and manufacture.                                                                                                   | SolidWorks PDM, Autodesk Vault, Siemens Teamcenter, PTC Windchill, Dassault ENOVIA, Aras, Propel.                                                                                           | eBOM, drawing revisions, design release, ECR/ECO/ECN, approved manufacturer parts, design history.                    |
| **Project management / programme control**               | Needed because ETO jobs behave like projects, not simple repeat work orders.                                                                                                                                                                | MS Project, Primavera P6, Smartsheet, Monday.com, Jira, ERP project module.                                                                                                                 | Project plan, milestones, risk register, issue log, action log, customer reporting pack.                              |
| **APS / finite scheduling**                              | Handles constrained capacity, bottleneck work centres, skilled labour and long-lead materials.                                                                                                                                              | Siemens Opcenter APS/Preactor, PlanetTogether, Visual Planning, Orchestrate/Opcenter variants, ERP scheduling.                                                                              | Capacity plan, dispatch list, production schedule, bottleneck report, promise-date analysis.                          |
| **MES / shop-floor data capture**                        | Converts ERP jobs into execution: labour booking, operation status, barcode scanning, quality gates, traceability.                                                                                                                          | ERP shop-floor module, Tulip, Siemens Opcenter, Plex, Epicor Advanced MES, ProShop, Redzone, bespoke tablets/barcoding.                                                                     | Work order, traveller, route card, digital work instruction, labour booking, inspection result, NCR.                  |
| **QMS / EQMS**                                           | Controls ISO/customer/regulatory quality processes. ISO 9001 remains the common baseline quality framework for manufacturers; it covers QMS establishment, operation, performance evaluation and improvement. ([ISO][1])                    | Ideagen, ETQ, MasterControl, Greenlight Guru, Intelex, Q-Pulse, ERP QMS module, SharePoint-based QMS.                                                                                       | Quality manual, SOPs, audit records, NCR, CAPA, concessions, supplier approvals, calibration, training matrix.        |
| **Document management / controlled document repository** | Manages approved documents, versioning, access, retention and audit trails. In practice, this is often split between SharePoint and PDM/PLM unless disciplined.                                                                             | SharePoint, M-Files, DocuWare, OpenText, Egnyte, Box, PDM vault, QMS document module.                                                                                                       | Policies, procedures, work instructions, forms, templates, technical files, controlled drawings.                      |
| **Procurement / supplier portal / SRM**                  | Supplier-heavy ETO work needs quote comparison, long-lead tracking, subcontractor documentation and supplier quality.                                                                                                                       | ERP procurement, supplier portals, Jaggaer/Coupa for larger firms, SharePoint/Excel for smaller ones.                                                                                       | RFQ to supplier, PO, supplier quote, order acknowledgement, supplier certs, SCAR, delivery notes.                     |
| **WMS / barcode / labelling**                            | More relevant where inventory volume, batch/serial traceability or multiple sites exist.                                                                                                                                                    | ERP WMS, Zebra/BarTender/Loftware/NiceLabel, handheld scanners.                                                                                                                             | Bin records, pick lists, stock movements, labels, despatch paperwork, packing lists.                                  |
| **Maintenance / CMMS / EAM**                             | Maintains machines, calibration assets, tooling and facilities.                                                                                                                                                                             | Fiix, eMaint, MaintainX, UpKeep, IFS/Epicor/SAP maintenance modules.                                                                                                                        | Asset register, PM schedule, breakdown log, calibration cert, tooling register.                                       |
| **BI / reporting / data platform**                       | Replaces spreadsheet-only reporting with job margin, OTIF, WIP, quality and capacity dashboards.                                                                                                                                            | Power BI, Fabric, Azure SQL/Synapse, Qlik, Tableau, ERP analytics, Excel.                                                                                                                   | KPI dashboards, WIP ageing, margin reports, OTIF, NCR Pareto, utilisation, cashflow forecast.                         |
| **Integration / workflow automation**                    | Connects CRM, CAD/PDM, ERP, QMS, MES and finance. Avoids re-keying BOMs, job status and quality data.                                                                                                                                       | APIs, Power Automate, Azure Logic Apps, Boomi, MuleSoft, Zapier for light use, SQL integrations.                                                                                            | Integration logs, approval workflows, automated notifications, master-data sync.                                      |
| **OT / industrial systems**                              | PLCs, CNCs, SCADA, historians, sensors and machine connectivity. Increasingly connected to IT, but should not be treated like normal office IT.                                                                                             | PLC/SCADA platforms, OPC/Kepware, AVEVA/Wonderware, Ignition, OSIsoft PI/AVEVA PI, machine OEM systems.                                                                                     | OT asset register, network diagram, historian data, machine logs, backup images, access records.                      |
| **Cyber, backup, endpoint and compliance tooling**       | Protects IT/OT, supplier access, IP, customer data and operational continuity. Cyber Essentials is the UK Government-recommended minimum cyber-security standard, aligned to five technical controls. ([National Cyber Security Centre][2]) | MDM/Intune, Defender/CrowdStrike/SentinelOne, SIEM, backup/DR, privileged access, password vault, vulnerability scanning.                                                                   | Asset register, access reviews, backup logs, incident plan, supplier access records, Cyber Essentials evidence.       |

UK manufacturers are being pushed toward digitalisation through programmes such as **Made Smarter**, which supports manufacturing SMEs in digitising processes to improve productivity, overheads, quality, capacity and profit. ([Made Smarter][3])

## 2. Typical document stack by lifecycle stage

### A. Lead-to-order documents

| Stage            | Typical documents                                                                                                                            |
| ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Enquiry          | Customer enquiry, RFQ, NDA, drawings/specification received, tender pack, bid/no-bid assessment.                                             |
| Technical review | Requirements matrix, feasibility review, risk log, make/buy assessment, compliance checklist.                                                |
| Estimating       | Materials take-off, labour estimate, tooling estimate, subcontract estimate, contingency/risk allowance, margin approval.                    |
| Quotation        | Quote, proposal, assumptions/exclusions, delivery promise, payment terms, validity period, T&Cs.                                             |
| Contract review  | Customer PO, order acknowledgement, contract review record, specification gap analysis, export-control/product-compliance check if relevant. |

### B. Engineering and product-definition documents

| Stage              | Typical documents                                                                                               |
| ------------------ | --------------------------------------------------------------------------------------------------------------- |
| Design input       | Customer specification, user requirements, design brief, interface control document, applicable standards list. |
| Design output      | 3D CAD, 2D drawings, design calculations, simulation/FEA, tolerance stack-up, wiring diagrams, schematics.      |
| Product structure  | eBOM, mBOM, item master, approved parts list, substitute parts, make/buy flags.                                 |
| Review and release | Design review minutes, DFM/DFA review, risk assessment, FMEA where used, drawing release record.                |
| Change control     | Engineering change request, ECO/ECN, deviation, concession, redline drawing, revision history.                  |
| Compliance file    | Technical file, declaration of conformity, UKCA/CE evidence, test reports, risk assessment, standards evidence. |

For Great Britain, many manufactured goods can still use either **UKCA or CE marking** because current EU requirements, including CE marking, are recognised indefinitely for a range of product regulations; sector and Northern Ireland rules still need checking. ([GOV.UK][4])

### C. Planning, procurement and production documents

| Stage               | Typical documents                                                                                                                      |
| ------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Planning            | Project plan, job/work order, routing, capacity plan, production schedule, material availability report.                               |
| Procurement         | Supplier RFQ, PO, supplier order acknowledgement, delivery expediting log, approved supplier list.                                     |
| Incoming goods      | Goods receipt, material certificate, certificate of conformity, inspection record, batch/serial traceability.                          |
| Production          | Route card, traveller, work instruction, setup sheet, tooling list, weld procedure, CNC program, nesting file.                         |
| Shop-floor control  | Operation sign-off, labour booking, machine booking, rework instruction, hold point, inspection gate.                                  |
| Test and inspection | Inspection and test plan, dimensional report, electrical/mechanical test record, FAT/SAT, pressure/leak test, FAI/FAIR where required. |

### D. Quality, compliance and assurance documents

| Area            | Typical documents                                                                                             |
| --------------- | ------------------------------------------------------------------------------------------------------------- |
| QMS             | Quality policy, quality objectives, process maps, SOPs, controlled forms, management review.                  |
| Non-conformance | NCR, quarantine record, root-cause analysis, CAPA, 8D report, customer complaint, supplier corrective action. |
| Audit           | Internal audit plan, audit checklist, audit report, findings log, corrective action evidence.                 |
| Competence      | Training matrix, competency records, authorisations, toolbox talks, induction records.                        |
| Calibration     | Gauge register, calibration certificates, out-of-tolerance assessment, calibration schedule.                  |
| HSE/SHEQ        | Risk assessments, COSHH, method statements, permits, incident reports, environmental records.                 |

### E. Despatch, installation and aftermarket documents

| Stage    | Typical documents                                                                                               |
| -------- | --------------------------------------------------------------------------------------------------------------- |
| Despatch | Packing list, delivery note, commercial invoice, export documents, certificates, shipping labels.               |
| Handover | As-built drawings, as-built BOM, O&M manual, commissioning pack, warranty certificate, training material.       |
| Service  | Service report, spare parts list, field failure report, warranty claim, service history, upgrade/change record. |

## 3. System-of-record rule of thumb

A practical stack avoids one system trying to do everything:

| Data/document type                                      | Preferred system of record                                |
| ------------------------------------------------------- | --------------------------------------------------------- |
| Customer, opportunity, quote status                     | CRM / CPQ                                                 |
| Sales order, job, cost, purchasing, stock, WIP, invoice | ERP                                                       |
| CAD, drawings, engineering BOM, design revisions        | PDM / PLM                                                 |
| Manufacturing BOM, routing, work order                  | ERP, sometimes MES for execution detail                   |
| Work instructions and shop-floor execution              | MES or ERP shop-floor module                              |
| NCR, CAPA, audits, concessions                          | QMS / EQMS                                                |
| Controlled policies, SOPs, forms                        | QMS document control or SharePoint with strict governance |
| Project schedule, actions, milestones                   | Project tool or ERP project module                        |
| Machine, PLC, SCADA, OT network records                 | OT asset/security repository                              |
| KPIs and management reporting                           | BI layer, not direct spreadsheet extracts only            |

## 4. What differs between MTO and ETO

| Area               | MTO pattern                               | ETO pattern                                                                                  |
| ------------------ | ----------------------------------------- | -------------------------------------------------------------------------------------------- |
| Product definition | Product largely known before order.       | Product definition evolves after order.                                                      |
| Estimating         | Quicker, often based on variants/options. | Heavier estimating, risk allowance and technical assumptions.                                |
| BOM                | Existing BOM adapted.                     | New eBOM created; mBOM may lag design release.                                               |
| CAD/PDM            | Useful but not always dominant.           | Central system; drawing and revision discipline are critical.                                |
| ERP                | Job costing, MRP and delivery control.    | Project accounting, milestone billing and change-order control become more important.        |
| MES                | Operation tracking and labour capture.    | Also needs strong deviation, concession and as-built traceability.                           |
| Document risk      | Wrong revision or missing certs.          | Scope creep, uncontrolled engineering change, late supplier input, unclear design authority. |

## 5. UK-specific 2025–2026 guardrails

| Area                       | Practical implication                                                                                                                                                                                                                                                                                                            |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Quality**                | ISO 9001-style documented information, audit trails, competence records, process control and continual improvement remain the normal baseline for serious B2B manufacturing. ([ISO][1])                                                                                                                                          |
| **Product marking**        | Keep a technical-file approach for regulated products. CE/UKCA flexibility exists for many GB product categories, but product-sector, customer, export and Northern Ireland rules must be checked. ([GOV.UK][4])                                                                                                                 |
| **Cyber security**         | Cyber Essentials is increasingly a supply-chain requirement; for manufacturers, include suppliers, remote access, backups, MFA, patching and privileged access in the evidence pack. ([National Cyber Security Centre][2])                                                                                                       |
| **OT security**            | Maintain a living OT “definitive record”: components, connectivity, zones/segmentation, resilience arrangements, suppliers and third-party access. NCSC guidance explicitly frames this as necessary because OT now interacts with enterprise IT, cloud platforms and remote vendor tools. ([National Cyber Security Centre][5]) |
| **Data protection**        | UK GDPR and the Data Protection Act 2018 remain relevant; the Data Use and Access Act 2025 changes parts of the regime but does not replace UK GDPR or the DPA. ([GOV.UK][6])                                                                                                                                                    |
| **AI/document automation** | Use AI first around quoting support, document extraction, supplier chasing, NCR classification, visual inspection support and knowledge search. Do not make it the uncontrolled source of truth for drawings, compliance decisions or released documents.                                                                        |

## 6. Typical maturity levels

### Minimum viable stack

For a smaller mid-size manufacturer:

* Microsoft 365 + SharePoint.
* ERP with MRP, purchasing, inventory, finance and job costing.
* CAD + basic PDM or controlled vault.
* Excel-based estimating, but controlled templates.
* QMS in SharePoint or a light EQMS.
* Barcode/labour booking at key shop-floor points.
* Power BI or ERP dashboards.
* Cyber Essentials evidence pack.

### Good 2025–2026 target stack

For a stronger MTO/ETO manufacturer:

* CRM + CPQ/estimating integrated to ERP.
* ERP as the commercial and manufacturing backbone.
* PDM/PLM integrated to ERP for released BOMs and revisions.
* APS for finite capacity and bottleneck scheduling.
* MES for work instructions, labour, WIP, quality gates and traceability.
* EQMS for NCR/CAPA/audits/concessions.
* Document-control layer with clear ownership and retention.
* BI/data warehouse for margin, OTIF, WIP, quality and capacity.
* IT/OT cyber controls, MFA, backups, supplier access governance and OT asset records.

### Manufacturer's Categories We Avoid

We don't target regulated, aerospace, defence, automotive, medical or complex capital-equipment firms!

## 7. Common failure pattern

The most common weak stack is:

**CRM in one place, estimating in Excel, drawings in shared drives, BOMs retyped into ERP, work instructions printed from uncontrolled folders, NCRs in spreadsheets, and project status held in meetings.**

The target is not more software by default. The target is clear ownership of:

1. **Customer requirement**
2. **Released design**
3. **Released BOM/routing**
4. **Approved supplier and material**
5. **Controlled work instruction**
6. **Inspection/test evidence**
7. **As-built/as-delivered record**
8. **Commercial cost and margin**

For MTO/ETO, the highest-value integrations are usually **CRM/CPQ → ERP**, **PDM/PLM → ERP**, **ERP → MES**, and **QMS ↔ ERP/PLM**.

[1]: https://www.iso.org/standard/62085.html "ISO 9001:2015 - Quality management systems — Requirements"
[2]: https://www.ncsc.gov.uk/cyberessentials/overview "Cyber Essentials | National Cyber Security Centre"
[3]: https://www.madesmarter.uk/ "UK Digital Manufacturing advice & innovation | Made Smarter"
[4]: https://www.gov.uk/guidance/placing-manufactured-goods-on-the-market-in-great-britain "Placing manufactured products on the market in Great Britain - GOV.UK"
[5]: https://www.ncsc.gov.uk/blog-post/understanding-ot-environment-1step-stronger-cyber-security "Understanding your OT environment: the first step to stronger cyber security | National Cyber Security Centre"
[6]: https://www.gov.uk/guidance/data-use-and-access-act-2025-data-protection-and-privacy-changes "Data (Use and Access) Act 2025: data protection and privacy changes - GOV.UK"
