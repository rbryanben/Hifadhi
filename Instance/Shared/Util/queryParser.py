"""
    Extracts the instance name, filename and signature if any from a given request
"""
def parse(queryString):
    tokens = queryString.split("@")
    return tokens[0], tokens[1]