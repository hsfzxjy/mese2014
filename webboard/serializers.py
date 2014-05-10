from django.core.urlresolvers import reverse
from rest_framework import serializers, pagination
import models
from django.contrib.auth.models import User
import accounts.serializers
from common.serializers import WritableRelatedField

class PassageSerializer(serializers.ModelSerializer):

	author = WritableRelatedField(serializer_class = accounts.serializers.UserSerializer)
	
	class Meta:
		model = models.Passage
		
class CommentSerializer(serializers.ModelSerializer):
	
	author = WritableRelatedField(serializer_class = accounts.serializers.UserSerializer)
	
	class Meta:
		model = models.Comment
		exclude = ['passage']
		
class PaginatedCommentSerializer(pagination.PaginationSerializer):

	class Meta:
		object_serializer_class = CommentSerializer