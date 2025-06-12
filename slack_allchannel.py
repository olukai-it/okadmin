#!/usr/bin/env python3

import os
from datetime import datetime
from typing import Any, Dict, Generator, List

from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

def join_channel_if_needed(
    client: WebClient, channel_id: str, channel_name: str, is_private: bool
) -> str:
    """Join a public channel if the bot is not already a member."""

    if is_private:
        return f"Cannot automatically join private channel: {channel_name}"

    try:
        response = client.conversations_join(channel=channel_id)
        if response.get("ok"):
            print(f"Successfully joined channel: {channel_name}")
            return "Joined successfully"
    except SlackApiError as e:
        error = e.response.get("error", "unknown_error")
        if error == "already_in_channel":
            return "Already a member"
        return f"Error joining channel: {error}"

    return "Failed to join"

def get_last_message_date(client: WebClient, channel_id: str) -> str:
    """Return the timestamp of the latest message in the given channel."""

    try:
        response = client.conversations_history(channel=channel_id, limit=1)
    except SlackApiError as e:
        return f"Unable to fetch messages: {e.response['error']}"

    if response.get("messages"):
        ts = float(response["messages"][0]["ts"])
        last_message_date = datetime.fromtimestamp(ts)
        return last_message_date.strftime("%Y-%m-%d %H:%M:%S")

    return "No messages"

def iter_channels(client: WebClient) -> Generator[Dict[str, Any], None, None]:
    """Yield all channels the bot has access to."""

    cursor: str | None = None
    while True:
        try:
            response = client.conversations_list(
                types="public_channel,private_channel",
                limit=1000,
                cursor=cursor,
            )
        except SlackApiError as e:
            print(f"Error fetching channels: {e.response['error']}")
            return

        for channel in response["channels"]:
            yield channel

        cursor = response["response_metadata"].get("next_cursor")
        if not cursor:
            break


def main() -> List[Dict[str, Any]]:
    """Load environment, fetch all channels and print details."""

    load_dotenv()

    slack_token = os.getenv("SLACK_TOKEN")
    if not slack_token:
        raise ValueError("SLACK_TOKEN not found in environment variables")

    client = WebClient(token=slack_token)

    all_channels: List[Dict[str, Any]] = list(iter_channels(client))

    print(f"Found {len(all_channels)} channels:")
    for channel in all_channels:
        last_message_date = get_last_message_date(client, channel["id"])
        join_status = join_channel_if_needed(
            client, channel["id"], channel["name"], channel.get("is_private", False)
        )

        print(f"Channel Name: {channel['name']}")
        print(f"Channel ID: {channel['id']}")
        print(f"Is Private: {channel.get('is_private', False)}")
        print(f"Member Count: {channel.get('num_members', 0)}")
        print(f"Last Message Date: {last_message_date}")
        print(f"Join Status: {join_status}")
        print("-" * 50)

    return all_channels

if __name__ == "__main__":
    main()
