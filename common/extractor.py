import re
from collections import Counter
from urllib.parse import quote

from logzero import logger


regex_comment = re.compile(r'<!--(.*?)-->', re.DOTALL)

regex_nowiki = re.compile(r'<nowiki>(.*?)</nowiki>', re.DOTALL)
regex_ref1 = re.compile(r'<(ref|references)(.*?)?>(.*?)</\1>', re.DOTALL)
regex_ref2 = re.compile(r'<(ref|references)(.*?)?/>', re.DOTALL)
regex_gallery = re.compile(r'<gallery(.*?)?>(.*?)</gallery>', re.DOTALL)
regex_imagemap = re.compile(r'<imagemap(.*?)?>(.*?)</imagemap>', re.DOTALL)
regex_score = re.compile(r'<score(.*?)?>(.*?)</score>', re.DOTALL)
regex_math = re.compile(r'<(math chem|math|chem)(.*?)?>(.*?)</\1>', re.DOTALL)
regex_timeline = re.compile(r'<timeline(.*?)?>(.*?)</timeline>', re.DOTALL)
regex_br = re.compile(r'<br ?/?>')
regex_html = re.compile(r'<[^><]+?/?>', re.DOTALL)

regex_magic_word = re.compile(r'__([A-Z]+?)__')
regex_template_lang = re.compile(r'{{ *[lL]ang *[|-] *[a-z][a-z][\w-]* *\| *([^}]*) *}}')
regex_template_unicode = re.compile(r'{{ *[uU]nicode *\| *([^}]*) *}}')
regex_template_ill = re.compile(r'{{ *([iI]ll|仮リンク) *\| *([^}|]*?) *\|[^}]*}}')
regex_template = re.compile(r'{{[^}{]*?}}', re.DOTALL)

regex_internal_link = re.compile(r'\[\[([^][]+?)\]\]')
regex_external_link = re.compile(r'\[([^][]*?://[^][ ]*?)( [^][]+?)?\]')
regex_file = re.compile(r'\[\[([fF]ile|Datei|[iI]mage|Bild):([^][]+?)\]\]')
regex_category = re.compile(r'\[\[([cC]ategory|Kategorie):([^][]+?)\]\]')

regex_inlink_token = re.compile(r'/\((.+?)/(.+?)\)/')

regex_highlight = re.compile(r"''+(.*?)''+")
regex_list = re.compile(r'[\n^] *[*#;:]+ *(.*?)(?=\n)')

regex_table_fomrat = re.compile(r'\n *({\||\|-|\|})(.*?)(?=\n)')
regex_table_cell = re.compile(r'\n *(\||\!)(.*?\|)* *([^|]*?)(?=\n)')

regex_blank_lines = re.compile(r'\n\n+')

regex_heading = re.compile(r'(==+) *(.+?) *\1')

regex_numeric = re.compile(r'^[a-z0-9.+\-*/^=!><()^ ]+$')


def normalize_page_title(title):
    return (title[0].upper() + title[1:]).replace('_', ' ')


class Extractor(object):
    def __init__(self, articles,
            wikilink_mode='preserve', ns6=None, ns14=None):
        assert wikilink_mode in ('remove', 'preserve', 'annotate')
        self.articles = articles
        self.wikilink_mode = wikilink_mode

        ns6_aliases = [r'[fF]ile', r'[iI]mage']
        if ns6 is not None:
            ns6_aliases += ns6
        self.regex_file = re.compile(
            r'\[\[(' + r'|'.join(ns6_aliases) + r'):([^][]+?)\]\]')

        ns14_aliases = [r'[cC]ategory']
        if ns14 is not None:
            ns14_aliases += ns14
        self.regex_category = re.compile(
            r'\[\[(' + r'|'.join(ns14_aliases) + r'):([^][]+?)\]\]')

    def extract(self, wikitext):
        # put aside nowiki spans
        nowikis = []
        while True:
            match_nowiki = regex_nowiki.search(wikitext)
            if match_nowiki is None:
                break

            (start, end) = match_nowiki.span()
            nowiki_token = f'@@@NOWIKI{len(nowikis)}@@@'
            nowikis.append(match_nowiki.group(1)[1:])
            wikitext = wikitext[:start] + nowiki_token + wikitext[end:]

        # remove comments
        wikitext = regex_comment.sub('', wikitext)

        # remove references
        wikitext = regex_ref1.sub('', wikitext)
        wikitext = regex_ref2.sub('', wikitext)

        # remove galleries
        wikitext = regex_gallery.sub('', wikitext)

        # remove misc. html spans
        wikitext = regex_imagemap.sub('', wikitext)
        wikitext = regex_score.sub('', wikitext)
        wikitext = regex_math.sub('', wikitext)
        wikitext = regex_timeline.sub('', wikitext)
        wikitext = regex_br.sub(' ', wikitext)

        # remove other html tags leaving contents
        wikitext = regex_html.sub('', wikitext)

        # remove magic words
        wikitext = regex_magic_word.sub('', wikitext)

        # replace some kinds of templates
        wikitext = regex_template_lang.sub(r'\1', wikitext)
        wikitext = regex_template_unicode.sub(r'\1', wikitext)
        wikitext = regex_template_ill.sub(r'\2', wikitext)

        # remove other templates
        for _ in range(10):
            before = wikitext
            wikitext = regex_template.sub('', wikitext)
            if before == wikitext:
                break

        # remove links to files and category pages
        wikitext = self.regex_file.sub('', wikitext)
        wikitext = self.regex_category.sub('', wikitext)

        # process internal links
        internal_links = []
        while True:
            match_link = regex_internal_link.search(wikitext)
            if match_link is None:
                break

            (start, end) = match_link.span()
            if '|' in match_link.group(1):
                (title, anchor) = match_link.group(1).split('|', 1)
            else:
                title = anchor = match_link.group(1)

            title = title.strip()
            anchor = anchor.strip()

            if title.startswith('#') or title.startswith(':'):
                title = title[1:]

            if '#' in title:
                title = title[:title.find('#')]

            if anchor == '':
                anchor = title

            title = self.articles.resolve_redirect(title)
            if title is None:
                if '|' in anchor or anchor[:3].endswith(':'):
                    wikitext = wikitext[:start] + wikitext[end:]
                else:
                    wikitext = wikitext[:start] + anchor + wikitext[end:]
                continue

            internal_links.append((title, anchor))
            if self.wikilink_mode == 'remove':
                repl = anchor
            else:
                repl = f'/({title}/{anchor})/'

            wikitext = wikitext[:start] + repl + wikitext[end:]

        # process external links
        while True:
            match_link = regex_external_link.search(wikitext)
            if match_link is None:
                break

            (start, end) = match_link.span()
            if match_link.group(2) is not None:
                repl = match_link.group(2).strip()
            else:
                repl = ''

            wikitext = wikitext[:start] + repl + wikitext[end:]

        # remove highlight and list markups
        wikitext = regex_highlight.sub(r'\1', wikitext)
        wikitext = regex_list.sub(r'\n\1', wikitext)

        # remove table markups
        wikitext = wikitext.replace('||', '\n|')
        wikitext = wikitext.replace('!!', '\n!')
        wikitext = regex_table_fomrat.sub('\n', wikitext)
        wikitext = regex_table_cell.sub(r'\3 ', wikitext)

        # some formating
        wikitext = regex_blank_lines.sub('\n\n', wikitext)
        wikitext = wikitext.strip()

        # annotate entity mentions
        if self.wikilink_mode == 'annotate':
            wikitext = self.annotate_inlinks(wikitext, internal_links)

        # restore nowiki spans
        for i, nowiki in enumerate(nowikis):
            nowiki_token = f'@@@NOWIKI{i}@@@'
            start = wikitext.find(nowiki_token)
            end = start + len(nowiki_token)
            if start == -1:
                continue

            wikitext = wikitext[:start] + nowiki + wikitext[end:]

        return wikitext

    def annotate_inlinks(self, wikitext, inlinks):
        mask = '*' * len(wikitext)

        cur = 0
        while cur < len(wikitext):
            match_inlink = regex_inlink_token.search(wikitext, pos=cur)
            if match_inlink is None:
                break

            start, end = match_inlink.span()
            mask = mask[:start] + '_' * (end - start) + mask[end:]
            cur = end

        cur = 0
        while cur < len(wikitext):
            match_heading = regex_heading.search(wikitext, pos=cur)
            if match_heading is None:
                break

            start, end = match_heading.span()
            mask = mask[:start] + '_' * (end - start) + mask[end:]
            cur = end

        for (title, anchor) in sorted(inlinks, key=lambda t: -len(t[0])):
            cur = 0
            while cur < len(wikitext):
                start = wikitext.find(anchor, cur)
                if start == -1:
                    break

                inlink_token = f'/({title}/{anchor})/'
                end = start + len(anchor)
                if '_' in mask[start:end]:
                    cur = end
                else:
                    wikitext = wikitext[:start] + inlink_token + wikitext[end:]
                    mask = mask[:start] + '_' * len(inlink_token) + mask[end:]
                    cur = start + len(inlink_token)

        return wikitext

    def split_sections(self, wikitext):
        sections = []
        (start, end) = (0, 0)
        section_text = ''
        section_heading = []
        cur = 0
        for match_section in regex_heading.finditer(wikitext):
            (start, end) = match_section.span()
            section_text = wikitext[cur:start].strip()
            sections.append((section_heading, section_text))

            level = len(match_section.group(1)) - 1
            name = match_section.group(2)
            section_heading = section_heading[:level-1] + [name]
            section_text = ''
            cur = end

        section_text = wikitext[cur:].strip()
        sections.append((section_heading, section_text))

        return sections
