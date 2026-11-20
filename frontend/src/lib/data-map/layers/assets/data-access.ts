import { DataLoader } from 'lib/data-loader/data-loader';
import { dataLoaderManager } from 'lib/data-loader/data-loader-manager';
import { FieldSpec } from 'lib/data-map/view-layers';
import { featureProperty } from 'lib/deck/props/data-source';
import { Accessor, withTriggers } from 'lib/deck/props/getters';
import { getFeatureId } from 'lib/deck/utils/get-feature-id';

type ModelParameters = Record<string, string | number | boolean | null>;

/**
 * Decorate a data access function with update triggers.
 * @param fn data access function
 * @param dataLoader data loader
 * @returns fn with additional properties; fn.updateTriggers and fn.dataLoader.
 */
function withLoaderTriggers(fn: Accessor<unknown>, dataLoader: DataLoader) {
  fn.dataLoader = dataLoader;
  return withTriggers(fn, [dataLoader.id, dataLoader.updateTrigger]);
}

/**
 * Generate a data accessor for a given asset layer and field spec.
 * Defaults to feature.property[field].
 * @param layer layer ID
 * @param fieldSpec field specification
 * @returns a data accessor for a given layer and field spec.
 */
export function getAssetDataAccessor(layer: string, fieldSpec: FieldSpec): Accessor<unknown> {
  if (fieldSpec == null) return null;

  const { fieldGroup, fieldDimensions, field } = fieldSpec;

  if (fieldGroup === 'damages_expected') {
    const { parameters } = fieldDimensions as {
      hazard: string;
      parameters: ModelParameters;
    };
    if (!parameters) return () => null;

    const dataLoader = dataLoaderManager.getDataLoader(layer, fieldSpec);
    return withLoaderTriggers((f) => dataLoader.getData(getFeatureId(f)), dataLoader);
  } else if (fieldGroup === 'damages_return_period') {
    // return return period damages dynamically loaded from API
    const dataLoader = dataLoaderManager.getDataLoader(layer, fieldSpec);
    return withLoaderTriggers((f) => dataLoader.getData(getFeatureId(f)), dataLoader);
  } else if (fieldGroup === 'adaptation') {
    const dataLoader = dataLoaderManager.getDataLoader(layer, fieldSpec);
    return withLoaderTriggers((f) => dataLoader.getData(getFeatureId(f)), dataLoader);
  } else if (fieldGroup === 'protected_features') {
    const dataLoader = dataLoaderManager.getDataLoader(layer, fieldSpec);
    return withLoaderTriggers((f) => dataLoader.getData(getFeatureId(f)), dataLoader);
  } else {
    // field other than damages - use field name as key
    return featureProperty(field);
  }
}

/**
 * Generate a data accessor function for a given asset layer.
 * @param layer the layer ID.
 * @returns a function which takes a field spec and returns a data accessor.
 */
export function assetDataAccessFunction(layer: string) {
  return (fieldSpec: FieldSpec) => getAssetDataAccessor(layer, fieldSpec);
}
