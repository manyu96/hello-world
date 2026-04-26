"""
Runtime: start a research session and stream results.

Prerequisites (run once to set up):
  pip install anthropic

  AGENT_ID=$(ant beta:agents create < research-agent.agent.yaml --transform id -r)
  ENV_ID=$(ant beta:environments create < research-agent.environment.yaml --transform id -r)

  export AGENT_ID="agent_..."
  export ENV_ID="env_..."
"""

import os
import anthropic

AGENT_ID = os.environ["AGENT_ID"]
ENV_ID = os.environ["ENV_ID"]

client = anthropic.Anthropic()


def run_research(topic: str) -> None:
    session = client.beta.sessions.create(
        agent=AGENT_ID,
        environment_id=ENV_ID,
        title=f"Research: {topic}",
    )

    # Stream-first: open stream before sending the kickoff message
    with client.beta.sessions.stream(session_id=session.id) as stream:
        client.beta.sessions.events.send(
            session_id=session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": topic}],
                }
            ],
        )

        for event in stream:
            if event.type == "agent.message":
                for block in event.content:
                    if block.type == "text":
                        print(block.text, end="", flush=True)
            elif event.type == "session.status_terminated":
                break
            elif event.type == "session.status_idle":
                # requires_action means the session is waiting on a tool result — keep going
                if event.stop_reason.type != "requires_action":
                    break

    print()  # newline after streamed output
    client.beta.sessions.archive(session_id=session.id)


if __name__ == "__main__":
    import sys

    topic = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "latest developments in AI agents"
    run_research(topic)
