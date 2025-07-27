from rest_framework import serializers
from .models import NodeTree, NodeTreeName
from typing import Dict, Any

# connects Django models to API responses&requests

'''
Translator between Python objects (Django models) <-> JSON or other data formats used in APIs

1. converts Django model instances to JSON data and vica versa (for API responses)
2. validates incoming JSON data (for API requests)

'''

class NodeSerializer(serializers.Serializer):
	# Serializer for node data in API responses

	node_id = serializers.IntegerField(source='id')
	name = serializers.SerializerMethodField()
	children_count = serializers.IntegerField(read_only=True)

	def get_name(self, obj:NodeTree) -> str:
		# Get the node name in the requested language

		language = self.context.get('language', 'English')
		try:
			name_obj = obj.names.get(language=language)
			return name_obj.node_name
		except NodeTreeName.DoesNotExist:
			# set to English if translation not found
			try:
				name_obj = obj.names.get(language='English')
				return name_obj.node_name
			except NodeTreeName.DoesNotExist:
				return f"Node {obj.id}"
			

class APIResponseSerializer(serializers.Serializer):
	# Standard API response format serializer.

	nodes = NodeSerializer(many=True, required=False, default=[])
	error = serializers.CharField(required=False, allow_blank=True)

	def to_representation(self, instance: Dict[str, Any]) -> Dict[str, Any]:
		# customize the output to exclude None values
		data = super().to_representation(instance)
		
		if not data.get('error'):
			data.pop('error', None)
		
		return data
