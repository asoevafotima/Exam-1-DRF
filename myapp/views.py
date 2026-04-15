from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import *
from .serializers import *
from .pagination import CustomPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import timedelta
from django.utils import timezone


class UserListView(ListCreateAPIView):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    pagination_class = CustomPagination


class UserDetailView(RetrieveAPIView):
    serializer_class = UserDetailSerializer
    queryset = User.objects.all()


class UserChannelsView(ListAPIView):
    serializer_class = ChannelSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Channel.objects.none()
        user_id = self.kwargs['pk']
        return Channel.objects.filter(owner_id=user_id)


class ChannelListView(ListCreateAPIView):
    serializer_class = ChannelSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        return Channel.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ChannelDetailView(RetrieveUpdateAPIView):
    serializer_class = ChannelDetailSerializer
    queryset = Channel.objects.all()

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:
            return [IsAuthenticated()]
        return [AllowAny()]

    def update(self, request, *args, **kwargs):
        channel = self.get_object()
        if channel.owner != request.user:
            return Response({'error': 'not your channel'}, status=403)
        return super().update(request, *args, **kwargs)


class ChannelDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            channel = Channel.objects.get(pk=pk)
        except Channel.DoesNotExist:
            return Response({'error': 'channel not found'})

        if channel.owner != request.user:
            return Response({'error': 'not your channel'}, status=403)

        channel_id = channel.id
        channel.delete()
        return Response({'status': 'deleted', 'deleted_channel_id': channel_id})


class ChannelVideosView(ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Video.objects.none()
        channel_id = self.kwargs['pk']
        videos = Video.objects.filter(channel_id=channel_id)
        sort = self.request.query_params.get('sort', 'latest')
        if sort == 'popular':
            videos = videos.order_by('-views')
        else:
            videos = videos.order_by('-created_at')
        return videos


class ChannelStatsView(APIView):
    def get(self, request, pk):
        try:
            channel = Channel.objects.get(pk=pk)
        except Channel.DoesNotExist:
            return Response({'error': 'Channel not found'})

        videos = Video.objects.filter(channel=channel)
        total_videos = videos.count()
        total_views = 0
        for video in videos:
            total_views += video.views

        avg_views = 0
        if total_videos > 0:
            avg_views = total_views / total_videos

        top_video = None
        for video in videos:
            if top_video is None or video.views > top_video.views:
                top_video = video

        return Response({
            'total_videos': total_videos,
            'total_views': total_views,
            'avg_views': avg_views,
            'top_video': {'id': top_video.id, 'title': top_video.title, 'views': top_video.views} if top_video else None
        })


class MyChannelsView(ListAPIView):
    serializer_class = ChannelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Channel.objects.filter(owner=self.request.user)

class VideoListView(ListCreateAPIView):
    serializer_class = VideoSerializer
    pagination_class = CustomPagination

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_queryset(self):
        videos = Video.objects.all()
        search = self.request.query_params.get('search')
        if search:
            videos = videos.filter(title__icontains=search)
        channel_id = self.request.query_params.get('channel')
        if channel_id:
            return videos.filter(channel_id=channel_id).order_by('-views')
        ordering = self.request.query_params.get('ordering', 'created_at')
        return videos.order_by(ordering)


class VideoDetailView(APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        video.views += 1
        video.save()

        comments = Comment.objects.filter(video=video)
        likes_count = Like.objects.filter(video=video).count()
        comments_serializer = CommentSerializer(comments, many=True)

        serializer = VideoSerializer(video)
        return Response({
            **serializer.data,
            'comments': comments_serializer.data,
            'likes_count': likes_count
        })


class VideoUpdateView(RetrieveUpdateAPIView):
    serializer_class = VideoSerializer
    queryset = Video.objects.all()
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        video = self.get_object()
        if video.channel.owner != request.user:
            return Response({'error': 'not your video'}, status=403)
        return super().update(request, *args, **kwargs)


class VideoDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'Video not found'})

        if video.channel.owner != request.user:
            return Response({'error': 'not your video'}, status=403)

        comments_count = Comment.objects.filter(video=video).count()
        likes_count = Like.objects.filter(video=video).count()
        video_id = video.id
        video.delete()

        return Response({
            'status': 'deleted',
            'deleted_video_id': video_id,
            'cascade': {
                'comments_deleted': comments_count,
                'likes_deleted': likes_count
            }
        })


class VideoCommentsView(ListAPIView):
    serializer_class = CommentSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Comment.objects.none()
        video_id = self.kwargs['pk']
        comments = Comment.objects.filter(video_id=video_id)
        sort = self.request.query_params.get('sort', 'new')
        if sort == 'old':
            comments = comments.order_by('created_at')
        else:
            comments = comments.order_by('-created_at')
        return comments


class VideoCommentsCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        comment = Comment.objects.create(
            video=video,
            user=request.user,
            text=request.data.get('text')
        )
        serializer = CommentSerializer(comment)
        return Response(serializer.data)


class CommentDetailView(APIView):
    def get(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'comment not found'})

        serializer = CommentSerializer(comment)
        data = serializer.data
        data['video'] = {'id': comment.video.id, 'title': comment.video.title}
        return Response(data)


class CommentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'comment not found'})

        if comment.user != request.user:
            return Response({'error': 'not your comment'}, status=403)

        comment_id = comment.id
        comment.delete()
        return Response({'status': 'deleted', 'deleted_comment_id': comment_id})


class LikeCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        like = Like.objects.filter(video=video, user=request.user).first()
        if like:
            return Response({'error': 'already liked'})

        Like.objects.create(video=video, user=request.user)
        return Response({'liked': True, 'total_likes': Like.objects.filter(video=video).count()})


class LikeDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        like = Like.objects.filter(video=video, user=request.user).first()
        if like:
            like.delete()
        return Response({'liked': False, 'total_likes': Like.objects.filter(video=video).count()})


class VideoLikesView(APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        likes = Like.objects.filter(video=video)
        fake_user_id = request.query_params.get('user_id')

        return Response({
            'total_likes': likes.count(),
            'is_liked_by_current_user': likes.filter(user_id=fake_user_id).exists() if fake_user_id else False,
            'users': list(likes.values('user__id', 'user__username'))
        })


class VideoSearchView(APIView):
    def get(self, request):
        query = request.query_params.get('query', '')
        videos = Video.objects.filter(title__icontains=query) | Video.objects.filter(description__icontains=query)
        serializer = VideoSerializer(videos, many=True)
        return Response({'results': serializer.data, 'total': videos.count()})


class VideoTopView(APIView):
    def get(self, request):
        videos = Video.objects.all()
        time_filter = request.query_params.get('time')
        if time_filter == 'day':
            videos = videos.filter(created_at__gte=timezone.now() - timedelta(days=1))
        elif time_filter == 'week':
            videos = videos.filter(created_at__gte=timezone.now() - timedelta(weeks=1))
        elif time_filter == 'month':
            videos = videos.filter(created_at__gte=timezone.now() - timedelta(days=30))
        videos = videos.order_by('views')
        serializer = VideoSerializer(videos, many=True)
        return Response({'top_videos': serializer.data})


class VideoRelatedView(APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        videos = Video.objects.filter(channel=video.channel)
        serializer = VideoSerializer(videos, many=True)
        return Response({'related': serializer.data})


class StatsVideosView(APIView):
    def get(self, request):
        videos = Video.objects.all()
        total_views = 0
        for video in videos:
            total_views += video.views

        avg_views = 0
        if videos.count() > 0:
            avg_views = total_views / videos.count()

        return Response({
            'total_videos': videos.count(),
            'total_views': total_views,
            'avg_views': avg_views
        })


class StatsUsersView(APIView):
    def get(self, request):
        total_users = User.objects.count()
        users_with_channels = 0
        active_users = 0

        for user in User.objects.all():
            if Channel.objects.filter(owner=user):
                users_with_channels += 1
            if Comment.objects.filter(user=user):
                active_users += 1

        return Response({
            'total_users': total_users,
            'users_with_channels': users_with_channels,
            'active_users': active_users
        })


class StatsChannelsView(APIView):
    def get(self, request):
        total_channels = Channel.objects.count()
        total_videos = Video.objects.count()

        avg_videos = 0
        if total_channels > 0:
            avg_videos = total_videos / total_channels

        return Response({
            'total_channels': total_channels,
            'total_videos': total_videos,
            'avg_videos_per_channel': avg_videos
        })