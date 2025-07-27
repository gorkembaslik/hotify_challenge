from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import NodeTree


class NodeAPITest(TestCase):
    """Test all API endpoints using the migration data"""
    
    def setUp(self):
        self.client = APIClient()
    
    # List Nodes Tests
    def test_list_nodes_success(self):
        """Test successful listing of all nodes"""
        url = reverse('org_chart:list-nodes')
        response = self.client.get(url, {'language': 'English'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('nodes', response.data)
        # First page should have 5 nodes (default pagination)
        self.assertEqual(len(response.data['nodes']), 5)
        
    def test_list_nodes_missing_language(self):
        """Test error when language parameter is missing"""
        url = reverse('org_chart:list-nodes')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing mandatory params')
        
    def test_list_nodes_italian(self):
        """Test listing nodes in Italian"""
        url = reverse('org_chart:list-nodes')
        response = self.client.get(url, {'language': 'Italian'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if we get Italian names
        company_node = next((n for n in response.data['nodes'] if n['node_id'] == 5), None)
        self.assertEqual(company_node['name'], 'Azienda')
        
    def test_list_nodes_pagination(self):
        """Test pagination"""
        url = reverse('org_chart:list-nodes')
        # Get second page
        response = self.client.get(url, {
            'language': 'English',
            'page_num': 1,
            'page_size': 5
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Second page should have the remaining nodes
        self.assertEqual(len(response.data['nodes']), 5)
    
    # Get Node Tests
    def test_get_company_node(self):
        """Test getting the Company node"""
        url = reverse('org_chart:get-node', args=[5])
        response = self.client.get(url, {'language': 'English'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['nodes']), 1)
        node = response.data['nodes'][0]
        self.assertEqual(node['node_id'], 5)
        self.assertEqual(node['name'], 'Company')
        self.assertEqual(node['children_count'], 11)
        
    def test_get_node_italian(self):
        """Test getting node in Italian"""
        url = reverse('org_chart:get-node', args=[7])
        response = self.client.get(url, {'language': 'Italian'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nodes'][0]['name'], 'Supporto Vendite')
        
    def test_get_node_not_found(self):
        """Test error when node doesn't exist"""
        url = reverse('org_chart:get-node', args=[999])
        response = self.client.get(url, {'language': 'English'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Not found')
    
    # Search Children Tests
    def test_search_children_of_company(self):
        """Test searching children of Company node"""
        url = reverse('org_chart:search-children', args=[5])
        response = self.client.get(url, {
            'language': 'English',
            'search': 'Sales'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['nodes']), 1)
        self.assertEqual(response.data['nodes'][0]['node_id'], 7)
        self.assertEqual(response.data['nodes'][0]['name'], 'Sales')
        
    def test_search_children_of_sales(self):
        """Test searching children of Sales node"""
        url = reverse('org_chart:search-children', args=[7])
        response = self.client.get(url, {
            'language': 'English',
            'search': 'Italy'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['nodes']), 1)
        self.assertEqual(response.data['nodes'][0]['node_id'], 8)
        
    def test_search_no_results(self):
        """Test search with no results"""
        url = reverse('org_chart:search-children', args=[5])
        response = self.client.get(url, {
            'language': 'English',
            'search': 'NonExistent'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['nodes']), 0)
        
    def test_search_missing_keyword(self):
        """Test error when search keyword is missing"""
        url = reverse('org_chart:search-children', args=[5])
        response = self.client.get(url, {'language': 'English'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing mandatory params')


class NodeModelTest(TestCase):
    """Test model methods"""
    
    def test_children_count_calculation(self):
        """Test children_count property with migration data"""
        from .models import NodeTree
        
        # Company node (id=5) has lft=1, rgt=24
        # children_count = (24 - 1 - 1) / 2 = 11
        company = NodeTree.objects.get(id=5)
        self.assertEqual(company.children_count, 11)
        
        # Marketing node (id=1) has lft=2, rgt=3
        # children_count = (3 - 2 - 1) / 2 = 0
        marketing = NodeTree.objects.get(id=1)
        self.assertEqual(marketing.children_count, 0)
        
        # Sales node (id=7) has lft=12, rgt=19
        # children_count = (19 - 12 - 1) / 2 = 3
        sales = NodeTree.objects.get(id=7)
        self.assertEqual(sales.children_count, 3)

class I18nTest(TestCase):
    """Test internationalization functionality"""
    
    def setUp(self):
        self.client = APIClient()
    
    def test_italian_error_messages(self):
        """Test that error messages are returned in Italian when Italian language is requested"""
        url = reverse('org_chart:get-node', args=[999])
        response = self.client.get(url, {'language': 'Italian'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Non trovato')
    
    def test_english_error_messages(self):
        """Test that error messages are returned in English when English is requested"""
        url = reverse('org_chart:get-node', args=[999])
        response = self.client.get(url, {'language': 'English'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Not found')
    
    def test_missing_params_italian(self):
        """Test missing params error in Italian"""
        url = reverse('org_chart:list-nodes')
        # Even without language param, we can't get Italian error
        # because we need the language param to know which language to use
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing mandatory params')

class AuthenticationTest(TestCase):
    """Test authentication functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
    
    def test_login_success(self):
        """Test successful login"""
        url = reverse('org_chart:login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('org_chart:login')
        response = self.client.post(url, {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_missing_params(self):
        """Test login with missing parameters"""
        url = reverse('org_chart:login')
        response = self.client.post(url, {
            'username': 'testuser'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing mandatory params')
    
    def test_logout(self):
        """Test logout functionality"""
        # First login
        token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        
        # Then logout
        url = reverse('org_chart:logout')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify token is deleted
        self.assertFalse(Token.objects.filter(user=self.user).exists())

class CreateNodeTest(TestCase):
    """Test node creation endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        # Create a test user and token
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        
    def test_create_node_success(self):
        """Test successful node creation with authentication"""
        # Authenticate
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('org_chart:create-node')
        data = {
            'parent_id': 5,  # Company node
            'names': {
                'English': 'Test Department',
                'Italian': 'Dipartimento Test'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['nodes']), 1)
        self.assertEqual(response.data['nodes'][0]['name'], 'Test Department')
        self.assertEqual(response.data['nodes'][0]['children_count'], 0)
        
        # Verify the node was actually created
        new_node = NodeTree.objects.get(id=response.data['nodes'][0]['node_id'])
        self.assertEqual(new_node.level, 2)  # Child of Company (level 1)
        
    def test_create_node_no_auth(self):
        """Test that creating node without authentication fails"""
        url = reverse('org_chart:create-node')
        data = {
            'parent_id': 5,
            'names': {
                'English': 'Test Department',
                'Italian': 'Dipartimento Test'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_create_node_missing_parent_id(self):
        """Test error when parent_id is missing"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('org_chart:create-node')
        data = {
            'names': {
                'English': 'Test Department',
                'Italian': 'Dipartimento Test'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Missing mandatory params')
    
    def test_create_node_invalid_parent(self):
        """Test error when parent doesn't exist"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('org_chart:create-node')
        data = {
            'parent_id': 999,
            'names': {
                'English': 'Test Department',
                'Italian': 'Dipartimento Test'
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['error'], 'Not found')
    
    def test_create_node_missing_language(self):
        """Test error when not all languages are provided"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')
        
        url = reverse('org_chart:create-node')
        data = {
            'parent_id': 5,
            'names': {
                'English': 'Test Department'
                # Missing Italian
            }
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('must be provided for both', response.data['error'])