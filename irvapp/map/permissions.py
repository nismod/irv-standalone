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


class HasDatasetAccess(BasePermission):
    message = "You do not have permission to access this dataset."

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, "datasets"):
            self.message = (
                "You do not have permission to access this raster source."
            )
            if not request.user.is_authenticated:
                return False
            return obj.datasets.visible_to(request.user).exists()

        user_group_ids = set(
            request.user.groups.values_list("pk", flat=True)
        )
        return user_has_dataset_access(
            request.user,
            obj,
            user_group_ids=user_group_ids,
        )
