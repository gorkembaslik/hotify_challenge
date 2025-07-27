from django.urls import path
from .views import ListNodesView, GetNodeView, SearchChildrenView, CreateNodeView
from .auth_views import LoginView, LogoutView
app_name = 'org_chart'

urlpatterns = [
	# Authentication endpoints
    path('api/auth/login/', LoginView.as_view(), name='login'),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    
    # Node endpoints
	path('api/nodes/', ListNodesView.as_view(), name='list-nodes'),
	path('api/nodes/create/', CreateNodeView.as_view(), name='create-node'),
	path('api/nodes/<int:node_id>/', GetNodeView.as_view(), name='get-node'),
	path('api/nodes/<int:node_id>/children/', SearchChildrenView.as_view(), name='search-children')
]