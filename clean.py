import json
import gzip
import argparse

import joblib
from logzero import logger
from tqdm import tqdm

from common import Articles, Extractor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('cirrus_content_file', type=argparse.FileType(),
        help='Wikipedia Cirrussearch content file (.json)')
    parser.add_argument('out_file', type=argparse.FileType('wt'),
        help='output file (.json)')
    parser.add_argument('articles_file', type=str,
        help='articles file (.pickle)')
    parser.add_argument('--wikilink', default='preserve',
        choices=('remove', 'preserve', 'annotate'),
        help='wikilink extraction mode [preserve]')
    parser.add_argument('--ns6', type=str, nargs='*')
    parser.add_argument('--ns14', type=str, nargs='*')
    parser.add_argument('--total', type=int, default=None)
    args = parser.parse_args()

    logger.info('loading articles file')
    articles = Articles.load(args.articles_file)
    logger.info('initializing extractor')
    extractor = Extractor(articles,
        wikilink_mode=args.wikilink, ns6=args.ns6, ns14=args.ns14)

    logger.info('processing Wikipedia pages')
    for line in tqdm(args.cirrus_content_file, total=args.total, ncols=60):
        item = json.loads(line)
        if 'index' in item:
            pageid = item['index']['_id']
            pageid = int(pageid) if pageid.isdigit() else None
        elif pageid is not None:
            title = item['title']
            namespace = item.get('namespace', -1)
            if title == '' or namespace != 0:
                continue

            wikidata_id = item.get('wikibase_item', None)
            wikitext = item.get('source_text', '')
            categories = item.get('category', [])
            n_inlinks = item.get('incoming_links', 0)

            redirects = []
            for redir in item.get('redirect', []):
                if redir['namespace'] == 0:
                    redirects.append(redir['title'])

            wikitext = extractor.extract(wikitext)
            sections = extractor.split_sections(wikitext)

            out = {
                'title': title,
                'pageid': pageid,
                'wikidata_id': wikidata_id,
                'categories': categories,
                'redirects': redirects,
                'n_inlinks': n_inlinks,
                'sections': sections
            }
            print(json.dumps(out, ensure_ascii=False), file=args.out_file)


if __name__ == '__main__':
    main()
