from django.db import migrations, connection

def load_initial_data(apps, schema_editor):
	NodeTree = apps.get_model('org_chart', 'NodeTree')
	NodeTreeName = apps.get_model('org_chart', 'NodeTreeName')

	# creating nodes based on provided data

	nodes_data = [
		{'id': 1, 'level': 2, 'lft': 2, 'rgt': 3},
        {'id': 2, 'level': 2, 'lft': 4, 'rgt': 5},
        {'id': 3, 'level': 2, 'lft': 6, 'rgt': 7},
        {'id': 4, 'level': 2, 'lft': 8, 'rgt': 9},
        {'id': 5, 'level': 1, 'lft': 1, 'rgt': 24},
        {'id': 6, 'level': 2, 'lft': 10, 'rgt': 11},
        {'id': 7, 'level': 2, 'lft': 12, 'rgt': 19},
        {'id': 8, 'level': 3, 'lft': 15, 'rgt': 16},
        {'id': 9, 'level': 3, 'lft': 17, 'rgt': 18},
        {'id': 10, 'level': 2, 'lft': 20, 'rgt': 21},
        {'id': 11, 'level': 3, 'lft': 13, 'rgt': 14},
        {'id': 12, 'level': 2, 'lft': 22, 'rgt': 23}
	]

	# creating nodes
	for node_data in nodes_data:
		NodeTree.objects.create(**node_data)

	# creating node names accordingly
	names_data = [
		(1, 'English', 'Marketing'),
        (1, 'Italian', 'Marketing'),
        (2, 'English', 'Helpdesk'),
        (2, 'Italian', 'Supporto tecnico'),
        (3, 'English', 'Managers'),
        (3, 'Italian', 'Managers'),
        (4, 'English', 'Customer Account'),
        (4, 'Italian', 'Assistenza Cliente'),
        (5, 'English', 'Company'),
        (5, 'Italian', 'Azienda'),
        (6, 'English', 'Accounting'),
        (6, 'Italian', 'Amministrazione'),
        (7, 'English', 'Sales'),
        (7, 'Italian', 'Supporto Vendite'),
        (8, 'English', 'Italy'),
        (8, 'Italian', 'Italia'),
        (9, 'English', 'Europe'),
        (9, 'Italian', 'Europa'),
        (10, 'English', 'Developers'),
        (10, 'Italian', 'Sviluppatori'),
        (11, 'English', 'North America'),
        (11, 'Italian', 'Nord America'),
        (12, 'English', 'Quality Assurance'),
        (12, 'Italian', 'Controllo Qualità')
	]

	# creating node names

	for node_id, language, name in names_data:
		node = NodeTree.objects.get(id=node_id)
		NodeTreeName.objects.create(
			node=node,
			language=language,
			node_name=name
		)
		
		with connection.cursor() as cursor:
			cursor.execute("SELECT setval('node_tree_id_seq', (SELECT MAX(id) FROM node_tree));")
			cursor.execute("SELECT setval('node_tree_names_id_seq', (SELECT MAX(id) FROM node_tree_names));")

def reverse_load_data(apps, schema_editor):
	NodeTreeName = apps.get_model('org_chart', 'NodeTreeName')
	NodeTree = apps.get_model('org_chart', 'NodeTree')

	NodeTreeName.objects.all().delete()
	NodeTree.objects.all().delete()
	
class Migration(migrations.Migration):

	dependencies = [
		('org_chart', '0001_initial')
	]

	operations = [
		migrations.RunPython(load_initial_data, reverse_load_data)
	]