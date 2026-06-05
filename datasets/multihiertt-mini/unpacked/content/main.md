# MultiHiertt Mini Financial Reasoning Package

This package is a 50-example curated subset of the public MultiHiertt dev split. It is intended as an MCD example for hybrid reasoning over financial report prose, multiple source tables, and benchmark questions.

The source benchmark stores each document as paragraphs plus multiple HTML tables. This MCD package normalizes those records into queryable CSV tables while preserving the original example IDs, table indexes, row indexes, and column indexes.

## Package Reference Map

- `multihiertt_examples` stores one row per selected benchmark example.
- `multihiertt_paragraphs` stores source paragraphs.
- `multihiertt_source_tables` stores one row per original HTML table.
- `multihiertt_table_rows` stores each original table row as a fixed-width row matrix.
- `multihiertt_cells` stores each table cell with the original `table-row-column` ref and cell description.
- MultiHiertt cell refs use zero-based `table_index-row_index-col_index`, such as `0-2-4`.

## Reasoning Notes

For arithmetic questions, inspect the relevant source paragraphs and tables, then compute the requested value from source numbers. The row matrix table is useful for scanning table shape, while the cell table is better for exact cell lookup.

## MHDEV-0001

Source UID: `7d840731012a4a09a735eeee286c364b`.

Question: Which year is Total Revenues of Group retirement products the most?

Source tables for this example: `mhdev_0001_table_0, mhdev_0001_table_1, mhdev_0001_table_2, mhdev_0001_table_3`.

## MHDEV-0002

Source UID: `63260a43bc4e4632a0317eb820caf964`.

Question: What will Distribution fees reach in 2010 if it continues to grow at its current rate? (in millions)

Source tables for this example: `mhdev_0002_table_0, mhdev_0002_table_1, mhdev_0002_table_2, mhdev_0002_table_3`.

## MHDEV-0003

Source UID: `7f9cd61fc4264c9bb81cdcfd2c5c4c38`.

Question: What was the total amount of Amount in 2007 for Financial Services Businesses ? (in million)

Source tables for this example: `mhdev_0003_table_0, mhdev_0003_table_1, mhdev_0003_table_2, mhdev_0003_table_3`.

## MHDEV-0004

Source UID: `b7642f569ac54d28af0a4a16683d3f35`.

Question: Does the average value of Power purchase agreements in Entergy Arkansas greater than that in Entergy Louisiana?

Source tables for this example: `mhdev_0004_table_0, mhdev_0004_table_1, mhdev_0004_table_2, mhdev_0004_table_3`.

## MHDEV-0005

Source UID: `5cc19228085048228131f5d77196655d`.

Question: What is the ratio of Securities to the total for Net realized losses reclassified into earnings in 2008?

Source tables for this example: `mhdev_0005_table_0, mhdev_0005_table_1, mhdev_0005_table_2, mhdev_0005_table_3`.

## MHDEV-0006

Source UID: `1ca146715d8b4ed9a102b68af5bdd385`.

Question: How many Below Investment Grade exceed the average of Below Investment Grade in 2004?

Source tables for this example: `mhdev_0006_table_0, mhdev_0006_table_1, mhdev_0006_table_2, mhdev_0006_table_3`.

## MHDEV-0007

Source UID: `a60e6202dde64cbb9c7eb29ed5fd3fe2`.

Question: containerboards net sales represented what percentage of industrial packaging sales in 2005?

Source tables for this example: `mhdev_0007_table_0, mhdev_0007_table_1, mhdev_0007_table_2, mhdev_0007_table_3`.

## MHDEV-0008

Source UID: `b6e47615b28841deaacce680de41c65c`.

Question: What's the difference of Securities America, Inc.-3(4) between 2010 and 2009 forActual Capital? (in million)

Source tables for this example: `mhdev_0008_table_0, mhdev_0008_table_1, mhdev_0008_table_2`.

## MHDEV-0009

Source UID: `9b1a8a210c654f1aada293d3ea35429e`.

Question: What is the ratio of Total cards-in-force in Table 1 to the Other in Table 0 in 2016?

Source tables for this example: `mhdev_0009_table_0, mhdev_0009_table_1, mhdev_0009_table_2`.

## MHDEV-0010

Source UID: `6a6d7accb802496fa8e7ed474f117d38`.

Question: In the year / section with largest amount of Average contract revenue per MWh, what's the sum of Planned net MW in operation?

Source tables for this example: `mhdev_0010_table_0, mhdev_0010_table_1, mhdev_0010_table_2, mhdev_0010_table_3, mhdev_0010_table_4, mhdev_0010_table_5`.

## MHDEV-0011

Source UID: `b06dcff918b84dbc8bdc39df31d6c355`.

Question: What is the average value of Total revenues in Table 2 and Restricted stock awards in Table 1 in 2007? (in million)

Source tables for this example: `mhdev_0011_table_0, mhdev_0011_table_1, mhdev_0011_table_2`.

## MHDEV-0012

Source UID: `0fc058f14a954e6eb3d22d45a76ef981`.

Question: What was the total amount of Allowance greater than 270 in 2018? (in million)

Source tables for this example: `mhdev_0012_table_0, mhdev_0012_table_1, mhdev_0012_table_2, mhdev_0012_table_3, mhdev_0012_table_4`.

## MHDEV-0013

Source UID: `a779b55236c7402fb7a09102e4295673`.

Question: What is the sum of Aircraft on Firm Order in 2009?

Source tables for this example: `mhdev_0013_table_0, mhdev_0013_table_1, mhdev_0013_table_2, mhdev_0013_table_3`.

## MHDEV-0014

Source UID: `723cdadfdcfc48f68cc952f98977cf62`.

Question: In which year is Other Expense greater than 30000?

Source tables for this example: `mhdev_0014_table_0, mhdev_0014_table_1, mhdev_0014_table_2`.

## MHDEV-0015

Source UID: `404ce5c5eb06402d8172096ca3cd0bd1`.

Question: What is the sum of the Cost of sales in the years where Net sales is greater than 1000? (in million)

Source tables for this example: `mhdev_0015_table_0, mhdev_0015_table_1, mhdev_0015_table_2, mhdev_0015_table_3`.

## MHDEV-0016

Source UID: `9b2dc866091743d7b190417a4307a3c4`.

Question: what was the change in advertising costs from 2001 to 2002?

Source tables for this example: `mhdev_0016_table_0, mhdev_0016_table_1, mhdev_0016_table_2, mhdev_0016_table_3`.

## MHDEV-0017

Source UID: `bbcbe3ddf43449a08763a2f7d7986260`.

Question: What is the sum amount of Capital lease obligations in the years with the lowest amount of Operating lease obligations? (in dollars in millions)

Source tables for this example: `mhdev_0017_table_0, mhdev_0017_table_1, mhdev_0017_table_2`.

## MHDEV-0018

Source UID: `161facf717424d17af248fcb4fdb738a`.

Question: What is the growth rate of Balance between December 31, 2008 and December 31, 2009?

Source tables for this example: `mhdev_0018_table_0, mhdev_0018_table_1, mhdev_0018_table_2, mhdev_0018_table_3`.

## MHDEV-0019

Source UID: `05be07b07d5a44ca8398c7ec38271bc6`.

Question: what is the pre-tax aggregate net unrealized loss in 2008?

Source tables for this example: `mhdev_0019_table_0, mhdev_0019_table_1, mhdev_0019_table_2`.

## MHDEV-0020

Source UID: `ce038f0f07ed4f90a13b4134d41bfa3e`.

Question: In the year with largest amount of government, what's the increasing rate of education?

Source tables for this example: `mhdev_0020_table_0, mhdev_0020_table_1, mhdev_0020_table_2, mhdev_0020_table_3`.

## MHDEV-0021

Source UID: `7389cfa35a894e14bf0773e29d326973`.

Question: What's the sum of Debt maturities of Thereafter, and Capital lease obligations of Less than 1 year ?

Source tables for this example: `mhdev_0021_table_0, mhdev_0021_table_1, mhdev_0021_table_2, mhdev_0021_table_3`.

## MHDEV-0022

Source UID: `032145bd6fdd4712b05cd5495f7c8f35`.

Question: What is the proportion of Asset Management to the total Mortgage and other loans receivable, net of allowance in 2006?

Source tables for this example: `mhdev_0022_table_0, mhdev_0022_table_1, mhdev_0022_table_2`.

## MHDEV-0023

Source UID: `9df041a1ce9440c2aaaf77f773811fcb`.

Question: What was the total amount of Amount greater than 5000 in 2013?

Source tables for this example: `mhdev_0023_table_0, mhdev_0023_table_1, mhdev_0023_table_2, mhdev_0023_table_3`.

## MHDEV-0024

Source UID: `071e671820fa4f89b003923a38b03741`.

Question: what was the percentage change in the allowance for loan losses from 2008 to 2009?

Source tables for this example: `mhdev_0024_table_0, mhdev_0024_table_1, mhdev_0024_table_2`.

## MHDEV-0025

Source UID: `4251b0c576c3429085b0f79fe3594b32`.

Question: What is the growing rate of Net credit losses in the year with the most Provision for benefits and claims?

Source tables for this example: `mhdev_0025_table_0, mhdev_0025_table_1, mhdev_0025_table_2`.

## MHDEV-0026

Source UID: `f1b58737e9a34f60b4882c8b7226395e`.

Question: What do all collateralized financings sum up in 2018 , excluding Repurchase agreements and Securities loaned? (in million)

Source tables for this example: `mhdev_0026_table_0, mhdev_0026_table_1, mhdev_0026_table_2, mhdev_0026_table_3`.

## MHDEV-0027

Source UID: `b86d620b573c45ffae2f15fb5a02e688`.

Question: In the year with the most other revenues , what is the growth rate of General and administrative expense? (in million)

Source tables for this example: `mhdev_0027_table_0, mhdev_0027_table_1, mhdev_0027_table_2, mhdev_0027_table_3`.

## MHDEV-0028

Source UID: `9e8eb2e5a768431c99abaef9de32a4ec`.

Question: as of february 19 , 2016 what was the market capitalization

Source tables for this example: `mhdev_0028_table_0, mhdev_0028_table_1, mhdev_0028_table_2, mhdev_0028_table_3`.

## MHDEV-0029

Source UID: `e4d6c1e51b0b49d895b73472bb9f0dc0`.

Question: What was the total amount of Net interest revenue and Non-interest revenue in 2009 ? (in million)

Source tables for this example: `mhdev_0029_table_0, mhdev_0029_table_1, mhdev_0029_table_2`.

## MHDEV-0030

Source UID: `612ad8b5f4f94223b2e4b3d38a00951f`.

Question: What is the sum of the amount of Equity securities in the range of 50 million and 100 million? (in million)

Source tables for this example: `mhdev_0030_table_0, mhdev_0030_table_1, mhdev_0030_table_2, mhdev_0030_table_3`.

## MHDEV-0031

Source UID: `d67cd399e6b94bb4a6cdb39afaf0f8f4`.

Question: what was the percentage change in cash from operations between 2008 and 2009?

Source tables for this example: `mhdev_0031_table_0, mhdev_0031_table_1, mhdev_0031_table_2, mhdev_0031_table_3, mhdev_0031_table_4, mhdev_0031_table_5, mhdev_0031_table_6`.

## MHDEV-0032

Source UID: `11904e0323e04189a6d0c03ebec8c27f`.

Question: What was the average of the Total operating revenues in the year where Other investment income/(losses) is positive? (in million)

Source tables for this example: `mhdev_0032_table_0, mhdev_0032_table_1, mhdev_0032_table_2, mhdev_0032_table_3`.

## MHDEV-0033

Source UID: `7ba60c94b1534e128a1841bbbb1a382e`.

Question: What's the sum of Collections reinvested in revolving period securitizations in terms of Home Equity in 2009? (in dollars in millions)

Source tables for this example: `mhdev_0033_table_0, mhdev_0033_table_1, mhdev_0033_table_2`.

## MHDEV-0034

Source UID: `000682417fd9450bb10fee113dae5fcc`.

Question: What will principal transaction be like in 2013 if it develops with the same increasing rate as current?

Source tables for this example: `mhdev_0034_table_0, mhdev_0034_table_1, mhdev_0034_table_2, mhdev_0034_table_3, mhdev_0034_table_4`.

## MHDEV-0035

Source UID: `91afe10a7407428c9bbad202945e060e`.

Question: what was the average operating leases 2014rental expense for operating leases from 2009 to 2011

Source tables for this example: `mhdev_0035_table_0, mhdev_0035_table_1, mhdev_0035_table_2, mhdev_0035_table_3`.

## MHDEV-0036

Source UID: `abb228ebc069473dbd8a62729def4b35`.

Question: what is the highest total amount of North Sea?

Source tables for this example: `mhdev_0036_table_0, mhdev_0036_table_1, mhdev_0036_table_2, mhdev_0036_table_3, mhdev_0036_table_4`.

## MHDEV-0037

Source UID: `ae2ce9e907114dd786d4a02437917f15`.

Question: What is the sum of Securities loaned in 2017 and Aggregate contractual principal in excess of fair value in 2015? (in million)

Source tables for this example: `mhdev_0037_table_0, mhdev_0037_table_1, mhdev_0037_table_2, mhdev_0037_table_3`.

## MHDEV-0038

Source UID: `930465d2a8a14fbc9c3de57267a5f067`.

Question: What is the average increasing rate of Purchased power between 2017 and 2018? (in million)

Source tables for this example: `mhdev_0038_table_0, mhdev_0038_table_1, mhdev_0038_table_2, mhdev_0038_table_3, mhdev_0038_table_4`.

## MHDEV-0039

Source UID: `6b77c2a63b8d4c268d745c78abf7db2a`.

Question: What will Total trading account assets be like in 2011 if it continues to grow at the same rate as it did in 2010? (in million)

Source tables for this example: `mhdev_0039_table_0, mhdev_0039_table_1, mhdev_0039_table_2`.

## MHDEV-0040

Source UID: `8caf20e28a314f43a0bc3fdbadcc2220`.

Question: What is the growing rate of BENEFIT OBLIGATION AT END OF YEAR for Con Edison in the year with the least Benefit obligation at beginning of year for Con Edison?

Source tables for this example: `mhdev_0040_table_0, mhdev_0040_table_1, mhdev_0040_table_2`.

## MHDEV-0041

Source UID: `70ee07d30a8b46e195c791b6d69b9534`.

Question: What's the total amount of the Net income for Amount in the years where Operating activities for Total cash provided by (used in) is greater than 1760? (in million)

Source tables for this example: `mhdev_0041_table_0, mhdev_0041_table_1, mhdev_0041_table_2, mhdev_0041_table_3, mhdev_0041_table_4, mhdev_0041_table_5`.

## MHDEV-0042

Source UID: `6cd056489ef745088e88f09c847c8ad9`.

Question: as of december 31 , 2017 , what was the percent of the 2016 program remaining available for purchase

Source tables for this example: `mhdev_0042_table_0, mhdev_0042_table_1, mhdev_0042_table_2, mhdev_0042_table_3`.

## MHDEV-0043

Source UID: `e258d39d9df44652a28ca25d0304b0ed`.

Question: In the year with the most Total fixed rate debt, what is the amount of Variable rate debt and total?

Source tables for this example: `mhdev_0043_table_0, mhdev_0043_table_1, mhdev_0043_table_2, mhdev_0043_table_3`.

## MHDEV-0044

Source UID: `05d560d08fbc406990e7b02b415aa60a`.

Question: what's the total amount of Loss expenses Casualty of 2008 Gross, and Case reserves of 2009 Gross ?

Source tables for this example: `mhdev_0044_table_0, mhdev_0044_table_1, mhdev_0044_table_2, mhdev_0044_table_3`.

## MHDEV-0045

Source UID: `0bcf9238356d41029754e323fa14108d`.

Question: What is the proportion of Pensions' Service cost of of net periodic benefit cost in U.S. Plans to the total in 2006?

Source tables for this example: `mhdev_0045_table_0, mhdev_0045_table_1, mhdev_0045_table_2`.

## MHDEV-0046

Source UID: `2a9928d6aa7a42b9b76531cf98982a26`.

Question: What is the total amount of Net cash used in financing activities of 2010, Individual fixed annuities of Net Investment Income, and Group retirement products of Total Revenues ?

Source tables for this example: `mhdev_0046_table_0, mhdev_0046_table_1, mhdev_0046_table_2, mhdev_0046_table_3`.

## MHDEV-0047

Source UID: `d126a1c3049746bba48ef34ad2dd159f`.

Question: What is the proportion of Land and land development for Nonperforming Loans andForeclosed Properties-1 to the total in 2011?

Source tables for this example: `mhdev_0047_table_0, mhdev_0047_table_1, mhdev_0047_table_2, mhdev_0047_table_3`.

## MHDEV-0048

Source UID: `838d349beccf4e2ebb0c04f518fa07e4`.

Question: What's the sum of the Net investment income in the years where Other income is positive? (in million)

Source tables for this example: `mhdev_0048_table_0, mhdev_0048_table_1, mhdev_0048_table_2, mhdev_0048_table_3, mhdev_0048_table_4`.

## MHDEV-0049

Source UID: `b52ac057503f483ca5e6a9c4bbef9367`.

Question: What is the sum of CET1 capital, Tier 1 capital and Total capital in 2017? (in million)

Source tables for this example: `mhdev_0049_table_0, mhdev_0049_table_1, mhdev_0049_table_2`.

## MHDEV-0050

Source UID: `22c216d2b29747adaf2c1f8ef4f954fa`.

Question: What's the sum of the Unit redemptions in the years where Mortgages Payable for Carrying Amounts is positive?

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
caption: MultiHiertt cell-level source table
numbering: auto
:::
