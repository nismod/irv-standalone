import Download from '@mui/icons-material/Download';
import { FormControl, InputLabel, IconButton, MenuItem, Select, Typography } from '@mui/material';
import { Box } from '@mui/system';
import { DamagesExpected, DamagesRp } from 'lib/api-client';
import { downloadFile, titleCase, unique } from 'lib/helpers';
import { useSelect } from 'lib/hooks/use-select';
import { useMemo } from 'react';
import { DamageTable } from './DamageTable';
import { RPDamageTable } from './RPDamageTable';
import { ExpectedDamageChart } from './ExpectedDamageChart';
import { ReturnPeriodDamageChart } from './ReturnPeriodDamageChart';
import { parameterLabel } from './parameter-labels';
import {
  expectedDamageDimensions,
  returnPeriodDimensions,
  parameterField,
  parameterNames,
  parameterOptions,
  parameterSelectionKey,
  parameterTitle,
} from './chart-parameters';


type ModelParameters = Record<string, unknown>;

function csvCell(value: unknown) {
  const text = value == null
    ? ''
    : typeof value === 'object'
      ? JSON.stringify(value)
      : String(value);
  return `"${text.replaceAll('"', '""')}"`;
}

function csv(rows: unknown[][]) {
  return rows.map((row) => row.map(csvCell).join(',')).join('\n');
}

interface ExpectedDamageCell {
  key: string;
  hazard: string;
  parameters: ModelParameters;
  ead_mean: number;
  ead_amin: number;
  ead_amax: number;
  eael_mean: number;
  eael_amin: number;
  eael_amax: number;
}
function getExpectedDamageObject(d: DamagesExpected): ExpectedDamageCell {
  const parameters = d.parameters as Record<string, unknown>;
  return {
    key: `${d.hazard}__${JSON.stringify(parameters)}`,
    hazard: d.hazard,
    parameters,
    ead_mean: d.ead_mean,
    ead_amin: d.ead_amin,
    ead_amax: d.ead_amax,
    eael_mean: d.eael_mean,
    eael_amin: d.eael_amin,
    eael_amax: d.eael_amax,
  };
}

interface RPDamageCell {
  key: string;
  hazard: string;
  parameters: ModelParameters;
  rp: number;
  probability: number;
  damage_mean: number;
  damage_amin: number;
  damage_amax: number;
  loss_mean: number;
  loss_amin: number;
  loss_amax: number;
}

function getRPDamageObject(d: DamagesRp): RPDamageCell {
  const parameters = d.parameters as Record<string, unknown>;
  return {
    key: `${d.hazard}__${JSON.stringify(parameters)}__rp_${d.rp}`,
    hazard: d.hazard,
    parameters,
    rp: d.rp,
    probability: 1 / d.rp,
    damage_mean: d.damage_mean,
    damage_amin: d.damage_amin,
    damage_amax: d.damage_amax,
    loss_mean: d.loss_mean,
    loss_amin: d.loss_amin,
    loss_amax: d.loss_amax,
  };
}

function prepareExpectedDamages(expectedDamages: DamagesExpected[]) {
  return expectedDamages.filter((d) => d.protection_standard === 0).map(getExpectedDamageObject);
}

function prepareRPDamages(rpDamages: DamagesRp[]) {
  return rpDamages.map(getRPDamageObject);
}

function useOrderedDamages(damages: ExpectedDamageCell[]) {
  return useMemo(
    () => [...damages].sort((a, b) => a.hazard.localeCompare(b.hazard) || a.key.localeCompare(b.key)),
    [damages],
  );
}

function useOrderedRPDamages(damages: RPDamageCell[]) {
  return useMemo(
    () => [...damages].sort((a, b) => a.hazard.localeCompare(b.hazard) || a.key.localeCompare(b.key)),
    [damages],
  );
}

function makeDamagesCsv(damages: ExpectedDamageCell[]) {
  const parameterNames = unique(damages.flatMap((damage) => Object.keys(damage.parameters)));
  return csv([
    ['hazard', ...parameterNames, 'ead_mean', 'ead_amin', 'ead_amax', 'eael_mean', 'eael_amin', 'eael_amax'],
    ...damages.map((d) => [d.hazard, ...parameterNames.map((name) => d.parameters[name]), d.ead_mean, d.ead_amin, d.ead_amax, d.eael_mean, d.eael_amin, d.eael_amax]),
  ]);
}

function makeRPDamagesCsv(damages: RPDamageCell[]) {
  const parameterNames = unique(damages.flatMap((damage) => Object.keys(damage.parameters)));
  return csv([
    ['hazard', ...parameterNames, 'rp', 'damage_mean', 'damage_amin', 'damage_amax', 'loss_mean', 'loss_amin', 'loss_amax'],
    ...damages.map((d) => [d.hazard, ...parameterNames.map((name) => d.parameters[name]), d.rp, d.damage_mean, d.damage_amin, d.damage_amax, d.loss_mean, d.loss_amin, d.loss_amax]),
  ]);
}

function ParameterSelector({ id, names, options, value, onChange }: {
  id: string;
  names: string[];
  options: { key: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  if (!names.length || !options.length) return null;
  return (
    <FormControl fullWidth sx={{ my: 2 }} disabled={options.length === 1}>
      <InputLabel id={id}>{parameterTitle(names)}</InputLabel>
      <Select
        labelId={id}
        value={value ?? ''}
        onChange={(event) => onChange(event.target.value)}
      >
        {options.map((option) => (
          <MenuItem key={option.key} value={option.key}>{option.label}</MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export const DamagesSection = ({ fd }) => {
  const damagesData = useOrderedDamages(prepareExpectedDamages(fd?.damages_expected ?? []));
  const returnPeriodDamagesData = useOrderedRPDamages(prepareRPDamages(fd?.damages_return_period ?? []));

  const hazards = useMemo(
    () => unique([...damagesData, ...returnPeriodDamagesData].map((d) => d.hazard)),
    [damagesData, returnPeriodDamagesData],
  );
  const [selectedHazard, setSelectedHazard] = useSelect(hazards);
  const hazardRPData = useMemo(
    () => returnPeriodDamagesData.filter((d) => d.hazard === selectedHazard),
    [returnPeriodDamagesData, selectedHazard],
  );
  const hazardExpectedData = useMemo(
    () => damagesData.filter((x) => x.hazard === selectedHazard),
    [selectedHazard, damagesData],
  );
  const expectedDimensions = expectedDamageDimensions(hazardExpectedData);
  const expectedOptions = parameterOptions(hazardExpectedData, expectedDimensions.selectors);
  const [expectedSelection, setExpectedSelection] = useSelect(expectedOptions.map((option) => option.key));
  const selectedData = hazardExpectedData.filter(
    (row) => parameterSelectionKey(row, expectedDimensions.selectors) === expectedSelection,
  );
  const rpDimensions = returnPeriodDimensions(hazardRPData);
  const rpOptions = parameterOptions(hazardRPData, rpDimensions.selectors);
  const [rpSelection, setRPSelection] = useSelect(rpOptions.map((option) => option.key));
  const selectedRPData = hazardRPData.filter(
    (row) => parameterSelectionKey(row, rpDimensions.selectors) === rpSelection,
  );
  const expectedTooltipFields = parameterNames(hazardExpectedData).map(parameterField);
  const rpTooltipFields = [...parameterNames(hazardRPData).map(parameterField), 'rp'];

  const has_eael = selectedData.some((d) => d.eael_amax > 0);

  return (
    <>
      <Box py={2}>
        <Box position="relative">
          <Typography variant="h6" component="h2">
            Risk
          </Typography>
          <IconButton
            sx={{
              position: 'absolute',
              top: 0,
              right: 0,
            }}
            title="Download CSV with damages data"
            onClick={() =>
              downloadFile(makeDamagesCsv(damagesData), 'text/csv', `feature_${fd.id}_damages.csv`)
            }
          >
            <Download />
          </IconButton>
        </Box>
        {hazards.length ? (
          <FormControl fullWidth sx={{ my: 2 }} disabled={hazards.length === 1}>
            <InputLabel id={`feature-${fd.id}-hazard`}>Hazard</InputLabel>
            <Select
              labelId={`feature-${fd.id}-hazard`}
              value={selectedHazard ?? ''}
              onChange={(e) => setSelectedHazard(e.target.value as string)}
            >
              {hazards.map((h) => (
                <MenuItem key={h} value={h}>
                  {titleCase(h)}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        ) : null}
        <ParameterSelector
          id={`feature-${fd.id}-expected-parameters`}
          names={expectedDimensions.selectors}
          options={expectedOptions}
          value={expectedSelection}
          onChange={setExpectedSelection}
        />
        {selectedData.length ? (
          <>
            <Box mt={1}>
              <Typography component="h3" variant="subtitle2">
                Expected Annual Damages
              </Typography>
              <ExpectedDamageChart
                data={{
                  table: selectedData,
                }}
                field="ead_mean"
                field_min="ead_amin"
                field_max="ead_amax"
                field_title="EAD (J$)"
                xField={expectedDimensions.x ? parameterField(expectedDimensions.x) : 'hazard'}
                xTitle={expectedDimensions.x ? parameterLabel(expectedDimensions.x) : null}
                seriesField={expectedDimensions.series ? parameterField(expectedDimensions.series) : undefined}
                seriesTitle={expectedDimensions.series ? parameterLabel(expectedDimensions.series) : null}
                tooltipFields={expectedTooltipFields}
                actions={false}
                width={280} // this is currently picked to fit the chart to the sidebar width
                height={170}
                renderer="svg"
              />
            </Box>
            {has_eael ? (
              <Box mt={1}>
                <Typography component="h3" variant="subtitle2">
                  Expected Annual Economic Losses
                </Typography>
                <ExpectedDamageChart
                  data={{
                    table: selectedData,
                  }}
                  field="eael_mean"
                  field_min="eael_amin"
                  field_max="eael_amax"
                  field_title="EAEL (J$/day)"
                  xField={expectedDimensions.x ? parameterField(expectedDimensions.x) : 'hazard'}
                  xTitle={expectedDimensions.x ? parameterLabel(expectedDimensions.x) : null}
                  seriesField={expectedDimensions.series ? parameterField(expectedDimensions.series) : undefined}
                  seriesTitle={expectedDimensions.series ? parameterLabel(expectedDimensions.series) : null}
                  tooltipFields={expectedTooltipFields}
                  actions={false}
                  width={280} // this is currently picked to fit the chart to the sidebar width
                  height={170}
                  renderer="svg"
                />
              </Box>
            ) : null}
            <Box mt={1}>
              <DamageTable damages={selectedData} />
            </Box>
          </>
        ) : (
          <Typography variant="body2" color="textSecondary">
            No direct damages or indirect losses estimated.
          </Typography>
        )}
      </Box>
      <Box py={2}>
        <Box position="relative">
          <Typography variant="h6" component="h2">
            Return Period Damages
          </Typography>
          <IconButton
            sx={{
              position: 'absolute',
              top: 0,
              right: 0,
            }}
            title="Download CSV with return period data"
            onClick={() =>
              downloadFile(
                makeRPDamagesCsv(returnPeriodDamagesData),
                'text/csv',
                `feature_${fd.id}_damages_rp.csv`,
              )
            }
          >
            <Download />
          </IconButton>
        </Box>
        <ParameterSelector
          id={`feature-${fd.id}-rp-parameters`}
          names={rpDimensions.selectors}
          options={rpOptions}
          value={rpSelection}
          onChange={setRPSelection}
        />
        {selectedRPData.length ? (
          <>
            <Box mt={1}>
              <ReturnPeriodDamageChart
                data={{
                  table: selectedRPData,
                }}
                field_key="damage_mean"
                field_title="Damage (J$)"
                seriesField={rpDimensions.series ? parameterField(rpDimensions.series) : undefined}
                seriesTitle={rpDimensions.series ? parameterLabel(rpDimensions.series) : null}
                tooltipFields={rpTooltipFields}
                actions={false}
                width={280} // this is currently picked to fit the chart to the sidebar width
                height={130}
                renderer="svg"
              />
            </Box>
            <Box mt={1}>
              <RPDamageTable damages={selectedRPData} />
            </Box>
          </>
        ) : (
          <Typography variant="body2" color="textSecondary">
            No direct damages or indirect losses estimated.
          </Typography>
        )}
      </Box>
    </>
  );
};
