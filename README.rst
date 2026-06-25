msg_parser
==========

.. image:: https://img.shields.io/pypi/v/msg_parser.svg
        :target: https://pypi.python.org/pypi/msg_parser

.. image:: https://img.shields.io/travis/vikramarsid/msg_parser.svg
        :target: https://travis-ci.org/vikramarsid/msg_parser

.. image:: https://readthedocs.org/projects/msg-parser/badge/?version=latest
        :target: https://msg-parser.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/vikramarsid/msg_parser/shield.svg
     :target: https://pyup.io/repos/github/vikramarsid/msg_parser/
     :alt: Updates

Python module for parsing outlook msg files.


* Free software: BSD license
* Documentation: https://msg-parser.readthedocs.io.


Features
--------

* Parse MSG file.
* Convert MSG file to EML file.
* Convert a MSG file (or a whole folder of MSG files) to Markdown with the
  mail headers rendered as YAML frontmatter.
* Output MSG file as JSON string.
* Handles nested MSG/EML attachments.
* Works 100% on Linux machines, do not require any windows libraries.

Installation
------------

* Basic installation

  .. code-block:: bash

 	 pip install msg_parser

* With RTF decompression

  .. code-block:: bash

 	 pip install msg_parser[rtf]

* With high quality HTML-to-Markdown conversion

  .. code-block:: bash

 	 pip install msg_parser[html]


Usage
-----

* Run CLI command

   .. code-block:: bash

       $ msg_parser --help
         usage: msg_parser [-h] -i PATH [-j] [-e EML] [-m] [-o OUTPUT] [-r]

        Microsoft Message Parser

        options:
            -h, --help            show this help message and exit
            -i PATH, --input PATH
                                  path to a .msg file (or a directory of .msg
                                  files for markdown output)
            -j, --json            output parsed msg as json to console
            -e EML, --eml EML     provide a directory path to save the message
                                  as an eml file.
            -m, --markdown        convert the message(s) to Markdown with YAML
                                  frontmatter
            -o OUTPUT, --output OUTPUT
                                  output .md file or directory for --markdown
                                  (defaults next to the source)
            -r, --recursive       recurse into sub-directories when the input is
                                  a directory

* Convert a single MSG file to Markdown

   .. code-block:: bash

       $ msg_parser -i message.msg -m -o message.md

* Convert a whole folder of MSG files to Markdown

   .. code-block:: bash

       $ msg_parser -i ./inbox -m -o ./markdown --recursive


 * Import in python modules

   .. code-block:: python

        from msg_parser import MsOxMessage

        msg_obj = MsOxMessage(msg_file_path)

        json_string = msg_obj.get_message_as_json()

        msg_properties_dict = msg_obj.get_properties()

        saved_path = msg_obj.save_email_file(output_eml_file_path)

        # Markdown with YAML frontmatter
        markdown_string = msg_obj.get_message_as_markdown()

        saved_md = msg_obj.save_markdown_file(output_directory)

 * Convert files or folders to Markdown directly

   .. code-block:: python

        from msg_parser import convert_to_markdown, convert_msg_to_markdown

        # single file -> markdown string
        markdown_string = convert_msg_to_markdown("message.msg")

        # file or directory -> written .md files
        written_paths = convert_to_markdown("./inbox", "./markdown", recursive=True)

