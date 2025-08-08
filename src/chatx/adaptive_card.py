import logging

import sqlparse
from botbuilder.core import CardFactory
from botbuilder.schema import Attachment, ActivityTypes, Activity

from chatx.const import WAITING_MESSAGE

# Log
logger = logging.getLogger(__name__)


class AdaptiveCardFactory:
    @staticmethod
    def get_activity(attachments: list[Attachment] | None) -> Activity:
        return Activity(type=ActivityTypes.message, attachments=attachments)

    @staticmethod
    def get_waiting_message() -> Activity:
        attachment = CardFactory.adaptive_card(
            {
                "type": "AdaptiveCard",
                "version": "1.5",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Processing your request",
                        "wrap": True,
                        "size": "Large",
                        "weight": "Bolder",
                    },
                    {"type": "ProgressBar"},
                    {
                        "type": "TextBlock",
                        "text": WAITING_MESSAGE,
                        "spacing": "ExtraSmall",
                        "size": "Small",
                    },
                ],
            }
        )
        return AdaptiveCardFactory.get_activity([attachment])

    @staticmethod
    def get_cell(text: str = "") -> dict:
        """
        Returns a cell object for use in adaptive cards.
        """
        return {
            "type": "TableCell",
            "items": [
                {
                    "type": "TextBlock",
                    "text": text,
                    "wrap": True,
                }
            ],
        }

    @staticmethod
    def get_table_card(
        response: str,
        col_output: list[dict[str, int]],
        row_output: list[dict[str, any]],
        query: str,
    ) -> Activity:
        """
        Returns an adaptive card template for displaying query results.
        """
        attachment = CardFactory.adaptive_card(
            {
                "type": "AdaptiveCard",
                "version": "1.5",
                "body": [
                    {
                        "type": "TextBlock",
                        "text": "Results",
                        "wrap": True,
                        "size": "Large",
                        "weight": "Bolder",
                    },
                    {
                        "type": "Container",
                        "layouts": [
                            {"type": "Layout.Flow", "horizontalItemsAlignment": "left"}
                        ],
                        "items": [
                            {"type": "Icon", "name": "TableLightning", "size": "Small"},
                            {"type": "TextBlock", "text": response, "wrap": True},
                        ],
                    },
                    {
                        "type": "Table",
                        "roundedCorners": True,
                        "firstRowAsHeaders": True,
                        "columns": col_output,
                        "rows": row_output,
                    },
                ],
                "actions": [
                    {
                        "type": "Action.ShowCard",
                        "title": "Show/hide SQL query",
                        "card": {
                            "type": "AdaptiveCard",
                            "body": [
                                {
                                    "type": "CodeBlock",
                                    "codeSnippet": sqlparse.format(
                                        query, reindent=True, keyword_case="upper"
                                    ),
                                    "language": "Sql",
                                }
                            ],
                        },
                    }
                ],
            }
        )

        return AdaptiveCardFactory.get_activity([attachment])
