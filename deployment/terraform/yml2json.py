#!/usr/bin/env python

import sys
from os.path import splitext
import yaml
import yamlordereddictloader
import json
import argparse


def yml2json(yml):
    return json.dumps(yaml.load(yml, Loader=yamlordereddictloader.Loader), indent=2)


def main():
    parser = argparse.ArgumentParser(description='tool to convert yml to json')
    parser.add_argument('filename', help='Filename of yml file to convert. '
                                         'Use - for STDIN.')
    args = parser.parse_args()
    if args.filename != '-':
        with open(args.filename, 'r') as f:
            json = yml2json(f.read())
        with open(splitext(args.filename)[0] + '.json', 'w') as dst:
            dst.write(json)
    else:  # pipe mode
        json = yml2json(sys.stdin)
        sys.stdout.write(json)


if __name__ == '__main__':
    main()
