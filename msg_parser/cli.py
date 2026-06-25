# -*- coding: utf-8 -*-

"""Console script for msg_parser."""
import os.path
import sys
from argparse import Action
from argparse import ArgumentParser
from argparse import ArgumentTypeError
from pprint import pprint

from msg_parser import MsOxMessage
from msg_parser import convert_to_markdown


class FullPaths(Action):
    """Expand user- and relative-paths"""

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(os.path.expanduser(values)))


def is_dir(dir_name):
    """Checks if a path is an actual directory"""
    if not os.path.isdir(dir_name):
        msg = "{0} is not a directory".format(dir_name)
        raise ArgumentTypeError(msg)
    else:
        return dir_name


def existing_path(path):
    """Checks that a path (file or directory) exists."""
    expanded = os.path.abspath(os.path.expanduser(path))
    if not os.path.exists(expanded):
        raise ArgumentTypeError("{0} does not exist".format(path))
    return expanded


def create_parser(args):
    parser = ArgumentParser(description="Microsoft Message Parser")
    parser.add_argument(
        "-i",
        "--input",
        dest="input_file",
        required=True,
        help="path to a .msg file (or a directory of .msg files for markdown output)",
        metavar="PATH",
        type=existing_path,
    )
    parser.add_argument(
        "-j",
        "--json",
        help="output parsed msg as json to console",
        dest="json_output",
        action="store_true",
    )
    parser.add_argument(
        "-e",
        "--eml",
        help="provide a directory path to save the message as an eml file.",
        dest="eml_file",
        action=FullPaths,
        type=is_dir,
    )
    parser.add_argument(
        "-m",
        "--markdown",
        help="convert the message(s) to Markdown with YAML frontmatter",
        dest="markdown",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output .md file or directory for --markdown (defaults next to the source)",
        dest="output",
        action=FullPaths,
        default=None,
    )
    parser.add_argument(
        "-r",
        "--recursive",
        help="recurse into sub-directories when the input is a directory",
        dest="recursive",
        action="store_true",
    )
    return parser.parse_args(args)


def main():
    args = create_parser(sys.argv[1:])

    input_file = args.input_file

    if args.markdown:
        written = convert_to_markdown(
            input_file, args.output, recursive=args.recursive
        )
        if not written:
            print("No .msg files found to convert.")
        elif args.output is None and os.path.isfile(input_file):
            # Single file with no explicit output: print to stdout as well.
            with open(written[0], encoding="utf-8") as md_file:
                print(md_file.read())
            print("Markdown written to: {0}".format(written[0]))
        else:
            for path in written:
                print("Markdown written to: {0}".format(path))
        return 0

    if args.json_output:
        ms_msg = MsOxMessage(input_file)
        pprint(ms_msg.get_message_as_json())

    eml_file = args.eml_file

    if eml_file:
        ms_msg = MsOxMessage(input_file)
        ms_msg.save_email_file(eml_file)

    return 0


if __name__ == "__main__":
    sys.exit(main())
