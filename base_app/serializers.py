from rest_framework import serializers


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
    created_by = serializers.CharField(source='created_by.user_name', read_only=True)
    complaint_image_url = serializers.SerializerMethodField()

    complaint_category = serializers.SlugRelatedField(
        slug_field="name",
        queryset=ComplaintCategory.objects.all()
    )
    complaint_subcategory = serializers.SlugRelatedField(
        slug_field="name",
        queryset=ComplaintSubCategory.objects.all()
    )
    zone = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Zone.objects.all()
    )
    ward = serializers.SlugRelatedField(
        slug_field="name",
        queryset=Ward.objects.all()
    )

    class Meta:
        model = Complaint
        fields = '__all__'
        read_only_fields = ('complaint_id', 'complaint_code', 'created_datetime', 'updated_datetime')

    def get_complaint_image_url(self, obj):
        if obj.complaint_image:
            return obj.complaint_image.url
        return None

class ComplaintCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintCategory
        fields = ['id', 'name']

class ComplaintSubCategorySerializer(serializers.ModelSerializer):
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=ComplaintCategory.objects.all(),
        source='category'
    )
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = ComplaintSubCategory
        fields = ['id', 'name', 'category_id', 'category_name']

class ZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Zone
        fields = ['id', 'name', 'code']


class WardSerializer(serializers.ModelSerializer):
    zone_name = serializers.CharField(source='zone.name', read_only=True)

    class Meta:
        model = Ward
        fields = ['id', 'name', 'zone', 'zone_name']
        
class SupervisorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupervisorProfile
        fields = [
            'id', 'user_name', 'user_email', 'contact_number', 'password',
            'address', 'city', 'state', 'zone', 'ward', 'profile_image',
            'created_by', 'updated_by', 'created_datetime', 'updated_datetime'
        ]
        extra_kwargs = {
            'password': {'write_only': True}  # password GET me nahi aayega
        }

    def create(self, validated_data):
        # Admin sets the password
        return SupervisorProfile.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance