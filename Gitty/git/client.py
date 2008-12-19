import os


class Client(object):
    def __init__(self, path):
        self.path = path
        self.encoding = None

    def get_encoding(self):
        if not self.encoding:
            fp = os.popen("git config --get i18n.commitencoding")
            self.encoding = fp.readline().strip() or "utf-8"
            fp.close()

        return self.encoding

    def diff_tree(self, parent_sha1, commit_sha1):
        fp = os.popen("git diff-tree -p %s %s" % (parent_sha1, commit_sha1))
        contents = unicode(fp.read(), self.get_encoding()).encode("utf-8")
        fp.close()

        return contents

    def get_commit_header(self, sha1):
        fp = os.popen("git cat-file commit %s" % sha1)
        contents = unicode(fp.read(), self.get_encoding()).encode("utf-8")
        fp.close()

        in_headers = True

        header = {
            "message": "",
        }

        for line in contents.splitlines():
            if in_headers:
                parts = line.split()

                if not parts:
                    in_headers = False
                elif parts[0] == "tree":
                    header["tree"] = parts[1]
                elif parts[0] == "parent":
                    header["parent"] = parts[1]
                elif parts[0] == "author":
                    header["author"] = {
                        'time': ' '.join(parts[-2:]),
                        'name': ' '.join(parts[1:-2]),
                    }
                elif parts[0] == "committer":
                    header["committer"] = {
                        'time': ' '.join(parts[-2:]),
                        'name': ' '.join(parts[1:-2]),
                    }
            else:
                header['message'] += line + "\n"

        return header
