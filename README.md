A Django REST API for managing hierarchical organizational structures using the Nested Set model. API provides endpoints to retrieve and manipulate organizational chart data with Italian language support.

## Features

### Core Features
- **List all nodes**: Fetch all nodes in the organizational chart with pagination support
- **Get single node**: Retrieve detailed information about a specific node
- **Search children**: Find all children of a node whose names contain specific text
- **Multi-language support**: Supports English and Italian for both data and error messages
- **Nested Set Model**: Efficient hierarchical data storage and retrieval

### Additional Features
- **Pagination**: Customizable page size (0-1000) with 0-based page numbering
- **Internationalization (i18n)**: Error messages automatically adapt to requested language
- **Token Authentication**: Secure API access using token-based authentication
- **Create nodes**: Add new nodes to the organizational structure (requires authentication)

## Prerequisites

- Python 3.12
- Django 5.0
- PostgreSQL
- pip (Python package manager)

## Installation

1. Clone the repository

git clone <repository-url>
cd org_chart_api

2. Create and activate virtual environment

python -m venv venv

# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

3. Install dependencies

pip install -r requirements.txt

4. Configure database

Create a .env file in the project root with your PostgreSQL credentials:

DATABASE_NAME=org_chart_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

5. Create database

# Create the database in PostgreSQL
psql -U postgres
CREATE DATABASE org_chart_db

6. Run migrations

python manage.py migrate

7. Create a superuser (for authentication)

python manage.py createsuperuser,

8. Compile translations

python manage.py compilemessages

9. Run the development server

python manage.py runserver

The API will be available at http://localhost:8000

# API Endpoints

## Authentication

### Create a test user

python manage.py shell

from django.contrib.auth.models import User
User.objects.create_user(username='admin', password='admin')
exit()

### Login / Logout

URL: http://localhost:8000/test-auth/

# Node Operations
1. List All Nodes
URL: /api/nodes/?language={language}&page_num={page}&page_size={size}
Method: GET
Parameters:
language (required): "English" or "Italian"
page_num (optional): Page number (0-based, default: 0)
page_size (optional): Items per page (0-1000, default: 5)
Example: /api/nodes/?language=English&page_num=0&page_size=10
Response:
json
{
    "nodes": [
        {
            "node_id": 1,
            "name": "Marketing",
            "children_count": 0
        },
        {
            "node_id": 2,
            "name": "Helpdesk",
            "children_count": 0
        }
    ]
}

2. Get Single Node
URL: /api/nodes/{node_id}/?language={language}
Method: GET
Parameters:
node_id (required): The ID of the node
language (required): "English" or "Italian"
Example: /api/nodes/5/?language=Italian
Response:
json
{
    "nodes": [
        {
            "node_id": 5,
            "name": "Azienda",
            "children_count": 11
        }
    ]
}

3. Search Children
URL: /api/nodes/{node_id}/children/?language={language}&search={keyword}&page_num={page}&page_size={size}
Method: GET
Parameters:
node_id (required): Parent node ID
language (required): "English" or "Italian"
search (required): Search keyword
page_num (optional): Page number (0-based)
page_size (optional): Items per page
Example: /api/nodes/5/children/?language=English&search=Sales
Response:
json
{
    "nodes": [
        {
            "node_id": 7,
            "name": "Sales",
            "children_count": 3
        }
    ]
}

4. Create New Node (Requires Authentication)
URL: /api/nodes/create/
Method: POST
Headers: Authorization: Token your_auth_token
Body:
json
{
    "parent_id": 5,
    "names": {
        "English": "Human Resources",
        "Italian": "Risorse Umane"
    }
}
Response:
json
{
    "nodes": [
        {
            "node_id": 13,
            "name": "Human Resources",
            "children_count": 0
        }
    ],
    "message": "Node created successfully"
}

# Error Messages
The API returns standardized error messages in the requested language:

## Error    English     Italian
Missing parameters	"Missing mandatory params"	"Parametri obbligatori mancanti"
Node not found	"Not found"	"Non trovato"
Invalid page number	"Invalid page number requested"	"Numero di pagina richiesto non valido"
Invalid page size	"Invalid page size requested"	"Dimensione pagina richiesta non valida"

## Response Format
All API responses follow this structure:

json
{
    "nodes": [],      // Array of node objects
    "error": ""       // Error message (only present if error occurs)
}

# Testing

python manage.py test

## Test coverage includes:

All API endpoints (success and error cases)
Authentication functionality
Pagination
Internationalization
Node creation with nested set updates