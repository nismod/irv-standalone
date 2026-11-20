from rest_framework.permissions import BasePermission


def _prefetched_access_group_ids(dataset):
    prefetched = getattr(dataset, "_prefetched_objects_cache", {})
    groups = prefetched.get("access_groups")
    if groups is None:
        return None
    return {group.pk for group in groups}


def _coerce_dataset_instance(dataset, *, prefetch_access_groups=False):
    if not isinstance(dataset, dict):
        return dataset

    dataset_id = dataset.get("id")
    if dataset_id is None:
        return None

    from .models import Dataset

    qs = Dataset.objects.all()
    if prefetch_access_groups:
        qs = qs.prefetch_related("access_groups")

    return qs.filter(pk=dataset_id).first()


def user_has_dataset_access(user, dataset, user_group_ids=None):
    dataset = _coerce_dataset_instance(
        dataset,
        prefetch_access_groups=user_group_ids is not None,
    )
    if dataset is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    if user_group_ids is not None:
        prefetched_group_ids = _prefetched_access_group_ids(dataset)
        if prefetched_group_ids is not None:
            return bool(prefetched_group_ids & set(user_group_ids))

        return any(
            group.pk in user_group_ids
            for group in dataset.access_groups.all()
        )

    return dataset.access_groups.filter(user=user).exists()


def accessible_feature_layers(user):
    from .models import Dataset, FeatureLayer

    if not user.is_authenticated:
        return FeatureLayer.objects.none()
    return FeatureLayer.objects.filter(dataset__in=Dataset.objects.visible_to(user))


class HasDatasetAccess(BasePermission):
    message = "You do not have permission to access this dataset."

    def has_object_permission(self, request, view, obj):
        from raster.models import RasterTileSource
        from .models import Dataset, FeatureLayer, RasterLayer

        if isinstance(obj, RasterTileSource):
            self.message = (
                "You do not have permission to access this raster source."
            )
            if not request.user.is_authenticated:
                return False
            return obj.raster_layers.filter(
                dataset__in=Dataset.objects.visible_to(request.user)
            ).exists()

        if isinstance(obj, (FeatureLayer, RasterLayer)):
            obj = obj.dataset if obj.dataset_id else None

        user_group_ids = set(
            request.user.groups.values_list("pk", flat=True)
        )
        return user_has_dataset_access(
            request.user,
            obj,
            user_group_ids=user_group_ids,
        )


def inaccessible_hazard_ids(user):
    """Known hazard datasets that this user cannot access.

    Result hazards without a raster catalogue entry are left available: a
    damage model does not require a matching raster dataset.
    """
    if user.is_superuser:
        return set()
    from .models import Dataset

    from .models import RasterLayer

    denied_layers = set(RasterLayer.objects.filter(dataset__group__iexact="hazards").exclude(
        dataset__in=Dataset.objects.visible_to(user),
    ).values_list("pk", flat=True))
    denied_unlinked = set(Dataset.objects.filter(group__iexact="hazards", raster_layers__isnull=True).exclude(
        pk__in=Dataset.objects.visible_to(user),
    ).values_list("pk", flat=True))
    return denied_layers | denied_unlinked
