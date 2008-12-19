import os
import re
import time


re_ident = re.compile(
    '(author|committer) (?P<ident>.*) (?P<epoch>\d+) (?P<tz>[+-]\d{4})')


class Commit(object):
    children_sha1 = {}

    def __init__(self, commit_lines):
        self.message     = ""
        self.author      = ""
        self.date        = ""
        self.commiter    = ""
        self.commit_date = ""
        self.commit_sha1 = ""
        self.parent_sha1 = []

        self.parse_commit(commit_lines)

    def parse_commit(self, commit_lines):
        line = commit_lines[0].strip()
        sha1 = line.split(" ")
        self.commit_sha1 = sha1[0]
        self.parent_sha1 = sha1[1:] or [0]

        # Build the child list
        for parent_id in self.parent_sha1:
            if parent_id not in Commit.children_sha1:
                Commit.children_sha1[parent_id] = []

            Commit.children_sha1[parent_id].append(self.commit_sha1)

        for line in commit_lines[1:]:
            if line.startswith(" "):
                if self.message == "":
                    self.message = line.strip()

                continue

            if line.startswith("tree") or line.startswith("parent"):
                continue

            m = re_ident.match(line)

            if m:
                date = self.format_date(m.group('epoch'), m.group('tz'))

                if m.group(1) == "author":
                    self.author = m.group('ident')
                    self.date = date
                elif m.group(1) == "committer":
                    self.committer = m.group('ident')
                    self.commit_date = date

                continue

    def get_message(self, with_diff=False):
        if with_diff:
            message = self.diff_tree()
        else:
            fp = os.popen("git cat-file commit " + self.commit_sha1)
            message = fp.read()
            fp.close()

        return message

    def diff_tree(self):
        fp = os.popen("git diff-tree --pretty --cc -v -p --always" +
                      self.commit_sha1)
        diff = fp.read()
        fp.close()

        return diff

    def format_date(self, epoch, tz):
        secs    = float(epoch)
        tzsecs  = float(tz[1:3]) * 3600
        tzsecs += float(tz[3:5]) * 60

        if tz.startswith("+"):
            secs += tzsecs
        else:
            secs -= tzsecs

        return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(secs))


class CommitGraph(object):
    def __init__(self):
        self.bt_sha1 = {}

        self.colors = {}
        self.node_pos = {}
        self.incomplete_line = {}

    def update_bt_sha1(self):
        self.bt_sha1 = {}
        ls_remote = re.compile('^(.{40})\trefs/([^^]+)(?:\\^(..))?$');
        fp = os.popen('git ls-remote "${GIT_DIR-.git}"')

        while True:
            line = fp.readline().strip()

            if line == "":
                break

            m = ls_remote.match(line)

            if m:
                sha1 = m.group(1)
                name = m.group(2)

                if sha1 not in self.bt_sha1:
                    self.bt_sha1[sha1] = []

                self.bt_sha1[sha1].append(name)

        fp.close()

    def get_commits(self):
        self.update_bt_sha1()

        index = 0
        last_color = 0
        last_node_pos = -1
        out_lines = []

        fp = os.popen("git rev-list --parents --all --header --topo-order")

        commit_lines = []

        for input_line in fp.xreadlines():
            # The commit header ends with '\0'.
            # This NUL is immediately folllowed by the sha1 of the
            # next commit.
            if input_line[0] != '\0':
                commit_lines.append(input_line)
            else:
                commit = Commit(commit_lines)

                out_lines, last_color, last_node_pos = \
                    self.make_graph(commit, index, out_lines, last_color,
                                    last_node_pos)
                index += 1

                yield commit

                # Skip the '\0'
                commit_lines = [input_line[1:]]

        fp.close()

        # Reset so we don't have to store this data.
        self.colors = {}
        self.node_pos = {}
        self.incomplete_line = {}


    def make_graph(self, commit, index, out_lines, last_color, last_node_pos):
        in_lines = []

        #   |   -> out_line
        #   X
        #   |\  <- in_line

        # Add the incomplete lines of the last call in this
        if commit.commit_sha1 not in self.colors:
            last_color = self.colors[commit.commit_sha1] = last_color + 1

        color = self.colors[commit.commit_sha1]

        if commit.commit_sha1 not in self.node_pos:
            last_node_pos = self.node_pos[commit.commit_sha1] = \
                last_node_pos + 1

        node_pos = self.node_pos[commit.commit_sha1]

        # The first parent always continues on the same line
        key = commit.parent_sha1[0]

        if key not in self.node_pos:
            self.colors[key] = color
            self.node_pos[key] = node_pos

        for sha1 in self.incomplete_line.keys():
            if sha1 != commit.commit_sha1:
                self.make_incomplete_line(sha1, node_pos, out_lines,
                                          in_lines, index)
            else:
                del self.incomplete_line[sha1]

        for parent_id in commit.parent_sha1:
            if parent_id not in self.node_pos:
                last_color = self.colors[parent_id] = last_color + 1
                last_node_pos = self.node_pos[parent_id] = \
                    last_node_pos + 1
            else:
                last_node_pos = self.node_pos[parent_id]

            in_lines.append((node_pos, self.node_pos[parent_id],
                             self.colors[parent_id]))
            self.add_incomplete_line(parent_id)

        branch_tag = self.bt_sha1.get(commit.commit_sha1, [])

        commit.node = (node_pos, color, branch_tag)

        # This is actually not wrong. The commit's out lines are the in lines
        # we processed, and vice-versa.
        commit.out_lines = in_lines
        commit.in_lines = out_lines

        return (in_lines, last_color, last_node_pos)

    def add_incomplete_line(self, sha1):
        if sha1 not in self.incomplete_line:
            self.incomplete_line[sha1] = []

        self.incomplete_line[sha1].append(self.node_pos[sha1])

    def make_incomplete_line(self, sha1, node_pos, out_lines, in_lines, index):
        for idx, pos in enumerate(self.incomplete_line[sha1]):
            if pos == node_pos:
                # Remove the straight line and add a slash
                line = (pos, pos, self.colors[sha1])

                if line in out_lines:
                    out_lines.remove(line)

                out_lines.append((pos, pos + 0.5, self.colors[sha1]))
                self.incomplete_line[sha1][idx] = pos = pos + 0.5

            next_index = index + 1

#            if len(self.commits) > next_index + 1:
#                next_commit = self.commits[next_index]
#
#                if next_commit.commit_sha1 == sha1 and pos != int(pos):
#                    # Join the line back to the node point.
#                    # This needs to be done only if we modified it.
#                    in_lines.append((pos, pos - 0.5, self.colors[sha1]))
#                    continue

            in_lines.append((pos, pos, self.colors[sha1]))
