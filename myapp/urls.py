from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserListView.as_view()),
    path('users/<int:pk>/', views.UserDetailView.as_view()),
    path('users/<int:pk>/channels/', views.UserChannelsView.as_view()),
    path('channels/', views.ChannelListView.as_view()),
    path('channels/<int:pk>/', views.ChannelDetailView.as_view()),
    path('channels/<int:pk>/delete/', views.ChannelDeleteView.as_view()),
    path('channels/<int:pk>/videos/', views.ChannelVideosView.as_view()),
    path('channels/<int:pk>/stats/', views.ChannelStatsView.as_view()),
    path('videos/', views.VideoListView.as_view()),
    path('videos/<int:pk>/', views.VideoDetailView.as_view()),
    path('videos/<int:pk>/update/', views.VideoUpdateView.as_view()),
    path('videos/<int:pk>/delete/', views.VideoDeleteView.as_view()),
    path('videos/<int:pk>/comments/', views.VideoCommentsView.as_view()),
    path('videos/<int:pk>/comments/create/', views.VideoCommentsCreateView.as_view()),
    path('videos/<int:pk>/like/', views.LikeCreateView.as_view()),
    path('videos/<int:pk>/like/delete/', views.LikeDeleteView.as_view()),
    path('comments/<int:pk>/', views.CommentDetailView.as_view()),
    path('comments/<int:pk>/delete/', views.CommentDeleteView.as_view()),
]