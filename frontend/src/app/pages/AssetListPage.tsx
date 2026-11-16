import { useState } from 'react';
import { Box, Stack, TableCell, Typography } from '@mui/material';
import { useAtom, useAtomValue } from 'jotai';

import { mapViewConfig } from 'lib/state/map-view/map-view-config';
import { FieldSpec } from 'lib/data-map/view-layers';

import { FieldSpecControl } from 'lib/asset-list/FieldSpecControl';
import { SortedAssetTable } from 'lib/asset-list/SortedAssetTable';
import { LayerSpec, ListFeature } from 'lib/asset-list/use-sorted-features';
import { ExpandableRow } from 'lib/asset-list/ExpandableRow';
import { FeatureSidebarContent } from 'details/features/FeatureSidebarContent';
import { getAssetDataFormats } from 'data-layers/assets/data-formats';
import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';
import {
  modelParametersState,
  scenarioCatalogState,
  scenarioQueryKey,
} from 'lib/model-scenarios/state';
import {
  ModelScenario,
  ModelType,
  scenarioDimensions,
  scenariosForHazard,
  selectResult,
} from 'lib/model-scenarios/scenarios';

export const AssetListPage = () => {
  const hazardsMetadata = useAtomValue(hazardsMetadataState);
  const [layerSpec] = useState<LayerSpec>({
    sector: 'power',
    subsector: 'transmission',
    asset_type: 'High Voltage',
  });

  const [model, setModel] = useState<ModelType>('damages_expected');
  const [requestedHazard, setHazard] = useState('all');
  const [dimensions, setDimensions] = useState<Partial<ModelScenario>>({ protection_standard: 0 });
  const [parameters, setParameters] = useAtom(modelParametersState(model));
  const catalog = useAtomValue(scenarioCatalogState(scenarioQueryKey(model, layerSpec)));
  const availableHazards = [...new Set(catalog?.rows.map((row) => row.hazard) ?? [])];
  const hazards = model === 'damages_expected' ? ['all', ...availableHazards] : availableHazards;
  const hazard = hazards.includes(requestedHazard) ? requestedHazard : hazards[0];
  const rows = scenariosForHazard(catalog?.rows ?? [], hazard);
  const preferredDimensions =
    model === 'damages_expected'
      ? { protection_standard: dimensions.protection_standard ?? 0 }
      : Object.fromEntries(
          Object.entries(dimensions).filter(([name]) => name.startsWith('adaptation_')),
        );
  const result = selectResult(rows, parameters, preferredDimensions);
  const selectedFieldSpec: FieldSpec | null = result
    ? {
        fieldGroup: model,
        fieldDimensions: scenarioDimensions(result),
        field: model === 'damages_expected' ? 'ead_mean' : 'avoided_ead_mean',
        fieldParams: {},
      }
    : null;

  const currency = useAtomValue(mapViewConfig).app.currency;
  const fieldSpec: FieldSpec | null = selectedFieldSpec ? {
    ...selectedFieldSpec,
    unit: selectedFieldSpec.field === 'cost_benefit_ratio'
      ? undefined
      : `${currency}${['eael_mean', 'avoided_eael_mean'].includes(selectedFieldSpec.field) ? '/day' : ''}`,
  } : null;

  const [selectedFeature, setSelectedFeature] = useState<ListFeature>(null);

  const formats = fieldSpec ? getAssetDataFormats(fieldSpec, hazardsMetadata) : null;

  return (
    <>
      <article>
        <Stack spacing={2}>
          <Typography variant="h4">Asset list</Typography>
          <Box>
            <Typography variant="h6">Choose variable to sort assets by</Typography>

            <FieldSpecControl
              model={model}
              onModelChange={setModel}
              hazards={hazards}
              hazard={hazard}
              onHazardChange={setHazard}
              rows={catalog ? rows : undefined}
              result={result}
              onParametersChange={setParameters}
              error={catalog?.error}
              onDimensionChange={(next) => setDimensions((previous) => ({ ...previous, ...next }))}
            />
          </Box>
          {fieldSpec && (
            <SortedAssetTable
              layerSpec={layerSpec}
              fieldSpec={fieldSpec}
              header={
                <>
                  <TableCell>#</TableCell>
                  <TableCell>Asset ID</TableCell>
                  <TableCell>{formats.getDataLabel(fieldSpec)}</TableCell>
                </>
              }
              renderRow={(feature, localIndex, globalIndex) => (
                <ExpandableRow
                  key={feature.string_id}
                  expanded={selectedFeature === feature}
                  onExpandedChange={(newExpanded) =>
                    setSelectedFeature(newExpanded ? feature : null)
                  }
                  expandableContent={
                    <>
                      <FeatureSidebarContent
                        feature={{ id: feature.id }}
                        assetType={feature.layer}
                      />
                    </>
                  }
                >
                  <TableCell>{globalIndex + 1}</TableCell>
                  <TableCell>{feature.string_id}</TableCell>
                  <TableCell>{formats.getValueFormatted(feature.value, fieldSpec)}</TableCell>
                </ExpandableRow>
              )}
            />
          )}
        </Stack>
      </article>
    </>
  );
};
