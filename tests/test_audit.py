"""Behavioral regression tests for the R216 specification."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from driver_license_extraction_claim_audit.audit import audit, match_claims, module_evidence, normalize, POSITIVE_RULE, NEGATIVE_RULE
from driver_license_extraction_claim_audit.phrases import DRIVERLICENSEEXTRACTION as POS, NODRIVERLICENSEEXTRACTION as NEG, GENERIC_NAMES
from driver_license_extraction_claim_audit.__main__ import main

MIND = 'import mindee\nc=mindee.Client()\nc.parse(DriverLicenseV1, source)\n'
GENERIC = 'service.extract_driver_license(source)\n'

class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def report(self, doc='driver license extraction', source=None, name='app.py', **kw):
        self.write('README.md', doc)
        if source is not None:
            self.write(name, source)
        return audit(self.root, **kw)

    def cli(self, args):
        output, error = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(error):
            try:
                code = main(args)
            except SystemExit as exc:
                code = exc.code
        return code, output.getvalue(), error.getvalue()

    def test_vocabulary(self):
        self.assertEqual((len(POS),len(NEG),len(GENERIC_NAMES)), (50,24,24))
        self.assertEqual((len(set(POS)),len(set(NEG))), (50,24))
        self.assertTrue(all(p==normalize(p) for p in POS+NEG))
        self.assertEqual(POSITIVE_RULE,'documented-driver-license-extraction-claim-false')
        self.assertEqual(NEGATIVE_RULE,'documented-no-driver-license-extraction-claim-false')

    def test_normalization(self):
        self.assertEqual(normalize("DOESN'T extract-driver-license"), 'does not extract driver license')
        self.assertEqual(match_claims("DOESN'T extract-driver-license")[0]['family'], 'NODRIVERLICENSEEXTRACTION')

    def test_boundaries(self):
        self.assertFalse(match_claims('xdriver license extractionx'))

    def test_longest(self):
        self.assertEqual([c['phrase'] for c in match_claims('extract driver license data')], ['extract driver license data'])

    def test_mixed_claims(self):
        self.assertEqual([c['family'] for c in match_claims('does not extract driver license; driver license extraction')], ['NODRIVERLICENSEEXTRACTION','DRIVERLICENSEEXTRACTION'])

    def test_paragraphs(self):
        self.assertTrue(match_claims('driver license\nextraction'))
        self.assertFalse(match_claims('driver license\n\nextraction'))

    def test_inline(self):
        self.assertTrue(match_claims('`driver license extraction`'))

    def test_fences(self):
        self.assertFalse(match_claims('````text\n```\ndriver license extraction\n````'))
        self.assertFalse(match_claims('~~~\n```\ndriver license extraction\n~~~'))
        self.assertTrue(match_claims('    ```\ndriver license extraction\n    ```'))
        self.assertFalse(match_claims('```\n```text\ndriver license extraction\n```'))

    def test_no_source(self):
        self.assertEqual(self.report()['findings'][0]['severity'],'HIGH')
        self.assertEqual(self.report('no driver license extraction')['verdict'],'PASS')

    def test_production(self):
        self.assertEqual(self.report(source=MIND)['verdict'],'PASS')
        finding=self.report('no driver license extraction', GENERIC)['findings'][0]
        self.assertEqual((finding['rule'],finding['severity']),(NEGATIVE_RULE,'HIGH'))

    def test_one_finding(self):
        self.assertEqual(len(self.report('\n\n'.join(POS),'')['findings']),1)

    def test_no_claim(self):
        self.assertEqual(self.report('Neutral.',GENERIC)['verdict'],'PASS')

    def test_split_modules(self):
        self.write('client.py','import mindee\nc=mindee.Client()')
        self.assertFalse(self.report(source='import mindee\nc.parse(DriverLicenseV1)')['evidence'])

    def test_syntax(self):
        self.assertFalse(module_evidence(MIND+'\ndef broken('))

    def test_dead_code(self):
        self.assertTrue(module_evidence('if False:\n    '+GENERIC))

    def test_client_alias(self):
        self.assertTrue(module_evidence('from mindee import Client as C\nc=C()\nc.parse(product.DriverLicenseV1)'))
        self.assertTrue(module_evidence('import mindee.Client as C\nC()\nc.parse(DriverLicenseV1)'))
        self.assertFalse(module_evidence('import mindee as m\nm.Client()\nc.parse(DriverLicenseV1)'))

    def test_product_alias_not_exact(self):
        self.assertFalse(module_evidence('from mindee import Client\nfrom mindee.product import DriverLicenseV1 as D\nClient()\nc.parse(D)'))

    def test_parse_forms(self):
        self.assertTrue(module_evidence('from mindee import Client\nClient()\nunrelated.parse(product_class=DriverLicenseV1)'))
        self.assertFalse(module_evidence('import mindee\nmindee.Client()\nparse(DriverLicenseV1)'))

    def test_local_methods(self):
        self.assertFalse(module_evidence(MIND+'\nclass Local:\n def parse(self): pass'))
        self.assertFalse(module_evidence(GENERIC+'\nclass Local:\n def extract_driver_license(self): pass'))

    def test_local_class(self):
        self.assertFalse(module_evidence('from sdk import extract_driver_license\nclass extract_driver_license: pass\nextract_driver_license()'))

    def test_shadowed_client_and_product(self):
        for extra in ['mindee=other','DriverLicenseV1=other']:
            with self.subTest(extra=extra):
                self.assertFalse(module_evidence(MIND+'\n'+extra))
        self.assertFalse(module_evidence('from mindee import Client\nClient=other\nClient()\nc.parse(DriverLicenseV1)'))

    def test_imported_base_shadow(self):
        self.assertFalse(module_evidence('import sdk as service\nservice=other\n'+GENERIC))

    def test_encoding_cookie(self):
        self.write('README.md','driver license extraction')
        (self.root/'app.py').write_bytes(b'# coding: latin-1\n# caf\xe9\nservice.extract_driver_license()')
        self.assertEqual(audit(self.root)['verdict'],'PASS')

    def test_ignore(self):
        self.write('vendor/app.py',GENERIC)
        self.write('vendorish/app.py','# neutral')
        result=self.report(ignore=['vendor'])
        self.assertFalse(result['evidence'])
        self.assertEqual(result['source_files'],['vendorish/app.py'])
        self.write('docs/guide.md','driver license extraction')
        self.assertFalse(audit(self.root,['docs'])['claims'][1:])

    def test_doc_paths(self):
        for name in ['guide.md','sub/README.md','nested/docs/guide.md']:
            self.write(name,'driver license extraction')
        self.assertEqual([c['path'] for c in audit(self.root)['claims']],['nested/docs/guide.md'])

    def test_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'app.py'
            target.write_text(GENERIC)
            (self.root/'linked.py').symlink_to(target)
            (self.root/'linked').symlink_to(directory,target_is_directory=True)
            result=self.report()
            self.assertFalse(result['evidence'])
            self.assertFalse(result['source_files'])

    def test_bad_path(self):
        self.assertEqual(self.cli(['audit',str(self.root/'missing')])[0],1)

    def test_io_error(self):
        with patch('driver_license_extraction_claim_audit.__main__.audit',side_effect=PermissionError('unreadable')):
            self.assertEqual(self.cli(['audit'])[0],1)

    def test_cli_usage(self):
        for args in [[],['unknown'],['audit','--fail-on','HIGH'],['audit','--ignore'],['audit','--ignore','a','b','c']]:
            with self.subTest(args=args):
                self.assertEqual(self.cli(args)[0],1)

    def test_cli_version(self):
        code,output,_=self.cli(['--version'])
        self.assertEqual((code,output.strip()),(0,'0.1.0'))

    def test_cli_json(self):
        self.report()
        code,output,_=self.cli(['audit',str(self.root),'--json'])
        self.assertEqual(code,2)
        self.assertEqual(json.loads(output)['findings'][0]['severity'],'HIGH')

    def test_medium_threshold(self):
        self.report(source=GENERIC,name='tests/test_impl.py')
        self.assertEqual(self.cli(['audit',str(self.root)])[0],0)
        self.assertEqual(self.cli(['audit',str(self.root),'--fail-on','medium'])[0],2)

    def test_pass_verbose(self):
        self.report(source=GENERIC)
        code,output,_=self.cli(['audit',str(self.root),'--verbose'])
        self.assertEqual(code,0)
        self.assertIn('app.py:1:',output)

    def test_repeat_ignore(self):
        self.report(source=GENERIC,name='one/app.py')
        self.write('two/app.py',GENERIC)
        self.assertEqual(self.cli(['audit',str(self.root),'--ignore','one','--ignore','two'])[0],2)

    def test_default_root(self):
        with patch('driver_license_extraction_claim_audit.__main__.audit',return_value=dict(verdict='PASS',findings=[])) as mocked:
            self.assertEqual(self.cli(['audit'])[0],0)
            mocked.assert_called_once_with('.',[])

    def test_readme(self):
        text=(Path(__file__).resolve().parents[1]/'README.md').read_text()
        self.assertFalse(match_claims(text))
        for phrase in POS+NEG:
            self.assertIn(phrase,text)


def add(name, function):
    setattr(AuditTests,'test_'+name,function)

for index,phrase in enumerate(POS+NEG):
    def phrase_case(self,phrase=phrase,index=index):
        claims=match_claims(phrase)
        self.assertEqual(len(claims),1)
        self.assertEqual(claims[0]['phrase'],phrase)
        self.assertEqual(claims[0]['family'],'DRIVERLICENSEEXTRACTION' if index<50 else 'NODRIVERLICENSEEXTRACTION')
    add('phrase_%02d'%index,phrase_case)

for name in sorted(GENERIC_NAMES):
    def generic(self,name=name):
        self.assertTrue(module_evidence('service.'+name+'(document)'))
        self.assertTrue(module_evidence('from sdk import '+name+' as route\nroute(document)'))
        self.assertFalse(module_evidence(name+'(document)'))
        self.assertFalse(module_evidence('from sdk import '+name+'\ndef '+name+'(): pass\n'+name+'()'))
    add('generic_'+name,generic)

for product in ('PassportV1 InternationalIdV2 IdCardV1 IdCardV2 HealthcareCardV1 HealthCardV1 IndianPassportV1 ReceiptV5 InvoiceV4 InvoiceSplitterV1 MultiReceiptsDetectorV1 FinancialDocumentV1 BankCheckV1 BankAccountDetailsV1 BankAccountDetailsV2 PayslipV2 PayslipV3 BusinessCardV1 CustomV1 GeneratedV1 BillOfLadingV1 ResumeV1 DeliveryNoteV1 CarteGriseV1 EnergyBillV1 NutritionFactsLabelV1 MaterialCertificateV1 BarcodeReaderV1 CropperV1 UsMailV2 UsMailV3 DriverLicenseV2 TypeDriverLicenseV1').split():
    def other(self,product=product):
        self.assertFalse(module_evidence(MIND.replace('DriverLicenseV1',product)))
    add('other_product_'+product,other)

EXCLUDED = [
'import mindee','import mindee\nmindee.Client()','import mindee\nc.parse(DriverLicenseV1)',
'Client()\nc.parse(DriverLicenseV1)', 'service.extract_license()', 'service.parse_license()',
'service.extract_licenses()', 'service.parse_licenses()', 'service.extract_license_data()', 'service.parse_license_data()',
'service.extract_id()', 'service.parse_id()', 'service.extract_document()', 'service.parse_document()',
'import veryfi\nv=veryfi.Client()\nv.process_driver_license()', 'v.process_drivers_license()', 'v.process_driver_license_url()',
'v.process_document()', 'v.process_any_document()', 'v.split_and_process_pdf()', 'v.process_w2_document()',
'v.process_w9_document()', 'v.process_w8_document()', 'v.process_check()', 'v.process_bank_statement_document()',
'v.process_bussines_card_document()', 'v.get_pdf()', 'v.get_documents_from_pdf()', 'v.get_business_card()',
'g.process_document(processor="US_DRIVER_LICENSE_PROCESSOR")','g.batch_process_documents()',
't.analyze_id()', 't.analyze_document()', 't.analyze_expense()', 'passporteye.read_mrz()',
'requests.post("https://api.edenai.run/v2/universal-ai", json={"model":"driver_license"})',
'LlamaParse().parse()', 'nanonets.ocr(model_id="opaque")', 'docsumo.upload()', 'abbyy.process(skill_id="opaque")',
'rossum.upload(queue="opaque")', 'klippa.parse()', 'parseur.upload()', 'extend.extract(workflow="opaque")',
'mindee.ClientV2().enqueue_and_get_inference(model_id="opaque")', 'pytesseract.image_to_string(page)',
'fitz.extract_text()', 'pdfplumber.extract_text()', 'camelot.read_pdf()', 'tabula.read_pdf()',
'pandas.read_csv()', 'pandas.read_excel()', 're.search("id",text)', 're.findall("id",text)',
'service.classify_document()', 'service.is_driver_license()',
'subprocess.run(["extract_driver_license","image.jpg"])', '"service.extract_driver_license()"',
'# service.extract_driver_license()', 'service.extract_driver_license']
for index,source in enumerate(EXCLUDED):
    def excluded(self,source=source):
        self.assertFalse(module_evidence(source))
    add('excluded_%02d'%index,excluded)

for model in ('prebuilt-idDocument prebuilt-healthInsuranceCard.us prebuilt-receipt prebuilt-invoice prebuilt-layout prebuilt-read prebuilt-check.us prebuilt-tax.us prebuilt-bankStatement.us prebuilt-payStub.us prebuilt-businessCard prebuilt-creditCard prebuilt-contract prebuilt-mortgage.us.1003 prebuilt-vaccinationCard driver_license').split():
    def azure(self,model=model):
        self.assertFalse(module_evidence('client.begin_analyze_document('+repr(model)+',document)'))
    add('azure_'+model.replace('-','_').replace('.','_'),azure)

for index,product in enumerate(['DriverLicenseV1','product.DriverLicenseV1','mindee.product.DriverLicenseV1','mindee.product.driver_license.DriverLicenseV1']):
    def product_form(self,product=product):
        self.assertTrue(module_evidence(MIND.replace('DriverLicenseV1',product)))
    add('product_form_%d'%index,product_form)

for index,binding in enumerate(['route=other','route: object=other','with ctx() as route:\n pass','async def f():\n async with ctx() as route:\n  pass']):
    def shadow(self,binding=binding):
        self.assertFalse(module_evidence('from sdk import extract_driver_license as route\n'+binding+'\nroute()'))
    add('binding_%d'%index,shadow)

for index,name in enumerate(['tests/a.py','nested/tests/a.py','test_app.py','app_test.py']):
    def test_only(self,name=name):
        result=self.report(source=GENERIC,name=name)
        self.assertEqual(result['findings'][0]['severity'],'MEDIUM')
        self.assertTrue(result['evidence'][0]['test'])
    add('test_location_%d'%index,test_only)

for index,name in enumerate(['fixtures/a.py','nested/fixtures/a.py','docs/a.py','examples/a.py','tests/fixtures/a.py']):
    def excluded_location(self,name=name):
        result=self.report(source=GENERIC,name=name)
        self.assertFalse(result['evidence'])
        self.assertEqual(result['findings'][0]['severity'],'HIGH')
    add('excluded_location_%d'%index,excluded_location)

for index,marker in enumerate(['```','~~~','   ```','   ~~~']):
    def fence(self,marker=marker):
        self.assertFalse(match_claims(marker+'\n'+'\n'.join(POS+NEG)+'\n'+marker))
    add('fence_%d'%index,fence)

if __name__=='__main__':
    unittest.main()
