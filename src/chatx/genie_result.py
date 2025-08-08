from dataclasses import dataclass
import logging

from databricks.sdk.service.sql import StatementResponse, ColumnInfoTypeName
from databricks.sdk.service.dashboards import GenieResultMetadata
from botbuilder.schema import Activity, ActivityTypes

from chatx.adaptive_card import AdaptiveCardFactory

# Log
logger = logging.getLogger(__name__)


@dataclass
class GenieResult:
    query_description: str | None = None
    query: str | None = None
    query_result_metadata: GenieResultMetadata | None = None
    statement_id: str | None = None
    statement_response: StatementResponse | None = None
    message: str | None = None
    conversation_id: str | None = None

    def process_query_results(self) -> Activity:
        """
        Processes the result from a Genie query and formats it into an Activity object.

        This function takes a GenieResult object, extracts relevant information such as
        query description, metadata, and query results, and formats it into a message
        activity. If the query result contains tabular data, it generates an adaptive
        card with a table representation of the data.

        :returns: An Activity object containing the formatted response or an error message.
        :rtype: Activity

        :raises: Logs errors if required fields (e.g., result or data_array) are missing
                in the GenieResult object.
        """
        response = ""

        if self.query_description:
            response += f"{self.query_description}\n\n"

        if self.query_result_metadata:
            metadata = self.query_result_metadata
            if metadata.row_count:
                response += f"**Row Count:** {metadata.row_count}\n\n"

        if self.statement_response:
            statement_response = self.statement_response
            logger.info(f"Found statement_response: {statement_response}")

            if statement_response.result and statement_response.result.data_array:
                manifest = statement_response.manifest
                columns = []

                if manifest and manifest.schema and manifest.schema.columns:
                    columns = manifest.schema.columns
                    logger.info(f"Schema columns: {columns}")
                else:
                    logger.warning("No manifest found in statement_response.")

                col_output = [{"width": 3} for _ in columns]

                data_array = statement_response.result.data_array
                logger.info(f"Data array: {data_array}")

                row_output = [
                    {
                        "type": "TableRow",
                        "cells": [
                            AdaptiveCardFactory.get_cell(col.name) for col in columns
                        ],
                    }
                ]

                for row in data_array:
                    cell_output = []
                    for value, col in zip(row, columns):
                        if value is None:
                            formatted_value = "NULL"
                        elif col.type_name in [
                            ColumnInfoTypeName.DECIMAL,
                            ColumnInfoTypeName.DOUBLE,
                            ColumnInfoTypeName.FLOAT,
                        ]:
                            formatted_value = f"{float(value):,.2f}"
                        elif col.type_name in [
                            ColumnInfoTypeName.INT,
                            ColumnInfoTypeName.LONG,
                            ColumnInfoTypeName.SHORT,
                        ]:
                            formatted_value = f"{int(value):,}"
                        else:
                            formatted_value = str(value)
                        cell_output.append(
                            AdaptiveCardFactory.get_cell(formatted_value)
                        )
                    row_output.append({"type": "TableRow", "cells": cell_output})
                return AdaptiveCardFactory.get_table_card(
                    response, col_output, row_output, self.query or "No query provided"
                )
            else:
                logger.error(
                    f"Missing result or data_array in statement_response: {statement_response}"
                )
        elif self.message:
            response += f"{self.message}\n\n"
            return Activity(
                text=response,
                type=ActivityTypes.message,
            )
        else:
            response += "No data available.\n\n"
            logger.error("No statement_response or message found in answer_json")

        return Activity(text=response, type=ActivityTypes.message)
