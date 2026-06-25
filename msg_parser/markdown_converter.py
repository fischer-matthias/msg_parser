# -*- coding: utf-8 -*-

"""Convert Outlook ``.msg`` files into Markdown documents.

The mail header information (subject, sender, recipients, dates, message id,
attachments, ...) is rendered as a YAML frontmatter block while the mail body
becomes the Markdown content of the document.

This module can convert a single ``.msg`` file or a whole directory of
``.msg`` files in one go.
"""
import html as html_module
import os
import re
from datetime import datetime

import yaml

from .msg_parser import MsOxMessage

MSG_EXTENSION = ".msg"
MARKDOWN_EXTENSION = ".md"

_HTML_MARKER = re.compile(r"<\s*html", re.IGNORECASE)


class MarkdownConverter(object):
    """Render a parsed :class:`MsOxMessage` as a Markdown document."""

    def __init__(self, msg_object):
        self.msg = msg_object

    @staticmethod
    def _normalize_address(address):
        """Tidy up a single ``"name <email>"`` address string."""
        if not address:
            return None
        address = str(address).strip()
        # ``parse_email_headers`` formats addresses as "name <email>"; when the
        # display name is empty this collapses to "<email>".
        if address.startswith("<") and address.endswith(">"):
            address = address[1:-1].strip()
        else:
            # Collapse redundant "email <email>" pairs to a single address.
            match = re.match(r"^(?P<name>.*?)\s*<(?P<email>[^>]+)>$", address)
            if match and match.group("name").strip() == match.group("email").strip():
                address = match.group("email").strip()
        return address or None

    def _address_list(self, value):
        """Coerce a header value into a clean list of address strings."""
        if not value:
            return []

        if isinstance(value, (list, tuple, set)):
            items = list(value)
        else:
            items = [part for part in str(value).split(",")]

        cleaned = []
        for item in items:
            normalized = self._normalize_address(item)
            if normalized and normalized not in cleaned:
                cleaned.append(normalized)
        return cleaned

    def _header(self, *keys):
        """Return the first populated value from the parsed mail headers."""
        header_dict = getattr(self.msg, "header_dict", None) or {}
        for key in keys:
            if key in header_dict and header_dict[key]:
                return header_dict[key]
        return None

    @staticmethod
    def _stringify_date(value):
        if not value:
            return None
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _attachment_metadata(self):
        attachments = getattr(self.msg, "attachments", None) or []
        metadata = []
        for attachment in attachments:
            filename = getattr(attachment, "Filename", None)
            if not filename:
                continue
            entry = {"filename": filename}
            size = getattr(attachment, "AttachmentSize", None)
            if size:
                entry["size"] = size
            mime = getattr(attachment, "AttachMimeTag", None)
            if mime:
                entry["mime_type"] = mime
            metadata.append(entry)
        return metadata

    def build_frontmatter(self):
        """Build an ordered mapping of header fields for the YAML frontmatter."""
        frontmatter = {}

        subject = getattr(self.msg, "subject", None)
        if subject:
            frontmatter["subject"] = str(subject)

        sender = self._address_list(self._header("From") or getattr(self.msg, "sender", None))
        if sender:
            frontmatter["from"] = sender[0] if len(sender) == 1 else sender

        to = self._address_list(self._header("To", "TO") or getattr(self.msg, "to", None))
        if to:
            frontmatter["to"] = to

        cc = self._address_list(self._header("CC", "Cc") or getattr(self.msg, "cc", None))
        if cc:
            frontmatter["cc"] = cc

        bcc = self._address_list(self._header("BCC", "Bcc") or getattr(self.msg, "bcc", None))
        if bcc:
            frontmatter["bcc"] = bcc

        reply_to = self._address_list(
            self._header("Reply-To") or getattr(self.msg, "reply_to", None)
        )
        if reply_to:
            frontmatter["reply_to"] = reply_to[0] if len(reply_to) == 1 else reply_to

        date = self._stringify_date(getattr(self.msg, "sent_date", None))
        if date:
            frontmatter["date"] = date

        received = self._stringify_date(getattr(self.msg, "received_date", None))
        if received:
            frontmatter["received"] = received

        message_id = getattr(self.msg, "message_id", None)
        if message_id:
            frontmatter["message_id"] = str(message_id)

        attachments = self._attachment_metadata()
        if attachments:
            frontmatter["attachments"] = attachments

        return frontmatter

    def _raw_body(self):
        """Return ``(content, is_html)`` preferring the plain-text body."""
        properties = getattr(getattr(self.msg, "_message", None), "properties", {}) or {}

        plain = properties.get("Body")
        if isinstance(plain, bytes):
            plain = plain.decode("utf-8", "ignore")
        if plain and plain.strip():
            return plain, False

        html = properties.get("Html")
        if isinstance(html, bytes):
            html = html.decode("utf-8", "ignore")
        if html and html.strip():
            return html, True

        body = getattr(self.msg, "body", None)
        if isinstance(body, bytes):
            body = body.decode("utf-8", "ignore")
        if body:
            return body, bool(_HTML_MARKER.search(body))

        return "", False

    @staticmethod
    def _html_to_markdown(html):
        """Convert an HTML body to Markdown.

        Uses ``markdownify`` when available (install the ``html`` extra) and
        falls back to a lightweight tag-stripping conversion otherwise.
        """
        try:
            from markdownify import markdownify as _markdownify
        except ImportError:
            _markdownify = None

        if _markdownify is not None:
            return _markdownify(html, heading_style="ATX").strip()

        text = re.sub(r"(?is)<(script|style).*?</\1>", "", html)
        text = re.sub(r"(?i)<br\s*/?>", "\n", text)
        text = re.sub(r"(?i)</(p|div|h[1-6]|li|tr)>", "\n", text)
        text = re.sub(r"(?s)<[^>]+>", "", text)
        text = html_module.unescape(text)
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def extract_body(self):
        """Return the mail body rendered as Markdown text."""
        content, is_html = self._raw_body()
        if not content:
            return ""
        if is_html:
            return self._html_to_markdown(content)
        return content.replace("\r\n", "\n").replace("\r", "\n").strip()

    def to_markdown(self):
        """Render the message as a Markdown string with YAML frontmatter."""
        frontmatter = self.build_frontmatter()
        yaml_block = yaml.safe_dump(
            frontmatter,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
        ).strip()

        body = self.extract_body()
        return "---\n{frontmatter}\n---\n\n{body}\n".format(
            frontmatter=yaml_block, body=body
        )


def convert_msg_to_markdown(msg_path):
    """Parse ``msg_path`` and return the Markdown representation as a string."""
    message = MsOxMessage(msg_path)
    return MarkdownConverter(message).to_markdown()


def _markdown_output_path(msg_path, output):
    """Resolve the destination ``.md`` path for a given ``.msg`` file."""
    base = os.path.splitext(os.path.basename(msg_path))[0] + MARKDOWN_EXTENSION
    if output is None:
        return os.path.join(os.path.dirname(os.path.abspath(msg_path)), base)
    if os.path.isdir(output) or output.endswith(os.sep):
        return os.path.join(output, base)
    return output


def save_markdown_file(msg_path, output=None):
    """Convert a single ``.msg`` file and write the Markdown to disk.

    :param msg_path: path to the source ``.msg`` file.
    :param output: target ``.md`` file path or an output directory. When
        ``None`` the Markdown file is written next to the source file.
    :return: the path of the written Markdown file.
    """
    markdown = convert_msg_to_markdown(msg_path)
    destination = _markdown_output_path(msg_path, output)

    parent = os.path.dirname(os.path.abspath(destination))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)

    with open(destination, "w", encoding="utf-8") as md_file:
        md_file.write(markdown)
    return destination


def _iter_msg_files(directory, recursive=False):
    if recursive:
        for root, _dirs, files in os.walk(directory):
            for name in sorted(files):
                if name.lower().endswith(MSG_EXTENSION):
                    yield os.path.join(root, name)
    else:
        for name in sorted(os.listdir(directory)):
            full = os.path.join(directory, name)
            if os.path.isfile(full) and name.lower().endswith(MSG_EXTENSION):
                yield full


def convert_directory(input_dir, output_dir=None, recursive=False):
    """Convert every ``.msg`` file in ``input_dir`` to a Markdown file.

    :param input_dir: directory containing ``.msg`` files.
    :param output_dir: directory to write the ``.md`` files to. When ``None``
        each Markdown file is written next to its source ``.msg`` file.
    :param recursive: also descend into sub-directories when ``True``.
    :return: list of written Markdown file paths.
    """
    if not os.path.isdir(input_dir):
        raise NotADirectoryError("{0} is not a directory".format(input_dir))

    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)

    written = []
    for msg_path in _iter_msg_files(input_dir, recursive=recursive):
        written.append(save_markdown_file(msg_path, output_dir))
    return written


def convert(input_path, output=None, recursive=False):
    """Convert a ``.msg`` file or a directory of ``.msg`` files to Markdown.

    Dispatches to :func:`save_markdown_file` or :func:`convert_directory`
    depending on whether ``input_path`` is a file or a directory.

    :return: list of written Markdown file paths.
    """
    if os.path.isdir(input_path):
        return convert_directory(input_path, output, recursive=recursive)
    return [save_markdown_file(input_path, output)]
