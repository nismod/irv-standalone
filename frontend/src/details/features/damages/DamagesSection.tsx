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


type ModelParameters = Record<string, unknown>;

function getScenarioKey(parameters: ModelParameters) {
  return JSON.stringify(Object.entries(parameters).sort(([a], [b]) => a.localeCompare(b)));
}

function getScenarioLabel(parameters: ModelParameters) {
  return Object.entries(parameters).sort(([a], [b]) => a.localeCompare(b)).length
    ? JSON.stringify(Object.entries(parameters).sort(([a], [b]) => a.localeCompare(b)))
    : 'Default';
}

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
  scenarioKey: string;
  scenario: string;
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
    scenarioKey: getScenarioKey(parameters),
    scenario: getScenarioLabel(parameters),
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
  scenarioKey: string;
  scenario: string;
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
    scenarioKey: getScenarioKey(parameters),
    scenario: getScenarioLabel(parameters),
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

export const DamagesSection = ({ fd }) => {
  const damagesData = useOrderedDamages(prepareExpectedDamages(fd?.damages_expected ?? []));
  const returnPeriodDamagesData = useOrderedRPDamages(prepareRPDamages(fd?.damages_return_period ?? []));

  const hazards = useMemo(() => unique(damagesData.map((d) => d.hazard)), [damagesData]);
  const scenarios = useMemo(
    () => [...new Set(returnPeriodDamagesData.map((d) => d.scenarioKey))],
    [returnPeriodDamagesData],
  );
  const [selectedHazard, setSelectedHazard] = useSelect(hazards);
  const [selectedScenario, setSelectedScenario] = useSelect(scenarios);

  const selectedData = useMemo(
    () => (selectedHazard ? damagesData.filter((x) => x.hazard === selectedHazard) : null),
    [selectedHazard, damagesData],
  );
  const selectedRPData = useMemo(
    () =>
      selectedHazard
        ? returnPeriodDamagesData.filter(
            (x) => x.hazard === selectedHazard && x.scenarioKey === selectedScenario,
          )
        : null,
    [selectedHazard, selectedScenario, returnPeriodDamagesData],
  );

  const has_eael = useMemo(
    () => (selectedData ? selectedData.some((d) => d.eael_amax > 0) : null),
    [selectedData],
  );

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
        {selectedData ? (
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
        {scenarios.length ? (
          <FormControl fullWidth sx={{ my: 2 }} disabled={scenarios.length === 1}>
            <InputLabel id={`feature-${fd.id}-scenario`}>Model parameters</InputLabel>
            <Select
              labelId={`feature-${fd.id}-scenario`}
              value={selectedScenario ?? ''}
              onChange={(e) => setSelectedScenario(e.target.value as string)}
            >
              {scenarios.map((scenarioKey) => (
                <MenuItem key={scenarioKey} value={scenarioKey}>
                  {returnPeriodDamagesData.find((d) => d.scenarioKey === scenarioKey)?.scenario}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        ) : null}
        {selectedRPData ? (
          <>
            <Box mt={1}>
              <ReturnPeriodDamageChart
                data={{
                  table: selectedRPData,
                }}
                field_key="damage_mean"
                field_title="Damage (J$)"
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
