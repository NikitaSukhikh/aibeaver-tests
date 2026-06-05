# MultiHiertt Mini Financial Reasoning Package

This package is a 50-example curated subset of the public MultiHiertt dev split. It is intended as an MCD example for hybrid reasoning over financial report prose, multiple source tables, cell-level evidence, and executable arithmetic programs.

The source benchmark stores each document as paragraphs plus multiple HTML tables. This MCD package normalizes those records into queryable CSV tables while preserving the original example IDs, table indexes, row indexes, column indexes, and evidence refs.

## Package Reference Map

- `multihiertt_examples` stores one row per selected benchmark example.
- `multihiertt_paragraphs` stores source paragraphs and marks text evidence rows.
- `multihiertt_source_tables` stores one row per original HTML table.
- `multihiertt_table_rows` stores each original table row as a fixed-width row matrix.
- `multihiertt_cells` stores each table cell with the original `table-row-column` ref.
- MultiHiertt cell refs use zero-based `table_index-row_index-col_index`, such as `0-2-4`.

## Reasoning Notes

For arithmetic questions, use `qa_program` from `multihiertt_examples` as the gold reasoning program when present. The program uses functions such as `add`, `subtract`, `multiply`, and `divide`; intermediate results are referenced as `#0`, `#1`, and so on.

For evidence-grounded answers, inspect `multihiertt_paragraphs.is_text_evidence` and `multihiertt_cells.is_table_evidence`. The row matrix table is useful for scanning table shape, while the cell table is better for exact evidence references.

## MHDEV-0001

Source UID: `7d840731012a4a09a735eeee286c364b`.

Question: Which year is Total Revenues of Group retirement products the most?

Gold answer: `2006`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 0: American International Group, Inc.  and Subsidiaries Management’s Discussion and Analysis of Financial Condition and Results of Operations Continued Domestic Retirement Services Results Domestic Retirement Services results, presented on a sub-product basis for 2007, 2006 and 2005 were as follows:

Original table evidence refs: `0-14-4, 0-2-4, 0-8-4`.

Source tables for this example: `mhdev_0001_table_0, mhdev_0001_table_1, mhdev_0001_table_2, mhdev_0001_table_3`.

## MHDEV-0002

Source UID: `63260a43bc4e4632a0317eb820caf964`.

Question: What will Distribution fees reach in 2010 if it continues to grow at its current rate? (in millions)

Gold answer: `1570.75785`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(1733,1912), divide(#0,1912), add(const_1,#1), multiply(#2,1733)`

Evidence paragraphs:

- Paragraph 32: The following table presents the results of operations of our Advice & Wealth Management segment:

Original table evidence refs: `2-5-1, 2-5-2`.

Source tables for this example: `mhdev_0002_table_0, mhdev_0002_table_1, mhdev_0002_table_2, mhdev_0002_table_3`.

## MHDEV-0003

Source UID: `7f9cd61fc4264c9bb81cdcfd2c5c4c38`.

Question: What was the total amount of Amount in 2007 for Financial Services Businesses ? (in million)

Gold answer: `8228`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 62: Investment Results The following tables set forth the income yield and investment income, excluding realized investment gains (losses), for each major investment category of our general account for the periods indicated.

Original table evidence refs: `2-15-2`.

Source tables for this example: `mhdev_0003_table_0, mhdev_0003_table_1, mhdev_0003_table_2, mhdev_0003_table_3`.

## MHDEV-0004

Source UID: `b7642f569ac54d28af0a4a16683d3f35`.

Question: Does the average value of Power purchase agreements in Entergy Arkansas greater than that in Entergy Louisiana?

Gold answer: `yes`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 20: Significant components of accumulated deferred income taxes and taxes accrued for the Registrant Subsidiaries as of December 31, 2011 and 2010 are as follows:

Original table evidence refs: `1-5-1, 1-5-3`.

Source tables for this example: `mhdev_0004_table_0, mhdev_0004_table_1, mhdev_0004_table_2, mhdev_0004_table_3`.

## MHDEV-0005

Source UID: `5cc19228085048228131f5d77196655d`.

Question: What is the ratio of Securities to the total for Net realized losses reclassified into earnings in 2008?

Gold answer: `0.66977`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(1797,2683)`

Evidence paragraphs:

- Paragraph 86: Accumulated OCI The following table presents the changes in accumulated OCI for 2008, 2007 and 2006, net-of-tax.
- Paragraph 88: (1) In 2008, 2007 and 2006, the Corporation reclassified net realized losses into earnings on the sales and other-than-temporary impairments of AFS debt securities of $1.4 billion, $137 million and $279 million, net-of-tax, respectively, and net realized (gains) losses on the sales and other-than-temporary impairments of AFS marketable equity securities of $377 million, $(284) million, and $(499) million, net-of-tax, respectively.

Original table evidence refs: `2-3-1, 2-3-5`.

Source tables for this example: `mhdev_0005_table_0, mhdev_0005_table_1, mhdev_0005_table_2, mhdev_0005_table_3`.

## MHDEV-0006

Source UID: `1ca146715d8b4ed9a102b68af5bdd385`.

Question: How many Below Investment Grade exceed the average of Below Investment Grade in 2004?

Gold answer: `1`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 45: The following table shows the Company’s exposure to asset-backed securities supported by sub-prime mortgage loans by credit quality and by vintage year:

Original table evidence refs: `1-7-10, 1-7-9`.

Source tables for this example: `mhdev_0006_table_0, mhdev_0006_table_1, mhdev_0006_table_2, mhdev_0006_table_3`.

## MHDEV-0007

Source UID: `a60e6202dde64cbb9c7eb29ed5fd3fe2`.

Question: containerboards net sales represented what percentage of industrial packaging sales in 2005?

Gold answer: `0.18136`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(895,4935)`

Evidence paragraphs:

- Paragraph 111: Containerboard’s net sales totaled $895 million in 2005, $951 million in 2004 and $815 million in 2003.
- Paragraph 120: Net sales totaled $468 million in 2005, $723 million in 2004 and $690 million in 2003.
- Paragraph 122: U. S.  Converting Operations net sales for 2005 were $2.6 billion compared with $2.3 billion in 2004 and $1.9 billion in 2003.
- Paragraph 126: European Container sales for 2005 were $883 million compared with $865 million in 2004 and $801 million in 2003.

Original table evidence refs: `3-1-1`.

Source tables for this example: `mhdev_0007_table_0, mhdev_0007_table_1, mhdev_0007_table_2, mhdev_0007_table_3`.

## MHDEV-0008

Source UID: `b6e47615b28841deaacce680de41c65c`.

Question: What's the difference of Securities America, Inc.-3(4) between 2010 and 2009 forActual Capital? (in million)

Gold answer: `-13.0`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(2,15)`

Evidence paragraphs:

- Paragraph 19: Actual capital and regulatory capital requirements as of December 31 for our wholly owned subsidiaries subject to regulatory capital requirements were as follows:

Original table evidence refs: `0-14-1, 0-14-2`.

Source tables for this example: `mhdev_0008_table_0, mhdev_0008_table_1, mhdev_0008_table_2`.

## MHDEV-0009

Source UID: `9b1a8a210c654f1aada293d3ea35429e`.

Question: What is the ratio of Total cards-in-force in Table 1 to the Other in Table 0 in 2016?

Gold answer: `0.34421`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(32.7,95)`

Evidence paragraphs:

- Paragraph 23: TABLE 3: PROVISIONS FOR LOSSES SUMMARY
- Paragraph 34: (a) Refer to Table 7 footnote (a).

Original table evidence refs: `0-4-2, 1-4-2`.

Source tables for this example: `mhdev_0009_table_0, mhdev_0009_table_1, mhdev_0009_table_2`.

## MHDEV-0010

Source UID: `6a6d7accb802496fa8e7ed474f117d38`.

Question: In the year / section with largest amount of Average contract revenue per MWh, what's the sum of Planned net MW in operation?

Gold answer: `4200`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 13: Following is a summary of the amount of the Non-Utility Nuclear business' installed capacity that is currently sold forward, and the blended amount of the Non-Utility Nuclear business' planned generation output and installed capacity that is currently sold forwar

Original table evidence refs: `0-6-4`.

Source tables for this example: `mhdev_0010_table_0, mhdev_0010_table_1, mhdev_0010_table_2, mhdev_0010_table_3, mhdev_0010_table_4, mhdev_0010_table_5`.

## MHDEV-0011

Source UID: `b06dcff918b84dbc8bdc39df31d6c355`.

Question: What is the average value of Total revenues in Table 2 and Restricted stock awards in Table 1 in 2007? (in million)

Gold answer: `4403.5`.

Question type: `arithmetic`.

Gold reasoning program:

`add(8755,52), divide(#0,2)`

Evidence paragraphs:

- Paragraph 29: The components of the Company’s share-based compensation expense, net of forfeitures, were as follows:
- Paragraph 58: Consolidated Results of Operations Year Ended December 31, 2008 Compared to Year Ended December 31, 2007 The following table presents our consolidated results of operations:

Original table evidence refs: `1-4-3, 2-9-2`.

Source tables for this example: `mhdev_0011_table_0, mhdev_0011_table_1, mhdev_0011_table_2`.

## MHDEV-0012

Source UID: `0fc058f14a954e6eb3d22d45a76ef981`.

Question: What was the total amount of Allowance greater than 270 in 2018? (in million)

Gold answer: `1918.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(271,1350), add(#0,297)`

Original table evidence refs: `4-2-1, 4-3-1, 4-6-1`.

Source tables for this example: `mhdev_0012_table_0, mhdev_0012_table_1, mhdev_0012_table_2, mhdev_0012_table_3, mhdev_0012_table_4`.

## MHDEV-0013

Source UID: `a779b55236c7402fb7a09102e4295673`.

Question: What is the sum of Aircraft on Firm Order in 2009?

Gold answer: `32.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(5,11), add(#0,6), add(#1,10)`

Evidence paragraphs:

- Paragraph 27: Table of Contents Index to Financial Statements Our purchase commitments (firm orders) for aircraft, as well as options to purchase additional aircraft, as of December 31, 2008 are shown in the following tables:
- Paragraph 29: (1) Includes 31 aircraft, which we have entered into definitive agreements to sell to third parties immediately following delivery of these aircraft to us by the manufacturer.

Original table evidence refs: `1-3-1, 1-4-1, 1-7-1`.

Source tables for this example: `mhdev_0013_table_0, mhdev_0013_table_1, mhdev_0013_table_2, mhdev_0013_table_3`.

## MHDEV-0014

Source UID: `723cdadfdcfc48f68cc952f98977cf62`.

Question: In which year is Other Expense greater than 30000?

Gold answer: `2007 2008`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 75: Results of Operations - Other The following table presents consolidated financial information for the Other segment for the years indicated:

Original table evidence refs: `2-7-3, 2-7-5`.

Source tables for this example: `mhdev_0014_table_0, mhdev_0014_table_1, mhdev_0014_table_2`.

## MHDEV-0015

Source UID: `404ce5c5eb06402d8172096ca3cd0bd1`.

Question: What is the sum of the Cost of sales in the years where Net sales is greater than 1000? (in million)

Gold answer: `1867.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(884,983)`

Evidence paragraphs:

- Paragraph 50: The following table presents summary operating data for our ammonia segment, including the impact of our acquisition of the remaining 50% equity interest in CF Fertilisers UK:

Original table evidence refs: `3-4-2, 3-4-3`.

Source tables for this example: `mhdev_0015_table_0, mhdev_0015_table_1, mhdev_0015_table_2, mhdev_0015_table_3`.

## MHDEV-0016

Source UID: `9b2dc866091743d7b190417a4307a3c4`.

Question: what was the change in advertising costs from 2001 to 2002?

Gold answer: `210000.0`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(267000,57000)`

Evidence paragraphs:

- Paragraph 33: Advertising costs were approximately $440,000 for 2003, $267,000 for 2002 and $57,000 for 2001.

Original table evidence refs: `none`.

Source tables for this example: `mhdev_0016_table_0, mhdev_0016_table_1, mhdev_0016_table_2, mhdev_0016_table_3`.

## MHDEV-0017

Source UID: `bbcbe3ddf43449a08763a2f7d7986260`.

Question: What is the sum amount of Capital lease obligations in the years with the lowest amount of Operating lease obligations? (in dollars in millions)

Gold answer: `4`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 37: Contractual Obligations The following table summarizes our known obligations to make future payments pursuant to certain contracts as of December 31, 2012, and the estimated timing thereof.

Original table evidence refs: `1-4-4, 1-5-1, 1-5-2, 1-5-3, 1-5-4, 1-5-5`.

Source tables for this example: `mhdev_0017_table_0, mhdev_0017_table_1, mhdev_0017_table_2`.

## MHDEV-0018

Source UID: `161facf717424d17af248fcb4fdb738a`.

Question: What is the growth rate of Balance between December 31, 2008 and December 31, 2009?

Gold answer: `-0.06413`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(25392,27132), divide(#0,27132)`

Evidence paragraphs:

- Paragraph 53: GOODWILL AND INTANGIBLE ASSETS Goodwill The changes in Goodwill during 2008 and 2009 were as follows:
- Paragraph 55: The changes in Goodwill by segment during 2008 and 2009 were as follows:

Original table evidence refs: `2-10-1, 2-16-1`.

Source tables for this example: `mhdev_0018_table_0, mhdev_0018_table_1, mhdev_0018_table_2, mhdev_0018_table_3`.

## MHDEV-0019

Source UID: `05be07b07d5a44ca8398c7ec38271bc6`.

Question: what is the pre-tax aggregate net unrealized loss in 2008?

Gold answer: `26.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(15.8,10.2)`

Evidence paragraphs:

- Paragraph 9: During the years ended December 31, 2008 and 2007, the Company recorded an aggregate net unrealized loss of approximately $15.8 million and $3.2 million, respectively (net of a tax provision of approximately $10.2 million and $2.0 million, respectively) in other comprehensive loss for the change in fair value of interest rate swaps designated as cash flow hedges and reclassified an aggregate of $0.1 million and $6.2 million, respectively (net of an income tax provision of $2.0 million and an income tax benefit of $3.3 million, respectively) into results of operations.9.

Original table evidence refs: `none`.

Source tables for this example: `mhdev_0019_table_0, mhdev_0019_table_1, mhdev_0019_table_2`.

## MHDEV-0020

Source UID: `ce038f0f07ed4f90a13b4134d41bfa3e`.

Question: In the year with largest amount of government, what's the increasing rate of education?

Gold answer: `-0.00932`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(1807,1824), divide(#0,1824)`

Evidence paragraphs:

- Paragraph 20: Net sales Net sales by segment, in dollars and as a percentage of total Net sales, and the year-over-year dollar and percentage change in Net sales for the years ended December 31, 2015 and 2014 are as follows:

Original table evidence refs: `1-9-1, 1-9-3`.

Source tables for this example: `mhdev_0020_table_0, mhdev_0020_table_1, mhdev_0020_table_2, mhdev_0020_table_3`.

## MHDEV-0021

Source UID: `7389cfa35a894e14bf0773e29d326973`.

Question: What's the sum of Debt maturities of Thereafter, and Capital lease obligations of Less than 1 year ?

Gold answer: `6905.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(2525.0,4380.0)`

Original table evidence refs: `0-2-5, 2-3-1`.

Source tables for this example: `mhdev_0021_table_0, mhdev_0021_table_1, mhdev_0021_table_2, mhdev_0021_table_3`.

## MHDEV-0022

Source UID: `032145bd6fdd4712b05cd5495f7c8f35`.

Question: What is the proportion of Asset Management to the total Mortgage and other loans receivable, net of allowance in 2006?

Gold answer: `0.17186`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(4884,28418)`

Original table evidence refs: `1-12-4, 1-12-6`.

Source tables for this example: `mhdev_0022_table_0, mhdev_0022_table_1, mhdev_0022_table_2`.

## MHDEV-0023

Source UID: `9df041a1ce9440c2aaaf77f773811fcb`.

Question: What was the total amount of Amount greater than 5000 in 2013?

Gold answer: `87700.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(62357,5598), add(#0,19745)`

Original table evidence refs: `3-11-1, 3-2-1, 3-5-1`.

Source tables for this example: `mhdev_0023_table_0, mhdev_0023_table_1, mhdev_0023_table_2, mhdev_0023_table_3`.

## MHDEV-0024

Source UID: `071e671820fa4f89b003923a38b03741`.

Question: what was the percentage change in the allowance for loan losses from 2008 to 2009?

Gold answer: `0.83756`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(29616,16117), divide(#0,16117)`

Original table evidence refs: `1-1-1, 1-1-2`.

Source tables for this example: `mhdev_0024_table_0, mhdev_0024_table_1, mhdev_0024_table_2`.

## MHDEV-0025

Source UID: `4251b0c576c3429085b0f79fe3594b32`.

Question: What is the growing rate of Net credit losses in the year with the most Provision for benefits and claims?

Gold answer: `0.75282`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(24585,14026), divide(#0,14026)`

Evidence paragraphs:

- Paragraph 53: Citi Holdings consists of the following: Brokerage and Asset Management, Local Consumer Lending, and Special Asset Pool.

Original table evidence refs: `1-5-2, 1-5-3`.

Source tables for this example: `mhdev_0025_table_0, mhdev_0025_table_1, mhdev_0025_table_2`.

## MHDEV-0026

Source UID: `f1b58737e9a34f60b4882c8b7226395e`.

Question: What do all collateralized financings sum up in 2018 , excluding Repurchase agreements and Securities loaned? (in million)

Gold answer: `21433`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 44: The table below presents information about our funding sources.

Original table evidence refs: `3-6-1`.

Source tables for this example: `mhdev_0026_table_0, mhdev_0026_table_1, mhdev_0026_table_2, mhdev_0026_table_3`.

## MHDEV-0027

Source UID: `b86d620b573c45ffae2f15fb5a02e688`.

Question: In the year with the most other revenues , what is the growth rate of General and administrative expense? (in million)

Gold answer: `13.36364`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(-12,33), add(#0,1), multiply(#1,21)`

Evidence paragraphs:

- Paragraph 26: Corporate & Other The following table presents the results of operations of our Corporate & Other segment on an operating basis:

Original table evidence refs: `1-12-1, 1-12-2, 1-12-3`.

Source tables for this example: `mhdev_0027_table_0, mhdev_0027_table_1, mhdev_0027_table_2, mhdev_0027_table_3`.

## MHDEV-0028

Source UID: `9e8eb2e5a768431c99abaef9de32a4ec`.

Question: as of february 19 , 2016 what was the market capitalization

Gold answer: `37014734589.92`.

Question type: `arithmetic`.

Gold reasoning program:

`multiply(423897556,87.32)`

Evidence paragraphs:

- Paragraph 3: On February 19, 2016, the closing price of our common stock was $87.32 per share as reported on the NYSE.
- Paragraph 4: As of February 19, 2016, we had 423,897,556 outstanding shares of common stock and 159 registered holders.

Original table evidence refs: `none`.

Source tables for this example: `mhdev_0028_table_0, mhdev_0028_table_1, mhdev_0028_table_2, mhdev_0028_table_3`.

## MHDEV-0029

Source UID: `e4d6c1e51b0b49d895b73472bb9f0dc0`.

Question: What was the total amount of Net interest revenue and Non-interest revenue in 2009 ? (in million)

Gold answer: `9789.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(5651,4138)`

Original table evidence refs: `2-1-1, 2-2-1`.

Source tables for this example: `mhdev_0029_table_0, mhdev_0029_table_1, mhdev_0029_table_2`.

## MHDEV-0030

Source UID: `612ad8b5f4f94223b2e4b3d38a00951f`.

Question: What is the sum of the amount of Equity securities in the range of 50 million and 100 million? (in million)

Gold answer: `131.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(58,73)`

Evidence paragraphs:

- Paragraph 21: The following tables set forth the income yield and investment income, excluding realized investment gains (losses) and non-hedge accounting derivative results, for each major investment category of our Japanese operations’ general account for the periods indicated.

Original table evidence refs: `1-5-2, 1-5-4`.

Source tables for this example: `mhdev_0030_table_0, mhdev_0030_table_1, mhdev_0030_table_2, mhdev_0030_table_3`.

## MHDEV-0031

Source UID: `d67cd399e6b94bb4a6cdb39afaf0f8f4`.

Question: what was the percentage change in cash from operations between 2008 and 2009?

Gold answer: `0.35413`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(868,641), divide(#0,641)`

Original table evidence refs: `0-1-2, 0-1-3`.

Source tables for this example: `mhdev_0031_table_0, mhdev_0031_table_1, mhdev_0031_table_2, mhdev_0031_table_3, mhdev_0031_table_4, mhdev_0031_table_5, mhdev_0031_table_6`.

## MHDEV-0032

Source UID: `11904e0323e04189a6d0c03ebec8c27f`.

Question: What was the average of the Total operating revenues in the year where Other investment income/(losses) is positive? (in million)

Gold answer: `1162.56667`.

Question type: `arithmetic`.

Gold reasoning program:

`add(3532.7,0.3), subtract(#0,45.3), divide(#1,const_3)`

Original table evidence refs: `2-2-1, 2-2-2, 2-2-3, 2-2-4`.

Source tables for this example: `mhdev_0032_table_0, mhdev_0032_table_1, mhdev_0032_table_2, mhdev_0032_table_3`.

## MHDEV-0033

Source UID: `7ba60c94b1534e128a1841bbbb1a382e`.

Question: What's the sum of Collections reinvested in revolving period securitizations in terms of Home Equity in 2009? (in dollars in millions)

Gold answer: `177`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 27: The following table summarizes selected information related to home equity and automobile loan securitizations at and for the year ended December 31, 2009 and 2008.

Original table evidence refs: `1-5-2`.

Source tables for this example: `mhdev_0033_table_0, mhdev_0033_table_1, mhdev_0033_table_2`.

## MHDEV-0034

Source UID: `000682417fd9450bb10fee113dae5fcc`.

Question: What will principal transaction be like in 2013 if it develops with the same increasing rate as current?

Gold answer: `82.23539`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(93.1,105.4), divide(#0,105.4), add(#1,const_1), multiply(#2,93.1)`

Evidence paragraphs:

- Paragraph 30: Revenue The components of revenue and the resulting variances are as follows (dollars in millions):

Original table evidence refs: `2-5-1, 2-5-2`.

Source tables for this example: `mhdev_0034_table_0, mhdev_0034_table_1, mhdev_0034_table_2, mhdev_0034_table_3, mhdev_0034_table_4`.

## MHDEV-0035

Source UID: `91afe10a7407428c9bbad202945e060e`.

Question: what was the average operating leases 2014rental expense for operating leases from 2009 to 2011

Gold answer: `45.33333`.

Question type: `arithmetic`.

Gold reasoning program:

`add(44,44), add(#0,48), divide(#1,const_3)`

Evidence paragraphs:

- Paragraph 21: Operating Leases—Rental expense for operating leases was $44 million in 2011, $44 million in 2010, and $48 million in 2009.

Original table evidence refs: `0-5-1`.

Source tables for this example: `mhdev_0035_table_0, mhdev_0035_table_1, mhdev_0035_table_2, mhdev_0035_table_3`.

## MHDEV-0036

Source UID: `abb228ebc069473dbd8a62729def4b35`.

Question: what is the highest total amount of North Sea?

Gold answer: `18`.

Question type: `span_selection`.

Evidence paragraphs:

- Paragraph 66: Productive Wells The number of productive crude oil and natural gas wells in which we held an interest at December 31, 2010 was as follows:

Original table evidence refs: `2-5-1`.

Source tables for this example: `mhdev_0036_table_0, mhdev_0036_table_1, mhdev_0036_table_2, mhdev_0036_table_3, mhdev_0036_table_4`.

## MHDEV-0037

Source UID: `ae2ce9e907114dd786d4a02437917f15`.

Question: What is the sum of Securities loaned in 2017 and Aggregate contractual principal in excess of fair value in 2015? (in million)

Gold answer: `24393.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(14793,9600)`

Evidence paragraphs:

- Paragraph 38: In the table below, the aggregate contractual principal amount of loans on nonaccrual status and/or more than 90 days past due (which excludes loans carried at zero fair value and considered uncollectible) exceeds the related fair value primarily because the firm regularly purchases loans, such as distressed loans, at values significantly below the contractual principal amounts.
- Paragraph 44: The table below presents information about our funding sources.

Original table evidence refs: `2-5-2, 3-5-3`.

Source tables for this example: `mhdev_0037_table_0, mhdev_0037_table_1, mhdev_0037_table_2, mhdev_0037_table_3`.

## MHDEV-0038

Source UID: `930465d2a8a14fbc9c3de57267a5f067`.

Question: What is the average increasing rate of Purchased power between 2017 and 2018? (in million)

Gold answer: `199.5`.

Question type: `arithmetic`.

Gold reasoning program:

`add(208,191), divide(#0,const_2)`

Original table evidence refs: `1-3-3, 1-3-6`.

Source tables for this example: `mhdev_0038_table_0, mhdev_0038_table_1, mhdev_0038_table_2, mhdev_0038_table_3, mhdev_0038_table_4`.

## MHDEV-0039

Source UID: `6b77c2a63b8d4c268d745c78abf7db2a`.

Question: What will Total trading account assets be like in 2011 if it continues to grow at the same rate as it did in 2010? (in million)

Gold answer: `207988.75032`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(194671,182206), divide(#0,182206), add(const_1,#1), multiply(194671,#2)`

Evidence paragraphs:

- Paragraph 0: NOTE 3 Trading Account Assets and Liabilities The table below presents the components of trading account assets and liabilities at December 31, 2010 and 2009.

Original table evidence refs: `0-8-1, 0-8-2`.

Source tables for this example: `mhdev_0039_table_0, mhdev_0039_table_1, mhdev_0039_table_2`.

## MHDEV-0040

Source UID: `8caf20e28a314f43a0bc3fdbadcc2220`.

Question: What is the growing rate of BENEFIT OBLIGATION AT END OF YEAR for Con Edison in the year with the least Benefit obligation at beginning of year for Con Edison?

Gold answer: `0.01147`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(1411,1395), divide(#0,1395)`

Original table evidence refs: `1-11-2, 1-11-3, 1-3-1, 1-3-2, 1-3-3`.

Source tables for this example: `mhdev_0040_table_0, mhdev_0040_table_1, mhdev_0040_table_2`.

## MHDEV-0041

Source UID: `70ee07d30a8b46e195c791b6d69b9534`.

Question: What's the total amount of the Net income for Amount in the years where Operating activities for Total cash provided by (used in) is greater than 1760? (in million)

Gold answer: `6708.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(4313,2395)`

Evidence paragraphs:

- Paragraph 70: Cash Flows The following table summarizes our cash flows from operating, investing and financing activities for each of the past three fiscal years ($ in millions):

Original table evidence refs: `3-2-1, 3-2-2, 3-2-3, 5-4-1, 5-4-2`.

Source tables for this example: `mhdev_0041_table_0, mhdev_0041_table_1, mhdev_0041_table_2, mhdev_0041_table_3, mhdev_0041_table_4, mhdev_0041_table_5`.

## MHDEV-0042

Source UID: `6cd056489ef745088e88f09c847c8ad9`.

Question: as of december 31 , 2017 , what was the percent of the 2016 program remaining available for purchase

Gold answer: `0.48`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(1.2,2.5)`

Evidence paragraphs:

- Paragraph 74: (b) On September 21, 2016, we announced that our board of directors authorized our purchase of up to $2.5 billion of our outstanding common stock (the 2016 program) with no expiration date.
- Paragraph 75: As of December 31, 2017, we had $1.2 billion remaining available for purchase under the 2016 program.
- Paragraph 76: On January 23, 2018, we announced that our board of directors authorized our purchase of up to an additional $2.5 billion of our outstanding common stock with no expiration date.

Original table evidence refs: `none`.

Source tables for this example: `mhdev_0042_table_0, mhdev_0042_table_1, mhdev_0042_table_2, mhdev_0042_table_3`.

## MHDEV-0043

Source UID: `e258d39d9df44652a28ca25d0304b0ed`.

Question: In the year with the most Total fixed rate debt, what is the amount of Variable rate debt and total?

Gold answer: `8342.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(3051,5291)`

Evidence paragraphs:

- Paragraph 21: Part II, Item 7A The following table represents principal amounts of Schlumberger’s debt at December 31, 2008 by year of maturity:

Original table evidence refs: `2-10-6, 2-9-6`.

Source tables for this example: `mhdev_0043_table_0, mhdev_0043_table_1, mhdev_0043_table_2, mhdev_0043_table_3`.

## MHDEV-0044

Source UID: `05d560d08fbc406990e7b02b415aa60a`.

Question: what's the total amount of Loss expenses Casualty of 2008 Gross, and Case reserves of 2009 Gross ?

Gold answer: `21178.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(3871.0,17307.0)`

Evidence paragraphs:

- Paragraph 21: The following table shows our total reserves segregated between case reserves (including loss expense reserves) and IBNR reserves at December 31, 2009 and 2008.

Original table evidence refs: `2-2-1, 3-9-4`.

Source tables for this example: `mhdev_0044_table_0, mhdev_0044_table_1, mhdev_0044_table_2, mhdev_0044_table_3`.

## MHDEV-0045

Source UID: `0bcf9238356d41029754e323fa14108d`.

Question: What is the proportion of Pensions' Service cost of of net periodic benefit cost in U.S. Plans to the total in 2006?

Gold answer: `0.625`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(130,208)`

Evidence paragraphs:

- Paragraph 17: Employee Benefits Continued (i) Components of net periodic benefit cost and other amounts recognized in other comprehensive income: The following table presents the components of net periodic benefit cost recognized in income and other amounts recognized in other comprehensive income with respect to the defined benefit pension plans and other postretirement benefit plans for the year ended December 31, 2006 (no amounts were recognized in other comprehensive income for the years ended 2005 and 2004):

Original table evidence refs: `1-4-2, 1-4-3`.

Source tables for this example: `mhdev_0045_table_0, mhdev_0045_table_1, mhdev_0045_table_2`.

## MHDEV-0046

Source UID: `2a9928d6aa7a42b9b76531cf98982a26`.

Question: What is the total amount of Net cash used in financing activities of 2010, Individual fixed annuities of Net Investment Income, and Group retirement products of Total Revenues ?

Gold answer: `15200.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(9261.0,3664.0), add(#0,2275.0)`

Evidence paragraphs:

- Paragraph 0: American International Group, Inc.  and Subsidiaries Management’s Discussion and Analysis of Financial Condition and Results of Operations Continued Domestic Retirement Services Results Domestic Retirement Services results, presented on a sub-product basis for 2007, 2006 and 2005 were as follows:
- Paragraph 27: ITEM 7 / LIQUIDITY AND CAPITAL RESOURCES The following table presents a summary of AIG’s Consolidated Statement of Cash Flows:

Original table evidence refs: `0-2-4, 0-3-2, 2-4-3`.

Source tables for this example: `mhdev_0046_table_0, mhdev_0046_table_1, mhdev_0046_table_2, mhdev_0046_table_3`.

## MHDEV-0047

Source UID: `d126a1c3049746bba48ef34ad2dd159f`.

Question: What is the proportion of Land and land development for Nonperforming Loans andForeclosed Properties-1 to the total in 2011?

Gold answer: `0.11799`.

Question type: `arithmetic`.

Gold reasoning program:

`divide(530,4492)`

Evidence paragraphs:

- Paragraph 48: Table 43 Commercial Real Estate Credit Quality Data
- Paragraph 50: Table 44 Commercial Real Estate Net Charge-offs and Related Ratios

Original table evidence refs: `2-10-1, 2-14-1`.

Source tables for this example: `mhdev_0047_table_0, mhdev_0047_table_1, mhdev_0047_table_2, mhdev_0047_table_3`.

## MHDEV-0048

Source UID: `838d349beccf4e2ebb0c04f518fa07e4`.

Question: What's the sum of the Net investment income in the years where Other income is positive? (in million)

Gold answer: `26756.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(8322,9082), add(#0,9352)`

Evidence paragraphs:

- Paragraph 0: CONSUMER INSURANCE Consumer Insurance Results The following table presents Consumer Insurance results:

Original table evidence refs: `0-5-1, 0-5-2, 0-5-3`.

Source tables for this example: `mhdev_0048_table_0, mhdev_0048_table_1, mhdev_0048_table_2, mhdev_0048_table_3, mhdev_0048_table_4`.

## MHDEV-0049

Source UID: `b52ac057503f483ca5e6a9c4bbef9367`.

Question: What is the sum of CET1 capital, Tier 1 capital and Total capital in 2017? (in million)

Gold answer: `1122758.0`.

Question type: `arithmetic`.

Gold reasoning program:

`add(184375,184375), add(#0,195839), add(#1,184375), add(#2,184375), add(#3,189419)`

Evidence paragraphs:

- Paragraph 38: The following tables present the regulatory capital, assets and risk-based capital ratios for JPMorgan Chase and its significant IDI subsidiaries under both Basel III Standardized Transitional and Basel III Advanced Transitional at December 31, 2017 and 2016.

Original table evidence refs: `2-4-1, 2-4-4, 2-5-1, 2-5-4, 2-6-1, 2-6-4`.

Source tables for this example: `mhdev_0049_table_0, mhdev_0049_table_1, mhdev_0049_table_2`.

## MHDEV-0050

Source UID: `22c216d2b29747adaf2c1f8ef4f954fa`.

Question: What's the sum of the Unit redemptions in the years where Mortgages Payable for Carrying Amounts is positive?

Gold answer: `-69999.0`.

Question type: `arithmetic`.

Gold reasoning program:

`subtract(-14889,55110)`

Evidence paragraphs:

- Paragraph 31: The following table presents the change in the redemption value of the Redeemable noncontrolling interests for the year ended December 31, 2009 and December 31, 2008 (amounts in thousands):
- Paragraph 38: The following are financial instruments for which the Company’s estimate of fair value differs from the carrying amounts (in thousands):

Original table evidence refs: `2-2-1, 2-2-2, 3-3-1, 3-3-3`.

Source tables for this example: `mhdev_0050_table_0, mhdev_0050_table_1, mhdev_0050_table_2, mhdev_0050_table_3, mhdev_0050_table_4`.

## Normalized Package Tables

:::table
ref: multihiertt-examples-table
table: multihiertt_examples
view: default
display: table
caption: MultiHiertt selected examples
numbering: auto
:::

:::table
ref: multihiertt-paragraphs-table
table: multihiertt_paragraphs
view: default
display: table
caption: MultiHiertt source paragraphs
numbering: auto
:::

:::table
ref: multihiertt-source-tables-table
table: multihiertt_source_tables
view: default
display: table
caption: MultiHiertt source table metadata
numbering: auto
:::

:::table
ref: multihiertt-table-rows-table
table: multihiertt_table_rows
view: default
display: table
caption: MultiHiertt row-matrix table data
numbering: auto
:::

:::table
ref: multihiertt-cells-table
table: multihiertt_cells
view: default
display: table
caption: MultiHiertt cell-level evidence table
numbering: auto
:::
