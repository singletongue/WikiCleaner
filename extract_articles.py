import json
import gzip
import argparse

import joblib
from logzero import logger
from tqdm import tqdm

from common import Articles


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cirrus_content_file', type=str,
        help='Wikipedia Cirrussearch content file (.json.gz)')
    parser.add_argument('out_file', type=str,
        help='output file (.pickle)')
    parser.add_argument('--total', type=int, default=None,
        help='total number of lines in input file')
    args = parser.parse_args()

    titles = dict()
    redirects = dict()

    logger.info('loading Cirrussearch file')
    with gzip.open(args.cirrus_content_file, 'rt') as f:
        for line in tqdm(f, total=args.total, ncols=60):
            jobj = json.loads(line)
            title = jobj.get('title', '')
            namespace = jobj.get('namespace', -1)
            if title == '' or namespace != 0:
                continue

            for redir in jobj.get('redirect', []):
                if redir['namespace'] == 0:
                    redirects[redir['title']] = title

            n_inlinks = jobj.get('incoming_links', 0)
            titles[title] = n_inlinks

    articles_obj = Articles(titles, redirects)

    logger.info('saving into file')
    articles_obj.save(args.out_file, compress=3)


if __name__ == '__main__':
    main()
