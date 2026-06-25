=======
History
=======

0.1.0 (2018-10-26)
------------------

* Initial commit.


1.0.0 (2018-10-29)
------------------
* Initial pypi release.
* Added headers_dict to message object.

1.2.0 (2019-12-12)
------------------
* Python 3.x support
* Updates to Makefile
* Formatting and linting

1.3.0 (2026-06-25)
------------------
* New feature: convert a ``.msg`` file or a whole folder of ``.msg`` files to
  Markdown with the mail headers rendered as YAML frontmatter
  (``MsOxMessage.get_message_as_markdown``, ``MsOxMessage.save_markdown_file``,
  ``convert_to_markdown`` and the ``--markdown`` CLI option).
* Optional ``html`` extra for high quality HTML-to-Markdown body conversion via
  ``markdownify`` (with a dependency-free fallback).
* Modernised supported Python versions (3.9 - 3.13) and refreshed dependencies.
* Switched CI to a GitHub Actions matrix and added a ``pyproject.toml`` build
  configuration.

