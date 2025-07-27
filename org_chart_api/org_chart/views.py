from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import NodeTree, NodeTreeName
from .serializers import NodeSerializer, APIResponseSerializer
from .pagination import CustomPageNumberPagination
from typing import Dict, Any, Optional
from django.utils.translation import gettext as _
from django.utils import translation
from django.db import transaction
from django.db.models import F
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


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
            if 'English' not in names or 'Italian' not in names:
                return self.format_response(
                    error=_("Names must be provided for both English and Italian")
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