"""Command-line entry point."""
import argparse
import json
import sys
from . import __version__
from .audit import audit


class Parser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(1, '%s: error: %s\n' % (self.prog, message))


def main(argv=None):
    parser = Parser(prog='driver-license-extraction-claim-audit')
    parser.add_argument('--version', action='version', version=__version__)
    sub = parser.add_subparsers(dest='command', required=True, parser_class=Parser)
    command = sub.add_parser('audit', help='Compare documentation claims with static source evidence')
    command.add_argument('repo', nargs='?', default='.')
    command.add_argument('--json', action='store_true')
    command.add_argument('--verbose', action='store_true')
    command.add_argument('--ignore', action='append', default=[], metavar='PREFIX')
    command.add_argument('--fail-on', choices=['high', 'medium'], default='high')
    args = parser.parse_args(argv)
    try:
        report = audit(args.repo, args.ignore)
    except (OSError, UnicodeError, SyntaxError) as error:
        print('error: ' + str(error), file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(report['verdict'])
        for finding in report['findings']:
            print('{severity} {rule}: {message}'.format(**finding))
        if args.verbose:
            for claim in report['claims']:
                print('{path}:{line}: {family}: {phrase}'.format(**claim))
            for item in report['evidence']:
                print('{path}:{line}: {route} (test={test})'.format(**item))
            print('Source files: ' + str(len(report['source_files'])))
    return 2 if any(f['severity'] == 'HIGH' or args.fail_on == 'medium' for f in report['findings']) else 0


if __name__ == '__main__':
    sys.exit(main())
