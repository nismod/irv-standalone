from rest_framework.permissions import BasePermission


def _coerce_dataset_instance(dataset):
    if not isinstance(dataset, dict):
        return dataset

    dataset_id = dataset.get("id")
    if dataset_id is None:
        return None

    from .models import Dataset

    return Dataset.objects.prefetch_related("access_groups").filter(
        pk=dataset_id
    ).first()


def user_has_dataset_access(user, dataset, user_group_ids=None):
    dataset = _coerce_dataset_instance(dataset)

    if dataset is None or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True

    if user_group_ids is not None:
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

        return user_has_dataset_access(request.user, obj)
