import os
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from ..config.config_loader import get_config

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
    
    slack_config = get_config().get_section('slack')

    if not prompt:
        say(slack_config['no_prompt_error'])
        return

    try:
        initial_msg_response = client.chat_postMessage(
            channel=user_id,
            text=slack_config['initial_response'].format(prompt=prompt)
        )
        logger.info(f"Received task from Slack user {user_id}: {prompt}")
        
    except Exception as e:
        logger.error(f"Error handling Slack command: {e}")
        say(slack_config['error_response'])