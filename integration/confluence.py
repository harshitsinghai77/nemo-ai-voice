import os
import re
import base64

from strands import tool
import httpx
import markdownify

CONFLUENCE_URL_PATTERN = r'https://[a-zA-Z0-9\-_.]+\.atlassian\.net/wiki/[^\s]+'

atlasian_api_token = os.getenv('ATLASSIAN_API_TOKEN')
atlasian_email = os.getenv('ATLASSIAN_EMAIL')
jira_base_url = os.getenv('JIRA_BASE_URL')

@tool(
    name="get_confluence_page",
    description="Fetch the content of a Confluence page given its URL and return it as Markdown."
)
def get_confluence_page(confluence_url: str) -> str:
    """
    Tool to fetch content from a Confluence page given its URL.
    Handles errors with detailed messages to help agents understand failures.
    For example - https://your-domain.atlassian.net/wiki/pages/123456789/Example-Page

    Args:
        confluence_url (str): The URL of the Confluence page
        
    Returns:
        Markdown content of the Confluence page as a string.
    """

    if not confluence_url or not isinstance(confluence_url, str):
        raise ValueError("Invalid confluence_url: Must be a non-empty string")
    
    try:
        if not atlasian_api_token or not atlasian_email or not jira_base_url:
            raise ValueError("Missing required Atlassian credentials in environment variables. Ignore the tool call.")
        
        match = re.search(r'/pages/(\d+)', confluence_url)
        if not match:
            raise ValueError("Cannot extract page ID from URL.")
        page_id = match.group(1)

        api_url = f"{jira_base_url}/wiki/rest/api/content/{page_id}?expand=body.storage"
        auth_string = f"{atlasian_email}:{atlasian_api_token}"
        auth_token = base64.b64encode(auth_string.encode()).decode()
        headers = {
            "Authorization": f"Basic {auth_token}",
            "Content-Type": "application/json"
        }

        response = httpx.get(api_url, headers=headers, timeout=30)
        print(f"Response status code: {response.text}")
        response.raise_for_status()
        data: dict = response.json()

        html_content = data.get('body', {}).get('storage', {}).get('value', '')
        if not html_content:
            raise Exception(
                f"No content found on the Confluence page. "
                f"The page at {confluence_url} may be empty or archived."
            )

        markdown_text = markdownify.markdownify(html_content, heading_style=markdownify.ATX)
        return markdown_text
    except Exception as e:
        print(f"Error fetching Confluence page: {str(e)}")
        raise e
        