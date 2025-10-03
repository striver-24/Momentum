import os
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

slack_app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

app_handler = SlackRequestHandler(slack_app)

@slack_app.command("/momentum")
def handle_momentum_command(ack, body, say, client, logger):
    ack()
    
    user_id = body['user_id']
    prompt = body.get('text', '').strip()

    if not prompt:
        say("Please provide a task description after the command. \nFor example: `/momentum Create a new API endpoint to fetch user profiles.`")
        return

    try:
        initial_msg_response = client.chat_postMessage(
            channel=user_id,
            text=f"🚀 Got it! Starting work on your request: *'{prompt}'*\n\nI'll keep you updated with a link to the live progress view shortly."
        )
        logger.info(f"Received task from Slack user {user_id}: {prompt}")
        
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}")
        say("Sorry, there was an error starting the agent.")