import joblib

class Articles(object):
    def __init__(self, titles, redirects):
        self.titles = titles
        self.redirects = redirects

    def __contains__(self, key):
        title = self.normalize_title(key)
        return title in self.titles or title in self.redirects

    def __getitem__(self, key):
        title = self.resolve_redirect(key)
        if title is None:
            raise KeyError(key)
        else:
            return title

    def resolve_redirect(self, title):
        title = self.normalize_title(title)
        if title in self.titles:
            return title
        elif title in self.redirects:
            return self.redirects[title]
        else:
            return None

    @staticmethod
    def normalize_title(title):
        title = title.strip()
        if len(title) > 0:
            return title[0].upper() + title[1:]
        else:
            return ''

    def save(self, fname, compress=3):
        data = [self.titles, self.redirects]
        joblib.dump(data, fname, compress)

    @classmethod
    def load(self, fname):
        (titles, redirects) = joblib.load(fname)
        return Articles(titles, redirects)
