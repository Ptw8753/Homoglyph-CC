# Regex preprocessing for encoding and decoding. Scans for protected indices to maintain links and email addresses

import re

# returns a set of indices that should be excluded from the final message's encoding and decoding
def get_protected_indices(filepath_in, whitespace_chars):
    whitespace = re.escape("".join(whitespace_chars))

    protected_regex = (
        rf"(?<![^{whitespace}])"
        rf"(?=[^{whitespace}]*[a-zA-Z0-9][.@][a-zA-Z0-9][^{whitespace}]*"
        rf"(?![^{whitespace}]))"
        rf"[^{whitespace}]+"
    )

    indices = set()
    with open(filepath_in, "r", encoding='utf_8') as f:
        text = f.read()
        for match in re.finditer(protected_regex, text):
            for i in range(match.start(), match.end()):
                indices.add(i)

    return indices
