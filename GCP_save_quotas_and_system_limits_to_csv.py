# # install billing_v1
# !pip install google-cloud-billing -q
# !pip install google-api-python-client pandas -q

from google.oauth2 import service_account
from googleapiclient import discovery
import pandas as pd

# Path to your service account JSON key file
SERVICE_ACCOUNT_FILE = '/path/to/service/account/json/file'

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/cloud-platform']

# Authenticate and initialize credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Function to initialize a GCP service using the service account credentials
def get_service(api_name, api_version):
    return discovery.build(api_name, api_version, credentials=credentials)

# Rest of the code from before
def get_compute_engine_quotas(project_id):
    service = get_service('compute', 'v1')
    request = service.projects().get(project=project_id)
    response = request.execute()
    return response.get('quotas', [])

def get_project_info(project_id):
    service = get_service('cloudresourcemanager', 'v1')
    request = service.projects().get(projectId=project_id)
    response = request.execute()
    return {
        'project_id': response['projectId'],
        'project_name': response['name']
    }

def list_projects():
    service = get_service('cloudresourcemanager', 'v1')
    request = service.projects().list()
    projects = []
    while request is not None:
        response = request.execute()
        projects += response.get('projects', [])
        request = service.projects().list_next(request, response)
    return projects

def save_quotas_to_csv(projects):
    all_quotas = []
    for project in projects:
        project_info = get_project_info(project['projectId'])
        quotas = get_compute_engine_quotas(project['projectId'])
        for quota in quotas:
            all_quotas.append({
                'Project ID': project_info['project_id'],
                'Project Name': project_info['project_name'],
                'Metric': quota['metric'],
                'Limit': quota['limit'],
                'Usage': quota['usage']
            })
    df = pd.DataFrame(all_quotas)
    df.to_csv('gcp_project_quotas.csv', index=False)
    print('Saved quotas to gcp_project_quotas.csv')

# Main execution
if __name__ == '__main__':
    projects = list_projects()
    save_quotas_to_csv(projects)