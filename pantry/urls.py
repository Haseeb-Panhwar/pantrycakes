from django.urls import path
from pantry import views
from pantrycakes import settings
from django.contrib.auth.views import LogoutView
from django.conf.urls.static import static


urlpatterns = [
    
    path("logout/",LogoutView.as_view(next_page='login'),name='logout'),
    path("",views.CustomLoginView.as_view(),name='login'),
    path("register/",views.RegisterPage.as_view(),name='register'),
    path('collections/',views.CollectionList.as_view(),name='collections'),
    path('recipe /',views.getRecipe,name='recipe'),
    path('collection-items/<int:collection_id>/',views.ItemList,name='items'),
    path('collection-createitem/<int:collection_id>/',views.ItemCreate.as_view(),name='create-item'),
    path("collection-update/<int:pk>/",views.CollectionUpdate.as_view(),name='collection-update'),
    path("collection-item-update/<int:pk>/",views.ItemUpdate.as_view(),name='item-update'),
    path("collection-item-delete/<int:pk>/",views.ItemDelete.as_view(),name='item-delete'),
    path("collection-create/",views.CollectionCreate.as_view(),name='collection-create'),
    path('collection-delete/<int:pk>',views.CollectionDelete.as_view(),name='collection-delete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)