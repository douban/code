from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
        self.script = 0

    def handle_data(self, d):
        if not self.script:
            self.fed.append(d)

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.script += 1

    def handle_endtag(self, tag):
        if tag == "script":
            self.script -= 1

    def get_data(self):
        return ''.join(self.fed)


def remove_html_tags(st):
    s = MLStripper()
    s.feed(st)
    return s.get_data()


def remove_consecutive_whitespace(st):
    return ' '.join(st.split())


def html_index_content(st):
    '''remove html tags.'''
    st = st.decode("utf-8")
    tmp = HTMLParser().unescape(st)
    tmp = remove_html_tags(tmp)
    return remove_consecutive_whitespace(tmp)
