import re


def regex_ciatation(text: str):
    """
    Extract file citations from text using optimized match-case pattern.

    Args:
        text (str): Input text to search for citations

    Returns:
        tuple: (bool, str) - (found, filename_or_original_text)
    """
    # Combined regex with named groups for optimal performance
    combined_pattern = r"(?::(?P<colon>[0-9a-fA-F]+\.txt)】)|(?:【\d+:\d+†(?P<bracket>[0-9a-f]{24}\.txt))"

    if match_obj := re.search(combined_pattern, text):
        # Use match-case with the matched groups
        match match_obj.groupdict():
            case {"colon": filename} if filename is not None:
                return True, filename
            case {"bracket": filename} if filename is not None:
                return True, filename
            case _:
                return False, text

    return False, text
