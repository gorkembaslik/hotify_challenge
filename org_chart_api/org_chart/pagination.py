from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils.translation import gettext as _
from typing import Any, Dict

class CustomPageNumberPagination(PageNumberPagination):
	# Custom pagination class as requested

	page_size = 5
	page_size_query_param = 'page_size'
	page_query_param = 'page_num'
	max_page_size = 1000

	def get_page_number(self, request, paginator):
		# override to use 0-based page numbers
		page_number = request.query_params.get(self.page_query_param, 0)

		try:
			page_number = int(page_number)
			if page_number < 0:
				raise ValidationError(_("Invalid page number requested"))
			
			return page_number + 1
		except (ValueError, TypeError):
			raise ValidationError(_("Invalid page number requested"))
		
	def get_page_size(self, request):
		
		if self.page_size_query_param:
			try:
				page_size = int(request.query_params.get(
					self.page_size_query_param, self.page_size
				))
				if page_size < 0 or page_size > self.max_page_size:
					raise ValidationError(_("Invalid page size requested"))
				return page_size
			except (ValueError, TypeError):
				raise ValidationError(_("Invalid page size requested"))
		return self.page_size
