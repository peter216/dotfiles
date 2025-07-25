#!/usr/bin/env python3

import logging
import optparse
import os
import re
from datetime import datetime

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import DiffLexer

logger = logging.getLogger(__name__)


# Converts markdown bulleted lists to HTML unordered lists #
def convert_markdown_lists(html_content):
    # Find sequences of list items (lines beginning with -, *, or +) #
    pattern = r"((?:^[\t ]*[-*+][ \t]+.*?(?:\n|$))+)"

    def replace_list(match):
        list_text = match.group(1)
        # Convert each list item to <li> elements #
        items = re.findall(r"^[\t ]*[-*+][ \t]+(.*?)(?:\n|$)", list_text, re.MULTILINE)
        list_items = "".join([f"<li>{item}</li>" for item in items])
        # Wrap all items in <ul> tags #
        return f"<ul>{list_items}</ul>"

    # Replace all found lists in the content #
    return re.sub(pattern, replace_list, html_content, flags=re.MULTILINE)


def convert(textfile, html_file):
    with open(textfile) as f:
        body_text = f.read()

    # Insert zero-width space to force line-break
    body_text = "\u200b\n" + body_text
    body_html = highlight(body_text, DiffLexer(), HtmlFormatter(full=True))
    body_html = re.sub(
        r"\*\*(.*?)\*\*", r"<bold>\1</bold>", body_html, flags=re.MULTILINE
    )
    body_html = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", body_html, flags=re.MULTILINE)
    body_html = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", body_html, flags=re.MULTILINE)
    body_html = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", body_html, flags=re.MULTILINE)

    # Convert markdown lists to HTML unordered lists #
    body_html = convert_markdown_lists(body_html)

    with open(html_file, "w") as f:
        f.write(body_html)
    msg = f"HTML written to {html_file}"
    logger.info(msg)
    print(msg)


def main():
    parser = optparse.OptionParser()
    parser.add_option(
        "-t",
        "--text_file",
        dest="text_file",
        help="Filename to write text to. Required.",
    )
    parser.add_option(
        "-w",
        "--html_file",
        dest="html_file",
        help="Filename to write html to. Required.",
    )
    parser.add_option(
        "-l",
        "--loglevel",
        dest="loglevel",
        help="Set the logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO",
    )
    (options, args) = parser.parse_args()

    LOGLEVEL = getattr(logging, options.loglevel.upper(), None)
    if not isinstance(LOGLEVEL, int):
        parser.error("Invalid log level: %s" % options.loglevel)
    if not options.text_file:
        parser.error("You must specify a text file to convert.")
    if not options.html_file:
        parser.error("You must specify an HTML file to write to.")
    if not os.path.exists(options.text_file):
        parser.error(f"File not found: {options.text_file}")

    # Create log directory
    os.makedirs("logs", exist_ok=True)

    detailed_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(lineno)d] - %(message)s"
    )
    file_handler = logging.FileHandler("logs/md2html.log")
    # stream_handler = logging.StreamHandler()
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    logger.setLevel(LOGLEVEL)

    logger.debug(f"options: {options}")
    logger.debug(f"args: {args}")
    convert(options.text_file, options.html_file)
    logger.debug("Conversion complete")
    logger.debug(f"New file is at {options.html_file}")


if __name__ == "__main__":
    main()
