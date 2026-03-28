# Update this config file with your values and then change its name and keep "config.py" 
# 
# Authentication for GitHub
GITHUB_TOKEN = "your token"
REPO_NAME = "your repo name"

# for Jira
JIRA_TOKEN = "your token"
JIRA_SERVER = "your server"
JIRA_EMAIL = "your email"

# for azure
AZURE_TOKEN = 'your token'
AZURE_ORG = 'your org'
AZURE_PROJECT = 'your project'
AZURE_REPO_NAME = 'your repo name'

#file configurations for extractions, you can keep the same names if you want
NAME_FILE_BUGS = 'jira_issues.csv'
NAME_FILE_COMMITS = 'azure_data.csv'
NAME_FILE_METRICS_CODE = 'metrics_code.csv'
COMMIT_PATH_FIELD = 'modified_files'
PREFIX_TOOL = 'prisme' #for example if your tool tickets are CEF-3241 in this case the prefix is CEF
SUPPORTED_EXTENSIONS = [".py", ".js", ".java", ".cpp", ".c", ".rb", ".go", ".ipynb", ".yaml", "yml", "json"] #extensions to consider for the files extractions from commits
UMBRAL = 0.8
MAX_EXPLANATIONS = 10
BUG_ID_FIELD = 'jira_ticket'
THRESHOLD_CONTRIB_LOW = 0.01 #percentage of changes done by a contributor to consider him as a minor contributor, this is useful for the feature engineering part, you can adjust it based on your data distribution
THRESHOLD_CONTRIB_HIGH = 0.08 #percentage of changes done by a contributor to consider him as a major contributor, this is useful for the feature engineering part, you can adjust it based on your data distribution

# Define what string columns you want to scale by categories
STRING_COLUMNS = ['Rapporteur', 'environment', 'severity', 'squad', 'resolution', 'Affecte la/les version(s)', 'Composants', 
                  'version corrected', 'complexity_rank']

#columns to remove after merge. here is mandatory to include: commit_id, file_name, description, comment, pull_request_number, date, 
                                                              #tool_ticket_commit, .... plus your bugs information columns that are not relevant for the model training
COLUMNS_TO_DROP = ['id', 'date', 'commit_id', 'comment', 'description', 'resume', 'jira_ticket', 'creation', 'update', 'pull_request_number', 
                'tool_ticket_commit', 'file_name']






