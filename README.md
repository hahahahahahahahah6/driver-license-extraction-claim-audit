# Documentation claim auditor

An offline auditor comparing Markdown promises about structured fields from driving permits against static source fingerprints. Requires Python 3.9 or newer and has no runtime dependencies. Source is parsed, never executed. No network calls, file writes, or telemetry occur.

## Usage

```sh
python3 -m pip install .
driver-license-extraction-claim-audit audit [repo] --json --fail-on medium
python3 -m driver_license_extraction_claim_audit audit . --verbose --ignore vendor --ignore build
driver-license-extraction-claim-audit --version
python3 -m unittest discover
python3 -m build
```

The repository defaults to the current directory. Repeat --ignore with one path prefix per option. The threshold accepts high (default) or medium. Exit codes are 0 for no findings reaching the threshold, 2 for findings reaching it, and 1 for usage or I/O errors. Version: 0.1.0. JSON includes verdict, findings, claims, evidence, and source_files. MEDIUM findings produce a FAIL verdict even when the default threshold exits 0.

## Matching and evidence

Root README.md and Markdown under any docs component supply claims. Blank lines separate paragraphs. Matching lowercases text, expands contractions, replaces hyphens with spaces, collapses whitespace, and uses word boundaries, longest phrases first with alphabetical ties. Denial spans are removed before positive matching. Backtick and tilde fences with up to three leading spaces are excluded; inline code counts.

Symlink files and directories are excluded. Fixtures, docs, and examples components cannot supply evidence. Tests components and test filename conventions supply test evidence separately. Invalid syntax supplies none. Each route must be in one module. Imported names and aliases are resolved; local functions, methods, classes, assignments, annotated assignments, and context-manager bindings suppress shadowed names.

A positive promise without production evidence produces HIGH, or MEDIUM with evidence only in tests. A denial contradicted by production evidence produces HIGH. One finding is emitted per family. With no source files, positive promises produce HIGH and denials pass.

```text
documented-driver-license-extraction-claim-false
documented-no-driver-license-extraction-claim-false
```

The typed route requires a mindee import, a Client construction, and an attribute parse call passing DriverLicenseV1 in the same module. The product argument must be a Name or Attribute with that exact final name, in any positional or keyword argument. Client is accepted as a resolved imported Name or mindee.Client. Generic calls require a listed attribute on any base or a name resolved through an import, including aliases; bare unimported names do not count.

## Limitations and reference vocabulary

DriverLicenseV1 is a 4.x-only fingerprint. It exists in mindee 4.22.0, exported through mindee.product and mindee.product.driver_license. The product was removed from the v1 namespace in mindee 5.x: the 5.4.0 wheel has zero files matching driver; generic PassportV1 survives under mindee/v1/product/passport/. The tool detects the call in source, not the installed SDK version or successful execution. Azure Document Intelligence, Mindee, and Veryfi are cloud APIs; source detection does not validate credentials or API access.

The verified product document is “Driver License API version 1.0”. It has only 13 fields: category, country_code, date_of_birth, dd_number, expiry_date, first_name, id, issued_date, issuing_authority, last_name, mrz, place_of_birth, state. Category describes class, country_code is alpha-3 ISO 3166, dates use ISO YYYY-MM-DD, and state is the two-letter US portion of ISO 3166-2. There is no driving record, points, violations, endorsements, restrictions, photo, signature, or chip data. No DriverLicenseV2 or TypeDriverLicenseV1 form exists; the 4.22.0 wheel has no mindee/documents module. Its class derives from Inference with endpoint_name driver_license and endpoint_version 1.

Static matching is not semantic judgement. Dead code counts; unsupported alias chains are missed. Exact phrases and the finite denial list constrain detection. Verification/KYC and age verification, barcode or magnetic-stripe hardware reading, archival scanning, and document classification are false-positive sources. Qualified reader/scan calls can name hardware instead of field processing. Review the claim and code together.

Bare extract_license / parse_license and plural or data variants do not count: software, business, and other licenses are indistinguishable without a driver qualifier. Bare extract_id / parse_id / extract_document / parse_document do not count. Generic license and ID promises are outside the phrase lists.

PassportV1 alone does not count: generic passport fields have no category, DD number, issuing authority, state, or license MRZ; that route belongs to R190. InternationalIdV2 / IdCardV1 / IdCardV2 alone belong to the id-document family; IndianPassportV1 alone belongs to R215. HealthCardV1 / HealthcareCardV1 are health cards. Every other Mindee product is excluded, as listed below. The v2 extraction API uses configurable model IDs and supplies no fixed fingerprint.

Azure has no specific model for these permit fields. begin_analyze_document with ANY model ID does not count. prebuilt-idDocument extracts generic identity fields only, without category, DD number, issuing authority, or license MRZ, and belongs to R190. Textract analyze_id is generic identity analysis; PassportEye read_mrz reads MRZ lines generically. Both belong to R190 and do not count here.

Veryfi 5.1.0 has no file or method mentioning the target product: process_driver_license / process_drivers_license / process_driver_license_url do not exist. All Veryfi methods, generic document endpoints, document processing, splitting, retrieval, and classification do not count.

Google Document AI has a US Driver's License Parser, but process_document / batch_process_documents use opaque project processor resources. ANY processor is excluded. Eden AI universal-ai calls with ANY model ID are excluded: arbitrary payload strings are not typed fingerprints. LlamaParse is generative without a fixed fingerprint. Nanonets, Docsumo, ABBYY Vantage, Rossum, Klippa, Parseur, and Extend use opaque model, skill, queue, template, or workflow IDs or externally configured generic uploads; none count.

OCR, tables, regex over OCR, CSV-only processing, and manual field assembly do not count. This includes pytesseract image_to_string, pdfplumber / fitz extract_text, camelot / tabula, pandas read_csv / read_excel, and re.search / re.findall. Parsing already extracted text alone is insufficient. classify_document and is_driver_license return labels rather than fields. Strings, comments, name references without calls, imports alone, split-module routes, shadowed calls, and subprocess wrappers invoking any external CLI do not count.

The following fenced vocabulary is reference material.

```text
DRIVERLICENSEEXTRACTION
driver license extraction
extract driver license
extracts driver license
extracting driver license
extract driver licenses
extracts driver licenses
extracting driver licenses
driver license parsing
driver license parser
parse driver license
parses driver license
parse driver licenses
parses driver licenses
driver license data extraction
extract driver license data
driver license field extraction
driver license document extraction
extract driver license documents
driver license reader
driver license scanning
scan driver license
scans driver license
scanning driver license
driver license recognition
recognize driver license
extract driver license fields
drivers license extraction
extract drivers license
extracts drivers license
extracting drivers license
extract drivers licenses
extracts drivers licenses
extracting drivers licenses
drivers license parsing
drivers license parser
parse drivers license
parses drivers license
parse drivers licenses
parses drivers licenses
drivers license data extraction
extract drivers license data
drivers license field extraction
drivers license document extraction
extract drivers license documents
drivers license reader
drivers license scanning
scan drivers license
scans drivers license
scanning drivers license
drivers license recognition

NODRIVERLICENSEEXTRACTION
no driver license extraction
does not extract driver license
does not extract driver licenses
does not support driver license extraction
without driver license extraction
no driver license parser
does not parse driver license
does not parse driver licenses
no drivers license extraction
does not extract drivers license
does not extract drivers licenses
does not support drivers license extraction
without drivers license extraction
no drivers license parser
does not parse drivers license
does not parse drivers licenses
driver license extraction not supported
drivers license extraction not supported
does not scan driver license
does not scan drivers license
no driver license reader
no drivers license reader
does not extract driver license data
does not extract drivers license data

Generic names
extract_driver_license
extract_driver_licenses
parse_driver_license
parse_driver_licenses
extract_driver_license_data
parse_driver_license_data
driver_license_extraction
driver_license_reader
read_driver_license
scan_driver_license
scans_driver_license
scanning_driver_license
driver_license_parsing
driver_license_parser
driver_license_recognition
recognize_driver_license
driver_license_field_extraction
driver_license_document_extraction
extract_driver_license_documents
get_driver_license_data
driver_license_data_extraction
extract_driver_license_fields
parse_driver_license_fields
driver_license_scanning
```

## Excluded routes and matching hazards

```text
 (implementation MUST match exactly)

mindee Client construction + parse call passing DriverLicenseV1
(Name exactly DriverLicenseV1, or Attribute with attr exactly
DriverLicenseV1 such as product.DriverLicenseV1 /
mindee.product.DriverLicenseV1 /
mindee.product.driver_license.DriverLicenseV1) as any
argument; import gate mindee. DriverLicenseV1 IS a 4.x-only
fingerprint (4.22.0 wheel inspected 2026-11-15:
mindee/product/driver_license/driver_license_v1.py
defines class DriverLicenseV1(Inference), endpoint_name
"driver_license", endpoint_version "1", exported via
mindee.product and via mindee.product.driver_license;
its document is "Driver License API version 1.0" with fields
category, country_code, date_of_birth, dd_number, expiry_date,
first_name, id, issued_date, issuing_authority, last_name, mrz,
place_of_birth, state; there is NO DriverLicenseV2 — the
4.22.0 wheel has no driver_license_v2 file and no
mindee/documents module; the 5.4.0 wheel inspected 2026-11-15
contains NO driver license product at all — zero files
matching "driver" anywhere in the wheel, while the generic
PassportV1 survives under mindee/v1/product/passport/, so the
product was removed from the v1 namespace in mindee 5.x). The
tool detects the call in source, not the installed SDK version.
A parse call passing any other product (PassportV1,
InternationalIdV2, IdCardV1, IdCardV2, HealthcareCardV1,
HealthCardV1, IndianPassportV1, InvoiceV4, ReceiptV5,
InvoiceSplitterV1, MultiReceiptsDetectorV1, FinancialDocumentV1,
BankCheckV1, BankAccountDetailsV1, BankAccountDetailsV2,
PayslipV2, PayslipV3, BusinessCardV1, CustomV1, GeneratedV1,
BillOfLadingV1, ResumeV1, DeliveryNoteV1, CarteGriseV1,
EnergyBillV1, NutritionFactsLabelV1, MaterialCertificateV1,
BarcodeReaderV1, CropperV1, UsMailV2, UsMailV3, or any other)
is NOT evidence. A bare generic extract_license /
parse_license / extract_licenses / parse_licenses /
extract_license_data / parse_license_data call with no
"driver" qualifier is NOT evidence here (a bare "license" call
cannot be told apart from a software license or any other
license). A bare generic extract_id / parse_id /
extract_document / parse_document call with no "driver license"
qualifier is NOT evidence here.

## veryfi names (implementation MUST match exactly)

NO veryfi route: the veryfi Python SDK 5.1.0 wheel, inspected
2026-11-15, contains no file or method mentioning "driver
license", "driver_license", or "driverlicense" at all — no
process_driver_license / process_drivers_license /
process_driver_license_url method exists in the SDK.
NOT evidence: veryfi split_and_process_pdf /
split_and_process_pdf_url (splitting a batched PDF into documents,
the invoice-splitter family's domain); veryfi process_document /
process_any_document and every other veryfi method listed in the
Behaviour section; a call to the non-existent
process_driver_license / process_drivers_license /
process_driver_license_url methods (no such methods exist in
the veryfi SDK); a raw HTTP call to
"https://api.veryfi.com/api/v8/partner/documents" (the generic
Veryfi documents endpoint, shared by receipts, invoices, and
other documents — not driver-license-specific).

## azure names (implementation MUST match exactly)

NO azure route: Azure Document Intelligence has no
driver-license-specific model. The Microsoft Learn v4.0 (GA)
prebuilt-model language-support page and the v4.0 model
catalog, searched 2026-11-15 (catalog listing carried from
R213/R214/R215), list prebuilt-read, prebuilt-layout,
prebuilt-contract, prebuilt-healthInsuranceCard.us,
prebuilt-idDocument, prebuilt-invoice, prebuilt-receipt,
prebuilt-marriageCertificate.us, prebuilt-creditCard,
prebuilt-check.us, prebuilt-payStub.us, prebuilt-bankStatement,
prebuilt-mortgage.us.1003/.1004/.1005/.1008/.closingDisclosure,
prebuilt-tax.us.*, prebuilt-vaccinationCard,
prebuilt-businessCard (deprecated in v4.0), and
prebuilt-document — and no model named "driver license".
A begin_analyze_document call with ANY model id is NOT evidence.
prebuilt-idDocument extracts generic identity fields from
driver licenses among other identity documents (names, document
number, dates, address); it does not extract a license
category, a DD number, an issuing authority, or a license MRZ,
and it is the R190 id-document family's route.

## google document ai names (implementation MUST match exactly)

NO Google Document AI route as a static fingerprint: a US
Driver's License Parser exists as a pretrained processor (the
Document AI processors list / pretrained overview page,
searched 2026-11-15, carried from R213/R214/R215, lists
pretrained parsers for invoice, expense, bank statement, pay
slip, W2, US driver licence, passport, utility bill, and
identity proofing) — but a process_document call names its
processor by an opaque per-project resource name, not by a
typed SDK call naming the processor type, so there is no fixed
static fingerprint for the call itself. A process_document /
batch_process_documents call with ANY processor is NOT evidence.
The generic passport parser is the R190 family's domain.

## eden ai / llamaparse / nanonets / docsumo / other vendor names (implementation MUST match exactly)

NO Eden AI route, by deliberate decision: the standing sibling
rule is that a universal-ai call with ANY model id is NOT
evidence, because the model id is a plain string inside an
arbitrary request payload, not a typed SDK call — the same call
shape serves every Eden AI feature, so there is no fixed static
fingerprint for the call itself. NO LlamaParse route: LlamaParse
is a generative parsing API with no fixed static fingerprint
naming driver license extraction. NO Nanonets route: Nanonets
document calls carry an opaque model_id in the URL path (no
fixed fingerprint — the model id is user-configured, not a
driver license product). NO Docsumo route: Docsumo uploads go
to a generic endpoint with the document type configured in the
dashboard, not in the call. NO ABBYY Vantage / Rossum / Klippa /
Parseur / Extend route: opaque skill / queue / template /
workflow IDs. NO Textract route: Textract has no driver license
extraction operation (analyze_document / analyze_expense /
analyze_id cover generic document, expense, and identity
analysis of one document; analyze_id is the R190 family's
domain). NO PassportEye route: PassportEye read_mrz reads MRZ
lines generically (the R190 family's domain) — reading an MRZ
is not extracting a driver's license's fields. NO generic
OCR route: pytesseract image_to_string or any plain-text
extraction returns raw text, not the structured driver license
fields, and has no fixed static fingerprint naming the license.
NO document classifier route: classifying a document as a
driver license returns one label, not the license's fields.
NO mindee v2 extraction API route: configurable model id, no
fixed fingerprint. NO bare generic extract_license /
parse_license route: a bare "license" call with no "driver"
qualifier cannot be told apart from a software license or any
other license. NO mindee PassportV1 route: extracting generic
passport fields is not extracting a driver's license's
license-specific fields. NO mindee InternationalIdV2 /
IdCardV1 / IdCardV2 route: extracting international ID /
national identity card fields is not extracting a driver's
license. NO mindee IndianPassportV1 route: extracting
India-specific passport fields is not extracting a driver's
license. NO mindee HealthCardV1 / HealthcareCardV1 route:
extracting health card fields is not extracting a driver's
license.


 (honest limitations, also for the README)

- The phrases "driver license extraction" / "extract driver
  license" / "driver license parser" are deliberately
  DRIVERLICENSEEXTRACTION phrases: in document-tool docs they
  name pulling structured fields out of a driver's license. But
  "driver license" can also name a license to verify (identity
  verification, KYC, age verification) rather than to extract
  fields from: a doc that means verification, not field
  extraction, is a false positive; the tool flags the claim, only
  the code decides.
- "driver license reader" / "drivers license reader" are
  deliberately phrases. But a "reader" can also name a barcode /
  magnetic-stripe reader (hardware that reads the card) rather
  than a field extractor: a doc that means hardware reading, not
  field extraction, is a false positive; the tool flags the claim,
  only the code decides.
- "scan driver license" / "scan drivers license" are deliberately
  phrases. But "scan" can also name scanning the physical license
  for archival (producing an image file) rather than extracting
  its fields: a doc that means image capture, not field
  extraction, is a false positive; the tool flags the claim, only
  the code decides.
- "driver license recognition" / "recognize driver license" /
  "drivers license recognition" are deliberately phrases. But
  "recognition" can also name detecting whether a document IS a
  driver's license (classification, one label) rather than
  extracting its fields: a doc that means classification, not
  field extraction, is a false positive; the tool flags the claim,
  only the code decides.
- "drivers license extraction" / "extract drivers license" are
  deliberately phrases: "drivers license" is the common
  unapostrophised form of the same document name, and docs do
  use it. But a doc that means a license to verify rather than
  to extract fields from is a false positive; the tool flags the
  claim, only the code decides.
- DriverLicenseV1 extracts the listed fields only (category,
  country_code, date_of_birth, dd_number, expiry_date,
  first_name, id, issued_date, issuing_authority, last_name, mrz,
  place_of_birth, state). It carries no driving record, no
  points or violations, no endorsements or restrictions, no photo
  or signature image, and no chip data. A tool that extracts
  those does so through some other route; this family checks for
  the DriverLicenseV1 call, not for those fields. Say so in the
  README.
- A generic `read_driver_license(` / `scan_driver_license(` /
  `driver_license_reader(` call can name a barcode / stripe
  reader rather than an image field extractor: the tool counts
  the call, the claim plus the code decide — and a subprocess
  call invoking an external CLI is NOT evidence by design, so a
  thin wrapper that only calls subprocess fails.
- Mindee `parse` with DriverLicenseV1 counts as evidence: the
  product exists in mindee 4.22.0 (wheel inspected 2026-11-15).
  The tool detects the call in source, not whether the call
  succeeds against a current API version. Say so in the README.
- Mindee `parse` with DriverLicenseV1 IS a 4.x-only fingerprint:
  mindee 5.x removed the driver license product from the v1
  namespace (5.4.0 wheel inspected 2026-11-15 — zero files
  matching "driver" anywhere in the wheel; the generic
  PassportV1 survives under mindee/v1/product/passport/). Say
  so in the README.
- A bare generic `extract_license(` / `parse_license(` call
  is NOT detected: a bare "license" call with no "driver"
  qualifier cannot be told apart from a software license or any
  other license. Only the qualified names count. Say so in the
  README.
- Mindee `parse` with PassportV1 alone is NOT detected:
  extracting generic passport fields is not extracting a
  driver's license's license-specific fields (no category, no DD
  number, no issuing authority, no state, no license MRZ), and
  the generic passport route is the R190 family's domain. Say so
  in the README.
- Mindee `parse` with InternationalIdV2 / IdCardV1 / IdCardV2
  alone is NOT detected: extracting fields from an international
  ID or a national identity card is not extracting a driver's
  license, and those routes are the id-document family's domain.
  Say so in the README.
- Mindee `parse` with IndianPassportV1 alone is NOT detected:
  extracting India-specific passport fields is not extracting a
  driver's license, and that route is the R215 family's domain.
  Say so in the README.
- Mindee `parse` with HealthCardV1 / HealthcareCardV1 alone is
  NOT detected: extracting health card fields is not extracting
  a driver's license. Say so in the README.
- Mindee `parse` with ReceiptV5 / InvoiceV4 / InvoiceSplitterV1 /
  MultiReceiptsDetectorV1 / FinancialDocumentV1 / BankCheckV1 /
  BankAccountDetailsV1 / BankAccountDetailsV2 / PayslipV2 /
  PayslipV3 / NutritionFactsLabelV1 / BusinessCardV1 / CustomV1 /
  GeneratedV1 / BillOfLadingV1 / ResumeV1 / DeliveryNoteV1 /
  CarteGriseV1 / EnergyBillV1 / MaterialCertificateV1 /
  BarcodeReaderV1 / CropperV1 / UsMailV2 / UsMailV3 is NOT
  detected: those are other document types or other operations.
  Say so in the README.
- Azure `begin_analyze_document` with ANY model id is NOT
  detected: Azure Document Intelligence has no driver-license-
  specific model (the Learn v4.0 GA prebuilt-model pages list no
  such model, verified 2026-11-15). prebuilt-idDocument extracts
  generic identity fields but no license-specific fields, and it
  is the R190 id-document family's route. Say so in the README.
- Veryfi has NO driver license method: the 5.1.0 wheel contains
  no file or method mentioning "driver license",
  "driver_license", or "driverlicense" (verified 2026-11-15).
  Veryfi `process_document` / `process_any_document` /
  `split_and_process_pdf` and all other veryfi calls are NOT
  detected. Say so in the README.
- Google Document AI `process_document` / `batch_process_documents`
  with ANY processor is NOT detected: the US Driver's License
  Parser is invoked by an opaque per-project processor resource
  name, not by a typed call naming the processor type, so there
  is no fixed static fingerprint; the generic passport parser is
  the R190 family's domain. Say so in the README.
- Textract `analyze_id` is NOT detected: generic identity
  analysis of one document is not driver license extraction,
  and it is the R190 family's domain. Say so in the README.
- PassportEye `read_mrz` is NOT detected: reading MRZ lines
  generically is not extracting a driver's license's fields, and
  it is the R190 family's domain. Say so in the README.
- Eden AI universal-ai calls with ANY model id are NOT detected:
  the model id is a plain string inside an arbitrary request
  payload, not a typed SDK call, so there is no fixed static
  fingerprint for the call itself. Say so in the README.
- LlamaParse calls are NOT detected: its parsing API is
  generative with no fixed static fingerprint naming driver
  license extraction. Say so in the README.
- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur /
  Extend calls are NOT detected: opaque model / skill / queue /
  template / workflow IDs, or a generic upload endpoint with the
  document type configured outside the call — no fixed fingerprint.
  Say so in the README.
- Generic OCR / table / regex-OCR / CSV calls (pytesseract
  image_to_string, pdfplumber / fitz extract_text, camelot /
  tabula table calls, pandas read_csv / read_excel) are NOT
  detected: plain text or tables are not driver license fields.
  Say so in the README.
- Document classifier calls (classify_document,
  is_driver_license, or any driver-license-classification call)
  are NOT detected: returning one label is not extracting the
  license's fields. Say so in the README.
- A hand-rolled extraction from OCR text (`re.search` /
  `re.findall` on extracted text plus manual field assembly,
  no listed call) is NOT detected: the tool requires a listed
  call. Say so in the README.
- The mindee CLI, the veryfi CLI, and any other external
  driver license extractor tool invoked through subprocess are NOT
  detected: subprocess calls invoking an external CLI are NOT
  evidence by design. Say so in the README.
- Azure Document Intelligence, Mindee, and Veryfi are cloud APIs:
  the tool detects the client call in source, not whether
  credentials are configured or the call succeeds. Say so in the
  README.
- "extract license" / "license extraction" / "extract id
  document" / "id document extraction" claims are NOT in the
  phrase lists: extracting fields from a generic license or an
  ID document is a different operation from extracting a driver's
  license — generic license / ID extraction is the R190 family's
  domain. Say so in the README.
- "extract indian passport" / "indian passport extraction"
  claims are NOT in the phrase lists: extracting an Indian
  passport is a different operation from extracting a driver's
  license. Say so in the README.
- "extract french health card" / "french health card extraction"
  claims are NOT in the phrase lists: extracting a French Carte
  Vitale is a different operation from extracting a driver's
  license. Say so in the README.
- "extract invoices" / "invoice extraction", "extract receipts" /
  "receipt extraction", "extract financial documents" /
  "financial document extraction", "extract bank statements" /
  "statement extraction", "extract tax forms" / "extract w2 forms",
  "extract pay stubs" / "payslip extraction", "extract us mail" /
  "us mail extraction", "extract contracts" / "contract extraction",
  "extract resumes" / "resume extraction", "extract bills of
  lading" / "bill of lading extraction", "extract delivery notes" /
  "delivery note extraction", "extract carte grises" / "carte
  grise extraction", "extract energy bills" / "energy bill
  extraction", "extract marriage certificates" / "marriage
  certificate extraction", "extract bank account details" / "bank
  details extraction", "extract nutrition facts labels" /
  "nutrition facts label extraction", "extract material
  certificates" / "material certificate extraction", "extract
  health insurance cards" / "health insurance card extraction",
  and "extract bank checks" / "check extraction" claims are NOT
  in the phrase lists: this family covers driver license
  extraction only. Say so in the README.
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot
  follow are missed; exact phrases only, not semantics; denial
  handling depends on the denial phrase list; each route must sit
  in a single module.

```

## Differentiation

The id-document family accepts generic identity fields through PassportV1, InternationalIdV2, IdCardV1/V2, prebuilt-idDocument, analyze_id, and read_mrz. This auditor requires the specific typed product or qualified generic calls. The DriverLicenseV1 route overlaps R190 correctly: its fields are also identity fields. Generic identity routes can pass R190 while failing this audit.

Sibling extraction families include OCR, table, receipt, invoice, financial-document, bank-check, bank-statement, tax-form, pay-stub, business-card, credit-card, contract, mortgage, resume, bill-of-lading, delivery-note, carte-grise, energy-bill, marriage-certificate, bank-account-details, nutrition-facts-label, material-certificate, us-mail, invoice-splitting, multi-receipt-detection, french-health-card, health-insurance-card, indian-passport, and document-question-answering. Their promises, fields, and routes do not establish this family's specific claim. Generic license, ID, Indian passport, French health card, and all other sibling claim phrases are outside this vocabulary.

## Development

The standard-library unittest suite is bundled in both distributions. Build with an isolated build frontend inside a virtual environment; no runtime dependencies are required.

```sh
python3 -m venv .venv
.venv/bin/python3 -m pip install build
.venv/bin/python3 -m unittest discover
.venv/bin/python3 -m build
```

MIT licensed. No SDK is required to run the auditor.
