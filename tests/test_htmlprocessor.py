from tests.base import TestCase
from vilya.libs.htmlprocessor import html_index_content


class TestHTMLProcessor(TestCase):

    def test_process_whitespaces(self):
        html = '''
                    <h1>Title</h1>
                    <br />
                    <p>This is a paragraph.</p>
                '''
        res = html_index_content(html)
        assert res == "Title This is a paragraph."

    def test_remove_script_tags(self):
        html = '''
                    <h1>Title</h1>
                    <script type="text/javascript">
                    </script>
               '''
        res = html_index_content(html)
        assert res == "Title"

    def test_unescape(self):
        html = '''
                    <h1>Title</h1>
                    <script type="text/javascript">
                    </script>
                    <footer>
                        <a href="./" class="button_accent">
                            &nbsp;&nbsp;&nbsp;Back to blog
                        </a>
                    </footer>
                    <code>
                        print 1&lt;3
                    </code>
                '''
        res = html_index_content(html)
        assert res == "Title Back to blog print 1<3"
