import os
import httpx
import base64
from strands import tool

atlasian_api_token = os.getenv('ATLASSIAN_API_TOKEN')
atlasian_email = os.getenv('ATLASSIAN_EMAIL')
jira_base_url = os.getenv('JIRA_BASE_URL')
board_id = int(os.getenv('JIRA_BOARD_ID'))
project_key = os.getenv('JIRA_PROJECT_KEY')

@tool(
    name="create_jira_story",
    description=(
        "Creates a Jira Story in the specified project and adds it to the current active sprint of the board. "
        "Returns the issue key."
    )
)
def create_jira_story(summary: str, description: str) -> str:
    """
    Args:
        summary (str): The summary/title of the Jira Story.
        description (str): Description of the story.

    Returns:
        str: The Jira issue key of the created story (e.g., 'PROJ-123').

    Raises:
        httpx.HTTPStatusError: For API request failures with details.
    """

    try:
        # Load credentials and Jira configuration from environment
        if not all([atlasian_email, atlasian_api_token, jira_base_url, board_id, project_key]):
            raise ValueError(
                "Missing Jira configuration in environment variables. "
                "Required: ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN, JIRA_BASE_URL, JIRA_BOARD_ID, JIRA_PROJECT_KEY"
            )

        # Prepare authentication header
        auth_string = f"{atlasian_email}:{atlasian_api_token}"
        auth_token = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # Step 1: Get current active sprint
        sprints_url = f"{jira_base_url}/rest/agile/1.0/board/{board_id}/sprint?state=active"
        resp = httpx.get(sprints_url, headers=headers, timeout=30)
        resp.raise_for_status()
        sprints = resp.json().get("values", [])
        if not sprints:
            raise ValueError(f"No active sprint found for board ID {board_id}")
        current_sprint_id = sprints[0]["id"]

        # Step 2: Prepare issue payload (ADF format for description)
        issue_payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "issuetype": {"name": "Story"},
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": description or ""}
                            ]
                        }
                    ]
                }
            }
        }

        # Step 3: Create Jira Story
        create_url = f"{jira_base_url}/rest/api/3/issue"
        create_resp = httpx.post(create_url, headers=headers, json=issue_payload, timeout=30)
        create_resp.raise_for_status()
        issue_key = create_resp.json()["key"]

        # Step 4: Add story to active sprint
        add_sprint_url = f"{jira_base_url}/rest/agile/1.0/sprint/{current_sprint_id}/issue"
        add_sprint_payload = {"issues": [issue_key]}
        add_sprint_resp = httpx.post(add_sprint_url, headers=headers, json=add_sprint_payload, timeout=30)
        add_sprint_resp.raise_for_status()

        return issue_key
    except Exception as e:
        print(f"Error creating Jira story: {str(e)}")
        raise e

if __name__ == "__main__":
    create_jira_story("This story has been created by Nemo AI Voice Planner", "This is a test story.")