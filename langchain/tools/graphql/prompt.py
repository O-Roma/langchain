# flake8: noqa
QUERY_CHECKER = """
{query}
Double check the GraphQL query above for common mistakes, including:
- Properly structuring query and mutation requests
- Correct use of variables and their types
- Ensuring fields and nested fields are properly used
- Use of arguments with fields where necessary
- Correct use of aliases if used
- Correct use of fragments, inline fragments and directives
- Ensuring operation names are unique where used
- Proper handling of error states and null values

If there are any of the above mistakes, rewrite the query. If there are no mistakes, just reproduce the original query.
"""
