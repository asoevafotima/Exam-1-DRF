from rest_framework.generics import ListCreateAPIView, RetrieveAPIView,ListAPIView, RetrieveUpdateAPIView
from .models import *
from .serializers import *
from .pagination import CustomPagination
from rest_framework.response import Response
from rest_framework.views import APIView

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
        user_id = self.kwargs['pk']
        return Channel.objects.filter(owner_id=user_id)
    

class ChannelListView(ListCreateAPIView):
    serializer_class = ChannelSerializer
    queryset = Channel.objects.all()

    
class ChannelDetailView(RetrieveAPIView):
    serializer_class = ChannelDetailSerializer
    queryset = Channel.objects.all()


class ChannelDeleteView(APIView):
    def delete(self, request, pk):
        try:
            channel = Channel.objects.get(pk=pk)
        except Channel.DoesNotExist:
            return Response({'error': 'channel not found'})
        
        channel_id = channel.id
        channel.delete()
        return Response({'status': 'deleted', 'deleted_channel_id': channel_id})
    

class ChannelVideosView(ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        channel_id = self.kwargs['pk']
        videos = Video.objects.filter(channel_id=channel_id)

        sort = self.request.query_params.get('sort', 'latest')
        if sort == 'popular':
            videos = videos.order_by('views')
        else:
            videos = videos.order_by('created_at')

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
    

class VideoListView(ListCreateAPIView):
    serializer_class = VideoSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        videos = Video.objects.all()

        search = self.request.query_params.get('search')
        if search:
            videos = videos.filter(title__icontains=search)
  
        ordering = self.request.query_params.get('ordering', 'created_at')
        videos = videos.order_by(ordering)

        return videos
    

class VideoDetailView(APIView):
    def get(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        video.views += 1
        video.save()

        comments_count = Comment.objects.filter(video=video).count()
        likes_count = Like.objects.filter(video=video).count()

        serializer = VideoSerializer(video)
        return Response({
            **serializer.data,
            'comments_count': comments_count,
            'likes_count': likes_count
        })
    

class VideoUpdateView(RetrieveUpdateAPIView):
    serializer_class = VideoSerializer
    queryset = Video.objects.all()



class VideoDeleteView(APIView):
    def delete(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'Video not found'})

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
        video_id = self.kwargs['pk']
        comments = Comment.objects.filter(video_id=video_id)

        sort = self.request.query_params.get('sort', 'new')
        if sort == 'old':
            comments = comments.order_by('created_at')
        else:
            comments = comments.order_by('created_at')

        return comments
    
class VideoCommentsCreateView(APIView):
    def post(self, request, pk):
        try:
            video = Video.objects.get(pk=pk)
        except Video.DoesNotExist:
            return Response({'error': 'video not found'})

        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({'error': 'user not found'})

        comment = Comment.objects.create(
            video=video,
            user=user,
            text=request.data.get('text')
        )

        serializer = CommentSerializer(comment)
        data = serializer.data
        data['video_id'] = video.id
        return Response(data)
    

class CommentDetailView(APIView):
    def get(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'comment not found'}  )

        serializer = CommentSerializer(comment)
        data = serializer.data
        data['video'] = {'id': comment.video.id, 'title': comment.video.title}
        return Response(data)
    


class CommentDeleteView(APIView):
    def delete(self, request, pk):
        try:
            comment = Comment.objects.get(pk=pk)
        except Comment.DoesNotExist:
            return Response({'error': 'comment not found'})

        comment_id = comment.id
        comment.delete()
        return Response({'status': 'deleted', 'deleted_comment_id': comment_id})
    

class LikeCreateView(APIView):
    def post(self, request, pk):
        video = Video.objects.get(pk=pk)
        user_id = request.data.get('user_id')
        
        like = Like.objects.filter(video=video, user_id=user_id).first()
        if like:
            return Response({'error': 'already liked'})
        
        Like.objects.create(video=video, user_id=user_id)
        return Response({'liked': True, 'total_likes': Like.objects.filter(video=video).count()})
    
    
class LikeDeleteView(APIView):
    def delete(self, request, pk):
        video = Video.objects.get(pk=pk)
        user_id = request.data.get('user_id')
        
        like = Like.objects.filter(video=video, user_id=user_id).first()
        if like:
            like.delete()
        
        return Response({'liked': False, 'total_likes': Like.objects.filter(video=video).count()})
    

