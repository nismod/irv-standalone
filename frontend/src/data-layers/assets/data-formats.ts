import { FieldSpec, FormatConfig } from 'lib/data-map/view-layers';
import { isNullish, numFormat, numFormatMoney, paren } from 'lib/helpers';
import startCase from 'lodash/startCase';

type HazardsMetadata = Record<string, { label: string }>;

function getSourceLabel(eadSource: string, hazardsMetadata) {
  if (eadSource === 'all') return 'All Hazards';

  return hazardsMetadata[eadSource].label;
}

function getDamageTypeLabel(field: string) {
  if (field === 'ead_mean') return 'Direct Damages';
  else if (field === 'eael_mean') return 'Economic Losses';
}

function formatDamageValue(value: number) {
  if (isNullish(value)) return value;

  return numFormatMoney(value);
}

const DAMAGES_EXPECTED_LEGEND_FORMAT: FormatConfig = {
  getDataLabel: ({ field }) => getDamageTypeLabel(field),
  getValueFormatted: formatDamageValue,
};

// ===== ADAPTATIONS FORMAT =====

const adaptationFieldLabels = {
  avoided_ead_mean: 'Avoided Direct Damages',
  avoided_eael_mean: 'Avoided Economic Losses',
  adaptation_cost: 'Adaptation Cost',
  cost_benefit_ratio: 'Cost Benefit Ratio',
};

function getAdaptationFieldLabel(field: string) {
  return adaptationFieldLabels[field] || startCase(field);
}

function formatAdaptationValue(value: number, { field }: FieldSpec) {
  if (isNullish(value)) return value;

  if (field === 'cost_benefit_ratio') {
    return `${numFormat(value)}x`;
  }

  return `$${numFormat(value)}`;
}

const ADAPTATION_DEFAULT_FORMAT: FormatConfig<number> = {
  getDataLabel: (colorField) => {
    return `${getAdaptationFieldLabel(colorField.field)} ${paren(
      String(colorField.fieldDimensions.adaptation_name),
    )}`;
  },
  getValueFormatted: formatAdaptationValue,
};

const ADAPTATION_LEGEND_FORMAT: FormatConfig = {
  getDataLabel: ({ field }) => getAdaptationFieldLabel(field),
  getValueFormatted: formatAdaptationValue,
};

// ==== ALL FORMATS ====

type FormatTarget = 'legend' | 'default';

export function createAssetDataFormats(
  hazardsMetadata: HazardsMetadata,
): Record<string, Record<FormatTarget, FormatConfig>> {
  return {
    damages_expected: {
      default: {
        getDataLabel: (colorField) => {
          const variableLabel = getDamageTypeLabel(colorField.field);
          const sourceLabel = getSourceLabel(
            String(colorField.fieldDimensions.hazard),
            hazardsMetadata,
          );

          return `${variableLabel} (${sourceLabel})`;
        },
        getValueFormatted: formatDamageValue,
      },
      legend: DAMAGES_EXPECTED_LEGEND_FORMAT,
    },
    adaptation: {
      default: ADAPTATION_DEFAULT_FORMAT,
      legend: ADAPTATION_LEGEND_FORMAT,
    },
  };
}

export function getAssetDataFormats(fieldSpec: FieldSpec, hazardsMetadata: HazardsMetadata): FormatConfig {
  const dataFormats = createAssetDataFormats(hazardsMetadata);
  return dataFormats[fieldSpec.fieldGroup].default;
}

export function getAssetLegendDataFormats(fieldSpec: FieldSpec, hazardsMetadata: HazardsMetadata): FormatConfig {
  const dataFormats = createAssetDataFormats(hazardsMetadata);
  return dataFormats[fieldSpec.fieldGroup].legend;
}
