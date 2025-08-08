import asyncio
import logging

from databricks.sdk import GenieAPI, WorkspaceClient, errors

from chatx.const import DATABRICKS_HOST, DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET, TOKEN_EXPIRED_MESSAGE
from chatx.genie_result import GenieResult

# Log
logger = logging.getLogger(__name__)


class GenieQuerier:
    genie_api: GenieAPI | None
    auth_method: str | None

    def __init__(self, token: str | None = None):
        # If token is provided, use it to authenticate
        if token is not None:
            workspace_client = WorkspaceClient(host=DATABRICKS_HOST, token=token)
            self.genie_api = GenieAPI(workspace_client.api_client)
            self.auth_method = "oauth"
        elif DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET:
            # Try Service Principal Secrets
            workspace_client = WorkspaceClient(
                host=DATABRICKS_HOST,
                client_id=DATABRICKS_CLIENT_ID,
                client_secret=DATABRICKS_CLIENT_SECRET,
            )
            self.genie_api = GenieAPI(workspace_client.api_client)
            self.auth_method = "service_principal"
        else:
            self.genie_api = None
            self.auth_method = None

    async def ask_genie(
        self, question: str, space_id: str, conversation_id: str | None
    ) -> GenieResult:
        """
        Asynchronously sends a question to the Genie API and waits for a response.
        This function handles both new conversations and adding messages to existing conversations.
        It processes message attachments and query results, converting them into a structured response.
        Args:
            question (str): The question or message to send to the Genie API.
            space_id (str): The identifier for the Genie Space.
            conversation_id (str | None): The ID of an existing conversation to continue,
                                         or None to start a new conversation.
        Returns:
            GenieResult: An object containing the response data, which may include:
                - message: Text response content
                - query_description: Description of any executed query
                - query_result_metadata: Metadata about query results
                - statement_id: ID of the executed statement
                - statement_response: Full response from executed statements
                - conversation_id: ID of the conversation
        Raises:
            Exception: Any errors during API communication or response processing are caught,
                       logged, and returned as an error message in the result.
        """
        try:
            loop = asyncio.get_running_loop()
            if conversation_id is None:
                initial_message = await loop.run_in_executor(
                    None, self.genie_api.start_conversation_and_wait, space_id, question
                )
                conversation_id = initial_message.conversation_id
            else:
                initial_message = await loop.run_in_executor(
                    None,
                    self.genie_api.create_message_and_wait,
                    space_id,
                    conversation_id,
                    question,
                )

            message_content = await loop.run_in_executor(
                None,
                self.genie_api.get_message,
                space_id,
                initial_message.conversation_id,
                initial_message.message_id,
            )
            logger.info(f"Raw message content: {message_content}")

            if not message_content.attachments:
                return GenieResult(
                    message=message_content.content,
                    conversation_id=conversation_id,
                )

            for attachment in message_content.attachments:
                attachment_id = attachment.attachment_id
                query_obj = attachment.query

                if not attachment_id or not query_obj:
                    text_obj = attachment.text
                    message = text_obj.content if text_obj else ""
                    return GenieResult(message=message, conversation_id=conversation_id)

                # Use the new endpoint to get query results
                query_result = await loop.run_in_executor(
                    None,
                    self.genie_api.get_message_query_result_by_attachment,
                    space_id,
                    initial_message.conversation_id,
                    initial_message.message_id,
                    attachment_id,
                )

                logger.info(f"Raw query result: {query_result}")

                response_data = GenieResult(
                    query_description=query_obj.description,
                    query_result_metadata=query_obj.query_result_metadata,
                    query=query_obj.query,
                    statement_id=query_obj.statement_id,
                    conversation_id=conversation_id,
                    statement_response=query_result.statement_response,
                )

                if not response_data.statement_response:
                    logger.error(
                        f"Missing statement_response in query_result: {query_result}"
                    )

                return response_data

            return GenieResult(
                message="No attachment found", conversation_id=conversation_id
            )

        except errors.platform.PermissionDenied as e:
            return GenieResult(
                message=TOKEN_EXPIRED_MESSAGE,
                conversation_id=conversation_id,
            )

        except Exception as e:
            logger.error(
                f"Error in ask_genie: {str(e)} | space_id: {space_id}, conversation_id: {conversation_id}"
            )
            return GenieResult(
                message="An error occurred while processing your request.",
                conversation_id=conversation_id,
            )
