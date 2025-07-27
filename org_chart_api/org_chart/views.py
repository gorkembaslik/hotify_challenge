from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import NodeTree, NodeTreeName
from .serializers import NodeSerializer
from .pagination import CustomPageNumberPagination
from typing import Optional
from django.utils.translation import gettext as _
from django.utils import translation
from django.db import transaction
from django.db.models import F
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse


class BaseNodeView(APIView):
	# Base view class with common functionality for node endpoints

	def validate_language(self, language: Optional[str]) -> str:
		# validate and return the language parameter

		if not language:
			raise ValueError(_("Missing mandatory params"))
		
		if language.lower() == 'italian':
			translation.activate('it')
		else:
			translation.activate('en')

		return language
	
	def format_response(self, nodes=None, error: Optional[str] = None) -> Response:
		# format the response according to the assignment

		data = {
			'nodes': nodes if nodes is not None else []
		}
		if error:
			data['error'] = error
		
		status_code = status.HTTP_400_BAD_REQUEST if error else status.HTTP_200_OK
		return Response(data, status=status_code)
	
class ListNodesView(BaseNodeView):
	# API endpoint to list all nodes in given language
	# GET /api/nodes/?language=English&page_num=0&page_size=5

	def get(self, request):
		try:
			# validate language parameter
			language = self.validate_language(request.query_params.get('language'))

			# get all nodes
			queryset = NodeTree.objects.all()
			
			# apply pagination
			paginator = CustomPageNumberPagination()
			try:
				page = paginator.paginate_queryset(queryset, request, view=self)
			except Exception as e:
				return self.format_response(error=str(e))
			
			# serialize the data
			serializer = NodeSerializer(
				page if page is not None else queryset,
				many=True,
				context={'language': language}
			)

			return self.format_response(nodes=serializer.data)
		
		except ValueError as e:
			return self.format_response(error=str(e))
		except Exception as e:
			# show actual error
			import traceback
			print(f"Error: {str(e)}")
			traceback.print_exc()
			return self.format_response(error=_("An unexpected error occurred"))
		
class GetNodeView(BaseNodeView):
	# API endpoint to get a single node by ID
	# GET /api/nodes/{id}/?language=English

	def get(self, request, node_id: int):
		try:
			# validate language parameter
			language = self.validate_language(request.query_params.get('language'))

			# get the node
			try:
				node = NodeTree.objects.get(id=node_id)
			except NodeTree.DoesNotExist:
				return self.format_response(error=_("Not found"))
			
			serializer = NodeSerializer(
				node,
				context={'language': language}
			)

			return self.format_response(nodes=[serializer.data])
		
		except ValueError as e:
			return self.format_response(error=str(e))
		except Exception as e:
			return self.format_response(error=_("An unexpected error occured"))
		
class SearchChildrenView(BaseNodeView):
	# API endpoint to search for children of a node.
	# GET /api/nodes/{id}/children/?language=English&search=keyword&page_num=0&page_size=5

	def get(self, request, node_id: int):
		try:
			# Validate parameters
			language = self.validate_language(request.query_params.get('language'))
			search_keyword = request.GET.get('search')

			if not search_keyword:
				return self.format_response(error=_("Missing mandatory params"))
			
			# get parent node
			try:
				parent_node = NodeTree.objects.get(id=node_id)
			except NodeTree.DoesNotExist:
				return self.format_response(error="Not found")
			
			# get all children of the parent node
			children = parent_node.get_children()

			# filter by search keyword in the specified language
			filtered_children = []
			for child in children:
				try:
					name_obj = child.names.get(language=language)
					if search_keyword.lower() in name_obj.node_name.lower():
						filtered_children.append(child)
				except NodeTreeName.DoesNotExist:
					continue
			
			# apply pagination
			paginator = CustomPageNumberPagination()

			try:
				page = paginator.paginate_queryset(filtered_children, request, view=self)
			except Exception as e:
				return self.format_response(error=str(e))

			# serialize the data
			serializer = NodeSerializer(
				page if page is not None else filtered_children,
				many=True,
				context={'language': language}
			)

			return self.format_response(nodes=serializer.data)
		
		except ValueError as e:
			return self.format_response(error=str(e))
		except Exception as e:
			return self.format_response(error=_("An unexpected error occurred"))
		

class CreateNodeView(BaseNodeView):
    """API endpoint to create a new node (requires authentication)
    POST /api/nodes/create/
    Headers: Authorization: Token <your-token>
    Body: {
        "parent_id": 5,
        "names": {
            "English": "New Department",
            "Italian": "Nuovo Dipartimento"
        }
    }
    """
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Get and validate input data
            parent_id = request.data.get('parent_id')
            names = request.data.get('names')
            
            # Validate required fields
            if not parent_id or not names:
                return self.format_response(error=_("Missing mandatory params"))
            
            # Validate that names contain all required languages
            required_languages = ['English', 'Italian']
            missing_languages = []
            
            for lang in required_languages:
                if lang not in names or not names[lang] or not names[lang].strip():
                    missing_languages.append(lang)
            
            if missing_languages:
                return self.format_response(
                    error=f"Names must be provided for all languages. Missing: {', '.join(missing_languages)}"
                )
            
            # Get parent node
            try:
                parent = NodeTree.objects.get(id=parent_id)
            except NodeTree.DoesNotExist:
                return self.format_response(error=_("Not found"))
            
            # Create the new node using a transaction to ensure data integrity
            with transaction.atomic():
                # Get the right value of the parent
                parent_right = parent.rgt
                
                # Update all nodes to make space for the new node
                # Shift all left values >= parent's right by 2
                NodeTree.objects.filter(
                    lft__gte=parent_right
                ).update(lft=F('lft') + 2)
                
                # Shift all right values >= parent's right by 2
                NodeTree.objects.filter(
                    rgt__gte=parent_right
                ).update(rgt=F('rgt') + 2)
                
                # Create the new node
                new_node = NodeTree.objects.create(
                    level=parent.level + 1,
                    lft=parent_right,
                    rgt=parent_right + 1
                )
                
                # Create name entries for all languages
                for language, name in names.items():
                    NodeTreeName.objects.create(
                        node=new_node,
                        language=language,
                        node_name=name
                    )
            
            # Return the created node
            serializer = NodeSerializer(
                new_node,
                context={'language': request.data.get('language', 'English')}
            )
            
            return Response({
                'nodes': [serializer.data],
                'message': 'Node created successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return self.format_response(error=_("An unexpected error occurred"))

def test_auth_page(request):
    """Serve the test HTML page"""
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Create Node Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
        }
        .section {
            margin: 20px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
        }
        input {
            margin: 5px 0;
            padding: 8px;
            width: 300px;
        }
        button {
            margin: 10px 5px;
            padding: 10px 20px;
            cursor: pointer;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .response {
            margin-top: 15px;
            padding: 15px;
            background-color: #f4f4f4;
            border-radius: 5px;
            white-space: pre-wrap;
            font-family: monospace;
        }
        .error { background-color: #ffe0e0; }
        .success { background-color: #e0ffe0; }
        .info { background-color: #e0e0ff; }
    </style>
</head>
<body>
    <h1>Node Creation Test (Protected Endpoint)</h1>
    
    <div class="section">
        <h2>Step 1: Login to Get Token</h2>
        <div>
            <input type="text" id="username" placeholder="Username" value="admin"><br>
            <input type="password" id="password" placeholder="Password"><br>
            <button onclick="login()">Login</button>
        </div>
        <div id="loginResponse" class="response" style="display:none;"></div>
    </div>
    
    <div class="section">
        <h2>Step 2: Create New Node</h2>
        <div>
            <p><strong>Token:</strong> <input type="text" id="token" placeholder="Token will appear here after login" style="width: 400px;" readonly></p>
            <p><strong>Parent Node ID:</strong> <input type="number" id="parentId" value="5" placeholder="e.g., 5 for Company"></p>
            <p><strong>English Name:</strong> <input type="text" id="nameEnglish" placeholder="English Name" value="Human Resources"></p>
            <p><strong>Italian Name:</strong> <input type="text" id="nameItalian" placeholder="Italian Name" value="Risorse Umane"></p>
            
            <button onclick="createNodeWithToken()">Create Node WITH Token</button>
            <button onclick="createNodeWithoutToken()">Create Node WITHOUT Token (Should Fail)</button>
        </div>
        <div id="createResponse" class="response" style="display:none;"></div>
    </div>
    
    <div class="section">
        <h2>Available Parent Nodes</h2>
        <div class="response info">
            ID: 5 - Company (Azienda)
            ID: 1 - Marketing
            ID: 2 - Helpdesk (Supporto tecnico)
            ID: 7 - Sales (Supporto Vendite)
            ID: 10 - Developers (Sviluppatori)
            ... and others
        </div>
    </div>

    <script>
        async function login() {
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            const responseDiv = document.getElementById('loginResponse');
            
            try {
                const response = await fetch('/api/auth/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ username, password })
                });
                
                const data = await response.json();
                responseDiv.style.display = 'block';
                responseDiv.className = response.ok ? 'response success' : 'response error';
                responseDiv.textContent = `Status: ${response.status}\\n${JSON.stringify(data, null, 2)}`;
                
                if (data.token) {
                    document.getElementById('token').value = data.token;
                }
            } catch (error) {
                responseDiv.style.display = 'block';
                responseDiv.className = 'response error';
                responseDiv.textContent = `Error: ${error.message}`;
            }
        }
        
        async function createNodeWithToken() {
            const token = document.getElementById('token').value;
            const parentId = document.getElementById('parentId').value;
            const nameEnglish = document.getElementById('nameEnglish').value;
            const nameItalian = document.getElementById('nameItalian').value;
            const responseDiv = document.getElementById('createResponse');
            
            if (!token) {
                responseDiv.style.display = 'block';
                responseDiv.className = 'response error';
                responseDiv.textContent = 'Please login first to get a token!';
                return;
            }
            
            try {
                const response = await fetch('/api/nodes/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Token ${token}`  // Include the token
                    },
                    body: JSON.stringify({
                        parent_id: parseInt(parentId),
                        names: {
                            English: nameEnglish,
                            Italian: nameItalian
                        }
                    })
                });
                
                const data = await response.json();
                responseDiv.style.display = 'block';
                responseDiv.className = response.ok ? 'response success' : 'response error';
                responseDiv.textContent = `Status: ${response.status}\\n${JSON.stringify(data, null, 2)}`;
                
                if (response.ok) {
                    responseDiv.textContent += '\\n\\n SUCCESS! Node created with authentication.';
                }
            } catch (error) {
                responseDiv.style.display = 'block';
                responseDiv.className = 'response error';
                responseDiv.textContent = `Error: ${error.message}`;
            }
        }
        
        async function createNodeWithoutToken() {
            const parentId = document.getElementById('parentId').value;
            const nameEnglish = document.getElementById('nameEnglish').value;
            const nameItalian = document.getElementById('nameItalian').value;
            const responseDiv = document.getElementById('createResponse');
            
            try {
                const response = await fetch('/api/nodes/create/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                        // NO Authorization header - this should fail
                    },
                    body: JSON.stringify({
                        parent_id: parseInt(parentId),
                        names: {
                            English: nameEnglish,
                            Italian: nameItalian
                        }
                    })
                });
                
                const data = await response.json();
                responseDiv.style.display = 'block';
                responseDiv.className = response.ok ? 'response success' : 'response error';
                responseDiv.textContent = `Status: ${response.status}\\n${JSON.stringify(data, null, 2)}`;
                
                if (!response.ok) {
                    responseDiv.textContent += '\\n\\n EXPECTED FAILURE: Cannot create node without authentication.';
                }
            } catch (error) {
                responseDiv.style.display = 'block';
                responseDiv.className = 'response error';
                responseDiv.textContent = `Error: ${error.message}`;
            }
        }
    </script>
</body>
</html>'''
    return HttpResponse(html_content, content_type='text/html')