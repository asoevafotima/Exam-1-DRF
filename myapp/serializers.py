from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    channels_count = serializers.SerializerMethodField()

    def get_channels_count(self, obj):
        return Channel.objects.filter(owner=obj).count()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at', 'channels_count']

class ChannelSerializer(serializers.ModelSerializer):
    videos_count = serializers.SerializerMethodField()

    def get_videos_count(self, obj):
        return Video.objects.filter(channel=obj).count()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'created_at', 'videos_count']



class UserDetailSerializer(serializers.ModelSerializer):
    channels = serializers.SerializerMethodField()
    total_videos = serializers.SerializerMethodField()

    def get_channels(self, obj):
        channels = Channel.objects.filter(owner=obj)
        return ChannelSerializer(channels, many=True).data

    def get_total_videos(self, obj):
        channels = Channel.objects.filter(owner=obj)
        total = 0
        for channel in channels:
            total += Video.objects.filter(channel=channel).count()
        return total

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at', 'channels', 'total_videos']



class ChannelSerializer(serializers.ModelSerializer):
    owner_details = UserSerializer(source='owner', read_only=True)
    subscribers_count = serializers.SerializerMethodField()

    def get_subscribers_count(self, obj):
        return Subscription.objects.filter(channel=obj).count()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'owner', 'owner_details', 'subscribers_count', 'created_at']



class ChannelDetailSerializer(serializers.ModelSerializer):
    
    owner_details = UserSerializer(source='owner', read_only=True)
    latest_videos = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'owner', 'owner_details', 'latest_videos', 'total_views', 'created_at']


class VideoSerializer(serializers.ModelSerializer):
    channel = ChannelSerializer(read_only=True)
    channel_id = serializers.PrimaryKeyRelatedField(
        queryset=Channel.objects.all(), source='channel', write_only=True
    )

    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'views', 'channel', 'channel_id', 'created_at']



class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'text', 'user', 'created_at']