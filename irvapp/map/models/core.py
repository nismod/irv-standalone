from django.contrib.gis.db import models
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from tree_queries.models import OrderableTreeNode, TreeQuerySet


class MapConfig(models.Model):
    config_name = models.CharField(primary_key=True)
    config_value = models.CharField()
    config_type = models.CharField(
        choices=[
            ("number", "Number"),
            ("string", "String"),
            ("boolean", "Boolean"),
        ],
        default='number'
    )

    class Meta:
        db_table = "map_config"


class InfrastructureNode(OrderableTreeNode):
    node_id = models.CharField(primary_key=True)
    node_name = models.CharField()
    feature_layer = models.OneToOneField(
        "FeatureLayer", on_delete=models.PROTECT, null=True, blank=True,
        related_name="infrastructure_node",
    )
    objects = TreeQuerySet.as_manager(with_tree_fields=True)

    class Meta(OrderableTreeNode.Meta):
        db_table = "infrastructure_nodes"

    def __str__(self):
        return self.node_id

    def clean(self):
        super().clean()
        if self.feature_layer_id and self.pk and self.children.exists():
            raise ValidationError({"feature_layer": "Only leaf nodes can have a feature layer."})
        if self.parent_id and self.parent.feature_layer_id:
            raise ValidationError({"parent": "A node with a feature layer cannot have children."})


class LayerOrdering(models.Model):
    """Ordering shared by raster and feature layers."""

    stacking_order = models.IntegerField()
    display_order = models.IntegerField()

    class Meta:
        abstract = True


class LayerIdentity(models.Model):
    """A globally unique identity belonging to one kind of layer."""

    id = models.CharField(primary_key=True)
    kind = models.CharField(max_length=16, choices=[("feature", "Feature"), ("raster", "Raster")])
    dataset = models.ForeignKey(
        "Dataset", models.PROTECT, null=True, blank=True, related_name="layer_identities",
    )

    class Meta:
        db_table = "layer_identities"
        constraints = [models.UniqueConstraint(fields=["id", "kind"], name="layer_identity_id_kind_unique")]

    def __str__(self):
        return self.id

    def clean(self):
        super().clean()
        if not self.pk:
            return
        alias = self._state.db or "default"
        current_kind = type(self).objects.using(alias).filter(pk=self.pk).values_list("kind", flat=True).first()
        if current_kind is None or current_kind == self.kind:
            return
        if (FeatureLayer.objects.using(alias).filter(pk=self.pk).exists() or
                RasterLayer.objects.using(alias).filter(pk=self.pk).exists()):
            raise ValidationError({"kind": "Cannot change the type while a layer is attached."})


class IdentityLayer(models.Model):
    identity = models.OneToOneField(
        LayerIdentity, models.PROTECT, primary_key=True, related_name="%(class)s",
    )

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if not self.identity_id:
            return
        try:
            identity = self.identity
        except LayerIdentity.DoesNotExist:
            return
        if identity.kind != self.identity_kind:
            raise ValidationError({"identity": f"Choose a {self.identity_kind} layer identity."})

    def save(self, *args, **kwargs):
        if self.identity_id is None:
            raise ValueError("A layer ID is required")
        alias = kwargs.get("using") or self._state.db or "default"
        with transaction.atomic(using=alias):
            identity, _ = LayerIdentity.objects.using(alias).get_or_create(
                pk=self.identity_id, defaults={"kind": self.identity_kind},
            )
            if identity.kind != self.identity_kind:
                raise IntegrityError(f"Layer ID {self.identity_id!r} belongs to {identity.kind}")
            return super().save(*args, **kwargs)


class FeatureLayer(IdentityLayer, LayerOrdering):
    identity = models.OneToOneField(
        LayerIdentity, models.PROTECT, primary_key=True, db_column="layer_name", related_name="featurelayer",
    )
    identity_kind = models.CharField(max_length=16, default="feature", db_default="feature", editable=False)
    sector = models.CharField()
    subsector = models.CharField()
    asset_type = models.CharField()
    stacking_order = models.IntegerField(default=0, db_default=0)
    display_order = models.IntegerField(default=0, db_default=0)

    class Meta:
        db_table = "feature_layers"
        constraints = [models.CheckConstraint(condition=models.Q(identity_kind="feature"), name="feature_layer_identity_kind")]

    def __init__(self, *args, **kwargs):
        if "layer_name" in kwargs:
            kwargs["identity_id"] = kwargs.pop("layer_name")
        super().__init__(*args, **kwargs)

    @property
    def layer_name(self):
        return self.pk


class NetworkLayerStyle(models.Model):
    layer_id = models.CharField(primary_key=True)
    label = models.CharField()
    style_type = models.CharField()
    color = models.CharField(max_length=64)
    min_zoom = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = "network_layer_styles"
        ordering = ["layer_id"]


class Feature(models.Model):
    string_id = models.CharField()
    layer = models.ForeignKey(
        FeatureLayer,
        models.CASCADE,
        db_column="layer",
    )
    sublayer = models.CharField(blank=True, null=True)
    properties = models.JSONField()
    geom = models.GeometryField()

    class Meta:
        db_table = "features"
        indexes = [models.Index(fields=["layer", "id"], name="features_layer_id_idx")]


class DatasetQuerySet(models.QuerySet):
    def visible_to(self, user):
        if user.is_superuser:
            return self

        return self.filter(
            access_groups__in=user.groups.all()
        ).distinct()


class Dataset(models.Model):
    id = models.CharField(primary_key=True)
    label = models.CharField()
    group = models.CharField()
    license = models.CharField(max_length=255, blank=True, null=True)
    access_groups = models.ManyToManyField(
        "auth.Group",
        blank=True,
        related_name="datasets",
    )

    objects = DatasetQuerySet.as_manager()

    class Meta:
        db_table = "datasets"


class RasterLayer(IdentityLayer, LayerOrdering):
    identity = models.OneToOneField(
        LayerIdentity, models.PROTECT, primary_key=True, db_column="id", related_name="rasterlayer",
    )
    identity_kind = models.CharField(max_length=16, default="raster", db_default="raster", editable=False)
    tile_source = models.ForeignKey(
        "raster.RasterTileSource", models.PROTECT, related_name="raster_layers"
    )
    label = models.CharField()
    quantity = models.CharField()
    unit = models.CharField()
    license = models.CharField(max_length=255, blank=True, null=True)
    color_scheme = models.CharField(max_length=255, blank=True, null=True)
    color_range = models.JSONField(blank=True, null=True)
    class Meta:
        db_table = "raster_layers"
        constraints = [models.CheckConstraint(condition=models.Q(identity_kind="raster"), name="raster_layer_identity_kind")]

    def __init__(self, *args, **kwargs):
        if "id" in kwargs:
            kwargs["identity_id"] = kwargs.pop("id")
        super().__init__(*args, **kwargs)

    @property
    def id(self):
        return self.pk
