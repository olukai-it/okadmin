#!/usr/bin/env python3

import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv
from datetime import datetime

def join_channel_if_needed(client, channel_id, channel_name, is_private):
    try:
        if not is_private:
            # Try to join the channel if it's public
            response = client.conversations_join(channel=channel_id)
            if response['ok']:
                print(f"Successfully joined channel: {channel_name}")
        else:
            print(f"Cannot automatically join private channel: {channel_name}")
    except SlackApiError as e:
        error = e.response['error']
        if error == 'already_in_channel':
            return "Already a member"
        else:
            return f"Error joining channel: {error}"
    return "Joined successfully"

def get_last_message_date(client, channel_id):
    try:
        # Get the most recent message in the channel
        response = client.conversations_history(
            channel=channel_id,
            limit=1  # We only need the most recent message
        )
        
        if response['messages']:
            # Get timestamp of the most recent message
            timestamp = float(response['messages'][0]['ts'])
            # Convert timestamp to datetime
            last_message_date = datetime.fromtimestamp(timestamp)
            return last_message_date.strftime('%Y-%m-%d %H:%M:%S')
        return "No messages"
            
    except SlackApiError as e:
        return f"Unable to fetch messages: {e.response['error']}"

def get_all_channels():
    # Load environment variables from .env file
    load_dotenv()
    
    # Initialize the Slack client with your bot token
    slack_token = os.getenv('SLACK_TOKEN')
    if not slack_token:
        raise ValueError("SLACK_BOT_TOKEN not found in environment variables")
    
    client = WebClient(token=slack_token)
    
    try:
        # Initialize an empty list to store all channels
        all_channels = []
        
        # Get all channels (public and private) that the bot has access to
        response = client.conversations_list(
            types="public_channel,private_channel",
            limit=1000  # Adjust this number based on your needs
        )
        
        # Add channels from the first response
        all_channels.extend(response["channels"])
        
        # If there are more channels, keep fetching them
        while response['response_metadata'].get('next_cursor'):
            response = client.conversations_list(
                types="public_channel,private_channel",
                cursor=response['response_metadata']['next_cursor'],
                limit=1000
            )
            all_channels.extend(response["channels"])
        
        # Print channel information
        print(f"Found {len(all_channels)} channels:")
        for channel in all_channels:
            last_message_date = get_last_message_date(client, channel['id'])
            join_status = join_channel_if_needed(client, channel['id'], channel['name'], channel.get('is_private', False))
            
            print(f"Channel Name: {channel['name']}")
            print(f"Channel ID: {channel['id']}")
            print(f"Is Private: {channel.get('is_private', False)}")
            print(f"Member Count: {channel.get('num_members', 0)}")
            print(f"Last Message Date: {last_message_date}")
            print(f"Join Status: {join_status}")
            print("-" * 50)
        
        return all_channels
            
    except SlackApiError as e:
        print(f"Error: {e.response['error']}")
        return None

if __name__ == "__main__":
    get_all_channels()
