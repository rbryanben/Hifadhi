"""
    Extracts the instance name, filename and signature if any from a given request
"""
def parse(queryString):
    if "@" not in queryString:
        return queryString+"@none_$d(query string error)"
    tokens = queryString.split("@")
    return tokens[0], tokens[1]