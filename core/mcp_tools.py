import os
import asyncio
import ast
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json
from concurrent.futures import ThreadPoolExecutor

def get_google_service(token_json, service_name, version):
    """Builds a Google API service using the OAuth token from the session."""
    
    try:
        creds_data= json.loads(token_json)
        creds = Credentials.from_authorized_user_info(creds_data)

        return build(service_name, version, credentials=creds)
    except Exception as e:
        print(f"Error building {service_name} service: {e}")
        return None

def get_or_create_folder(drive_service):
    """Checks for 'Company Lens' folder in root; creates it if missing."""

    query = (
        "name = 'Company Lens' and "
        "'root' in parents and "
        "mimeType = 'application/vnd.google-apps.folder' and "
        "trashed = false"
    )
    
    results = drive_service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id']
    else:
        
        folder_metadata = {
            'name': 'Company Lens',
            'mimeType': 'application/vnd.google-apps.folder'
        }

        folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')
    
async def create_interview_note(token_json, company_name, summary_text):
    """ Creates a Google Doc with interview summary in a specific folder and returns the link."""
    
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=3)
    
    try:
        docs_service = get_google_service(token_json, 'docs', 'v1')
        drive_service = get_google_service(token_json, 'drive', 'v3')
        
        if not docs_service or not drive_service:
            return "Error: Could not authenticate with Google Services"

        # Run blocking Google API calls on thread executor
        folder_id = await loop.run_in_executor(executor, get_or_create_folder, drive_service)
        
        doc_metadata = {
            'name': f"Interview Prep: {company_name}",
            'mimeType': 'application/vnd.google-apps.document',
            'parents': [folder_id]
        }
        
        doc_file = await loop.run_in_executor(
            executor,
            lambda: drive_service.files().create(body=doc_metadata, fields='id').execute()
        )
        doc_id = doc_file.get('id')

        # Parse summary data
        data_dict = {}
        if isinstance(summary_text, str):
            try:
                data_dict = ast.literal_eval(summary_text)
            except Exception as e:
                print(f"Parse error: {e}")
                data_dict = {"Agent Insights-": {"data": summary_text}}
        elif isinstance(summary_text, dict):
            data_dict = summary_text

        # Build formatting requests
        requests = []
        header_text = f"Interview Prep Notes: {company_name}\n"
        separator = "-" * 123 + "\n\n"
        
        requests.append({'insertText': {'location': {'index': 1}, 'text': header_text + separator}})
        requests.append({
            'updateParagraphStyle': {
                'range': {'startIndex': 1, 'endIndex': len(header_text)},
                'paragraphStyle': {'namedStyleType': 'HEADING_1'},
                'fields': 'namedStyleType'
            }
        })

        current_index = 1 + len(header_text) + len(separator)
        
        for agent_name, agent_content in data_dict.items():
            section_title = agent_name.replace('_', ' ').title() + "\n"
        
            if isinstance(agent_content, dict):
                body_text = agent_content.get('data', str(agent_content))
            else:
                body_text = str(agent_content)

            body_text = body_text.replace('\\n', '\n') + "\n\n"

            # Insert Section Title
            requests.append({'insertText': {'location': {'index': current_index}, 'text': section_title}})
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index, 'endIndex': current_index + len(section_title)},
                    'textStyle': {'bold': True, 'fontSize': {'magnitude': 14, 'unit': 'PT'}},
                    'fields': 'bold,fontSize'
                }
            })
            current_index += len(section_title)

            # Insert Body Text
            requests.append({'insertText': {'location': {'index': current_index}, 'text': body_text}})
            requests.append({
                'updateTextStyle': {
                    'range': {'startIndex': current_index, 'endIndex': current_index + len(body_text)},
                    'textStyle': {'bold': False, 'fontSize': {'magnitude': 11, 'unit': 'PT'}},
                    'fields': 'bold,fontSize'
                }
            })
            current_index += len(body_text)

        # Run batchUpdate on thread executor
        await loop.run_in_executor(
            executor,
            lambda: docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
        )

        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        return {"status": "success", "url": doc_url}
    
    except Exception as e:
        print(f"Error creating note: {e}", flush= True)
        return {"status": "error", "message": f"Note Creation Error: {str(e)}"}
    finally:
        executor.shutdown(wait=False)

