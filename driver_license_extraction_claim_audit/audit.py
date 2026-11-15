"""Read-only Markdown matching and module-local AST evidence detection."""
import ast
import os
import re
from pathlib import Path

from .phrases import DRIVERLICENSEEXTRACTION, NODRIVERLICENSEEXTRACTION, GENERIC_NAMES

POSITIVE_RULE = 'documented-driver-license-extraction-claim-false'
NEGATIVE_RULE = 'documented-no-driver-license-extraction-claim-false'


def normalize(text):
    return ' '.join(text.lower().replace("n't", ' not').replace('’t', ' not').replace('-', ' ').split())


def prose(text):
    """Remove fenced blocks, retaining paragraph and source line boundaries."""
    fence = None
    result = []
    for line in text.splitlines():
        match = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', line)
        if fence:
            if match and match[1][0] == fence[0] and len(match[1]) >= fence[1] and not match[2].strip():
                fence = None
            result.append('')
        elif match and (match[1][0] != '`' or '`' not in match[2]):
            fence = (match[1][0], len(match[1]))
            result.append('')
        else:
            result.append(line)
    return '\n'.join(result)


def _pattern(phrases):
    return re.compile(r'\b(?:' + '|'.join(re.escape(p) for p in sorted(phrases, key=lambda p: (-len(p), p))) + r')\b')


_POS = _pattern(DRIVERLICENSEEXTRACTION)
_NEG = _pattern(NODRIVERLICENSEEXTRACTION)


def match_claims(text, path='README.md'):
    claims = []
    clean = prose(text)
    for paragraph in re.finditer(r'\S[^\n]*(?:\n(?!\s*\n)[^\n]*)*', clean):
        normalized = normalize(paragraph[0])
        line = clean.count('\n', 0, paragraph.start()) + 1
        for match in _NEG.finditer(normalized):
            claims.append(dict(family='NODRIVERLICENSEEXTRACTION', phrase=match[0], path=path, line=line))
        remaining = _NEG.sub(lambda m: ' ' * len(m[0]), normalized)
        for match in _POS.finditer(remaining):
            claims.append(dict(family='DRIVERLICENSEEXTRACTION', phrase=match[0], path=path, line=line))
    return claims


def module_evidence(source):
    """Return routes and line numbers; never import or execute audited source."""
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    nodes = list(ast.walk(tree))
    imports = {}
    mindee = False
    bound = set()
    definitions = set()
    for node in nodes:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
                mindee |= alias.name.split('.')[0] == 'mindee'
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            mindee |= module.split('.')[0] == 'mindee'
            for alias in node.names:
                imports[alias.asname or alias.name] = module + '.' + alias.name
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            definitions.add(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                bound.update(n.id for n in ast.walk(target) if isinstance(n, ast.Name))
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                if item.optional_vars:
                    bound.update(n.id for n in ast.walk(item.optional_vars) if isinstance(n, ast.Name))
    shadowed = bound | definitions

    def available(expr):
        if isinstance(expr, ast.Name):
            return expr.id not in shadowed
        if isinstance(expr, ast.Attribute):
            return expr.attr not in definitions and (
                expr.value.id not in definitions and not (expr.value.id in bound and expr.value.id in imports)
                if isinstance(expr.value, ast.Name) else available(expr.value))
        # A constructed object's attribute is permitted on any base.
        return True

    def imported(expr):
        if isinstance(expr, ast.Name) and available(expr):
            return imports.get(expr.id, '')
        return ''

    calls = [n for n in nodes if isinstance(n, ast.Call)]
    client = False
    parses = []
    evidence = []
    for call in calls:
        func = call.func
        if not available(func):
            continue
        if imported(func) == 'mindee.Client' or (
            isinstance(func, ast.Attribute) and func.attr == 'Client'
            and isinstance(func.value, ast.Name) and func.value.id == 'mindee'
        ):
            client = True
        if isinstance(func, ast.Attribute) and func.attr == 'parse':
            args = call.args + [kw.value for kw in call.keywords]
            if any(available(a) and ((isinstance(a, ast.Name) and a.id == 'DriverLicenseV1') or
                   (isinstance(a, ast.Attribute) and a.attr == 'DriverLicenseV1')) for a in args):
                parses.append(call.lineno)
        name = func.attr if isinstance(func, ast.Attribute) else imported(func).rsplit('.', 1)[-1]
        if name in GENERIC_NAMES and name not in definitions:
            evidence.append(dict(route='generic:' + name, line=call.lineno))
    if mindee and client:
        evidence.extend(dict(route='mindee:DriverLicenseV1', line=line) for line in parses)
    return sorted(evidence, key=lambda e: (e['line'], e['route']))


def audit(root='.', ignore=()):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise OSError('Root must be an existing, non-symlink directory')
    prefixes = [str(p).replace('\\', '/').strip('/') for p in ignore]

    def ignored(path):
        return any(path == p or path.startswith(p + '/') for p in prefixes if p)

    claims, evidence, source_files = [], [], []
    def walk_error(error):
        raise error
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        dirs[:] = sorted(d for d in dirs if not (Path(directory) / d).is_symlink()
                         and not ignored((Path(directory) / d).relative_to(root).as_posix()))
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(root)
            label = relative.as_posix()
            if path.is_symlink() or ignored(label):
                continue
            parts = relative.parts
            is_doc = label == 'README.md' or (path.suffix == '.md' and 'docs' in parts[:-1])
            if is_doc:
                claims.extend(match_claims(path.read_text(encoding='utf-8'), label))
            if path.suffix != '.py':
                continue
            source_files.append(label)
            if {'fixtures', 'docs', 'examples'} & set(parts[:-1]):
                continue
            test = 'tests' in parts[:-1] or name.startswith('test_') or name.endswith('_test.py')
            # tokenize.open respects coding cookies without executing anything.
            import tokenize
            with tokenize.open(path) as stream:
                source = stream.read()
            evidence.extend(dict(item, path=label, test=test) for item in module_evidence(source))
    production = [e for e in evidence if not e['test']]
    test_evidence = [e for e in evidence if e['test']]
    findings = []
    if any(c['family'] == 'DRIVERLICENSEEXTRACTION' for c in claims) and not production:
        findings.append(dict(rule=POSITIVE_RULE, severity='MEDIUM' if test_evidence else 'HIGH',
                             message='Documented positive claim has only test evidence.' if test_evidence else 'Documented positive claim has no production evidence.'))
    if any(c['family'] == 'NODRIVERLICENSEEXTRACTION' for c in claims) and production:
        findings.append(dict(rule=NEGATIVE_RULE, severity='HIGH', message='Documented denial contradicts production evidence.'))
    return dict(verdict='FAIL' if findings else 'PASS', findings=findings, claims=claims,
                evidence=evidence, source_files=source_files)
