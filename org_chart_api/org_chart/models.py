from django.db import models
from django.core.exceptions import ValidationError
from typing import Optional

class NodeTree(models.Model):
	"""
	Represents a node in the organizational chart using the Nested Set model
	"""
	level = models.IntegerField(help_text="Depth level in the tree hierarchy")
	lft = models.IntegerField(db_column='ileft', help_text="Left boundary for nested set")
	rgt = models.IntegerField(db_column='iright', help_text="Right boundary for nested set")

	class Meta:
		db_table = 'node_tree'
		ordering = ['lft']

	def __str__(self) -> str:
		return f"Node {self.id} (Level: {self.level}, Left: {self.lft}, Right: {self.rgt})"
	
	@property
	def children_count(self) -> int:
		return (self.rgt - self.lft - 1) // 2
	
	def get_children(self):
		# all direct children
		return NodeTree.objects.filter(
			lft__gt=self.lft,
			rgt__lt=self.rgt,
			level=self.level + 1
		)
	
	def get_all_descendants(self):
		# children, grandchilden, etc.
		return NodeTree.objects.filter(
			lft__gt=self.lft,
			rgt__lt=self.rgt
		)

class NodeTreeName(models.Model):
	# stores translations for node names in different languages

	LANGUAGE_CHOICES = [
		('English', 'English'),
		('Italian', 'Italian')
	]

	node = models.ForeignKey(
		NodeTree,
		on_delete=models.CASCADE,
		related_name='names',
		help_text="Reference to the node"
	)
	language = models.CharField(
		max_length=50,
		choices=LANGUAGE_CHOICES,
		help_text="Language of the translation"
	)
	node_name = models.CharField(
		max_length=255,
		help_text="Translated name of the node"
	)

	class Meta:
		db_table = 'node_tree_names'
		unique_together = ['node', 'language']

	def __str__(self) -> str:
		return f"{self.node_name} ({self.language})"