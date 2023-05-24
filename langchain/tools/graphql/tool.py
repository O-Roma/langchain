import json
from typing import Any, Dict, Optional
from pydantic import Extra, Field, root_validator

from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain.tools.base import BaseTool
from langchain.tools.graphql.prompt import QUERY_CHECKER
from langchain.utilities.graphql import GraphQLAPIWrapper
from langchain.base_language import BaseLanguageModel
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate



NOT_IMPLEMENTED_ASYNC = "This tool does not support async"


class BaseGraphQLTool(BaseTool):
    """Base tool for querying a GraphQL API."""

    graphql_wrapper: GraphQLAPIWrapper = Field(exclude=True)

    class Config(BaseTool.Config):
        """Configuration for this pydantic object."""

        arbitrary_types_allowed = True
        extra = Extra.forbid


class QueryGraphQLTool(BaseGraphQLTool):
    """Tool for querying a GraphQL API."""

    name = "query_graphql"
    description = """\
    Input to this tool is a detailed and correct GraphQL query, output is a result from the API.
    If the query is not correct, an error message will be returned.
    If an error is returned with 'Bad request' in it, rewrite the query and try again.
    If an error is returned with 'Unauthorized' in it, do not try again, but tell the user to change their authentication.

    Example Input: query {{ allUsers {{ id, name, email }} }}\
    """  # noqa: E501

    def _run(
        self,
        tool_input: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        result = self.graphql_wrapper.run(tool_input)
        return json.dumps(result, indent=2)

    async def _arun(
        self,
        tool_input: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        """Use the Graphql tool asynchronously."""
        raise NotImplementedError("GraphQLAPIWrapper does not support async")


class ListTablesGraphQLTool(BaseGraphQLTool):
    """Tool for retrieving GraphQL type names."""

    name: str = "list_tables_graphql"
    description: str = (
        "This tool receives an empty string and returns a list of types from the GraphQL API."
    )

    def _run(self, tool_input: str = "", 
             run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Return a comma-separated list of type names from the GraphQL API."""
        return ", ".join(self.graphql_wrapper.get_type_names()) 

    async def _arun(self, tool_input: str = "", 
                    run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        raise NotImplementedError(NOT_IMPLEMENTED_ASYNC)


class SchemaGraphQLTool(BaseGraphQLTool):
    """Tool for retrieving metadata about a GraphQL API."""

    name: str = "schema_graphql"
    description: str = (
        "This tool takes a comma-separated list of type names and returns the schema for these types."
        " Ensure the types actually exist by calling 'list_tables_graphql' first."
    )

    def _run(self, type_names: str, 
             run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        """Return the schema for given types in a comma-separated list in JSON format."""
        types = [type_name.strip() for type_name in type_names.split(",")]
        return json.dumps(self.graphql_wrapper.get_type_info(types), indent=2)

    async def _arun(self, type_name: str, 
                    run_manager: Optional[AsyncCallbackManagerForToolRun] = None) -> str:
        raise NotImplementedError(NOT_IMPLEMENTED_ASYNC)


class QueryCheckerTool(BaseGraphQLTool):
    """Use an LLM to check if a query is correct for GraphQL."""

    template: str = QUERY_CHECKER
    llm: BaseLanguageModel
    llm_chain: LLMChain = Field(init=False)
    name = "query_checker_graphql"
    description = """
    Use this tool to double check if your GraphQL query is correct before executing it.
    Always use this tool before executing a query with run_graphql_query!
    """

    @root_validator(pre=True)
    def initialize_llm_chain(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if "llm_chain" not in values:
            values["llm_chain"] = LLMChain(
                llm=values.get("llm"),
                prompt=PromptTemplate(
                    template=QUERY_CHECKER, input_variables=["query"]
                ),
            )

        if values["llm_chain"].prompt.input_variables != ["query"]:
            raise ValueError(
                "LLM chain for QueryCheckerTool must have input variables ['query']"
            )

        return values

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
    ) -> str:
        """Use the LLM to check the query."""
        return self.llm_chain.predict(query=query)

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return await self.llm_chain.apredict(query=query)
