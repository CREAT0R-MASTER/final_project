from rest_framework import serializers;
from .models import *;

class UserProfileSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'

class QRCodeSerializers(serializers.ModelSerializer):   
    class Meta:
        model = QRCode
        fields = '__all__'
        
class ComplaintSerializers(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.user_name', read_only=True)
    complaint_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ('complaint_id', 'complaint_code', 'created_datetime', 'updated_datetime')
    
    def get_complaint_image_url(self, obj):
        if obj.complaint_image:
            return obj.complaint_image.url
        return None

# class DropdownValueSerializers(serializers.ModelSerializer):
#     class Meta:
#         model = DropdownValue
#         fields = '__all__'

class ComplaintCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name']

class ComplaintSubCategorySerializer(serializers.ModelSerializer):
    category = ComplaintCategorySerializer(read_only=True)

    class Meta:
        model = ComplaintSubCategory
        fields = ['id', 'name', 'category']

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'name']

class WardSerializer(serializers.ModelSerializer):
    zone = ZoneSerializer(read_only=True)

    class Meta:
        model = Ward
        fields = ['id', 'name', 'zone']