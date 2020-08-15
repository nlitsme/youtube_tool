"""
A tool for investigating youtube json dictionaries.

This tries to pretty print the rather complex json dictionaries youtube uses.
You can pass the json either through stdin, pass it as a string on the commandline,
or as a filename on the commandline.


Author: Willem Hengeveld <itsme@xs4all.nl>
"""
import json
import sys
import os.path


def extractruns(runs):
    """
    Extract all text in a 'runs' dictionary.
    """
    text = []
    for r in runs:
        text.append(r.get('text'))
    return "".join(text)


def pathendswith(path, *end):
    """
    A helper for matching paths in the json dictionary.
    """
    if len(end) > len(path):
        return False
    for a, b in zip(path[-len(end):], end):
        if type(b)==type:
            if type(a)!=b:
                return False
        elif type(b)==int:
            if a != b:
                return False
        elif type(a)==int:
            return False
        elif b[:1] == '*':
            if not a.endswith(b[1:]):
                return False
        else:
            if a != b:
                return False
    return True


def processRender(j, path):
    """
    print all properties directly under 'j'
    """
    info = []
    for k, item in j.items():
        if type(item) in (int, float, str, bool):
            info.append((k, item))
        elif type(item) != dict:
            pass
        elif runs := item.get('runs'):
            info.append((k, extractruns(runs)))
        elif text := item.get("simpleText"):
            info.append((k, text))
    indent = "  " * len(path)
    print(indent, "==== %s" % (path[::-1],))
    for k, v in info:
        print(indent, "|    %-20s : %s" % (k, v))


def process(j, path=[]):
    """
    recursively process the json dictionary passed in 'j'.

    Printing all 'Renderer' dictionaries in detail, indented according to path length.

    The path is the list of keys needed to find the current entry from the top.
    """
    if path:
        if pathendswith(path, "*Renderer"):
            if type(j)!=dict:
                print("Renderer without dict", path)
            else:
                processRender(j, path)
        elif pathendswith(path, "continuations"):
            if not pathendswith(path, "*Renderer", "continuations"):
                print("continuations without renderer", path)
            pass
        elif pathendswith(path, "nextContinuationData"):
            if not pathendswith(path, "continuations", int, "nextContinuationData"):
                print("continuationData without continuation", path)
            pass
        elif pathendswith(path, "continuation"):
            if not pathendswith(path, "nextContinuationData", "continuation"):
                print("continuation without continuationData", path)
            pass

    if type(j) == list:
        for i, item in enumerate(j):
            process(item, path + [i])
    elif type(j) == dict:
        for k, item in j.items():
            process(item, path + [k])
    elif type(j) in (int, float, str, bool, type(None)):
        pass
    else:
        print("unexpected type", type(j), j)


def main():
    if len(sys.argv)==1:
        data = sys.stdin.read()
        j = json.loads(data)
        process(j)
    else:
        for arg in sys.argv[1:]:
            if os.path.exists(arg):
                try:
                    with open(arg, "r") as fh:
                        print("==>", arg, "<==")
                        j = json.load(fh)
                        process(j)
                except Exception as e:
                    print("ERROR reading %s: %s" % (arg, e))
            else:
                print("==> json commandline argument <==")
                j = json.loads(arg)
                process(j)

if __name__ == '__main__':
    main()


