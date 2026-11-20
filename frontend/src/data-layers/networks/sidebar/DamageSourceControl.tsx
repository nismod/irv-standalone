import {
  FormControl,
  FormControlLabel,
  RadioGroup,
  FormLabel,
  MenuItem,
  Radio,
  Select,
  FormHelperText,
} from '@mui/material';
import { useEffect, useId } from 'react';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';

import { StateEffectRoot } from 'lib/recoil/state-effects/StateEffectRoot';
import { InputSection } from 'lib/sidebar/ui/InputSection';
import {
  damageSourceState,
  damageTypeState,
  damageProtectionStandardState,
} from 'lib/state/damage-map';
import { damageScenarioState } from '../state/damage-scenarios';
import { modelParametersState } from 'lib/model-scenarios/state';
import { ModelParameterControls } from 'lib/model-scenarios/ModelParameterControls';
import { parameterKey } from 'lib/model-scenarios/scenarios';
import {
  ModelParameterControl,
  type NumericControl,
} from 'lib/model-scenarios/ModelParameterControl';
import {
  damageScenarioSyncState,
  damageSourceStateEffect,
  damageRasterReturnPeriodsState,
} from 'app/state/damage-mapping/damage-map';
import { LayerStylePanel } from 'lib/sidebar/ui/LayerStylePanel';

import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';

export const DamageSourceControl = ({
  numericControl = 'select',
}: {
  numericControl?: NumericControl;
}) => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  const { catalog, hazards, selectedHazards, rows, result } = useAtomValue(damageScenarioState);
  const [requestedSource, setDamageSource] = useAtom(damageSourceState);
  const setParameters = useSetAtom(modelParametersState('damages_expected'));
  const setProtection = useSetAtom(damageProtectionStandardState);
  const [damageType, setDamageType] = useAtom(damageTypeState);
  const id = useId();
  const returnPeriods = useAtomValue(damageRasterReturnPeriodsState);
  const periodGroups = new Map<string, { hazards: string[]; value: number; options: number[] }>();
  for (const { hazard, value, options } of returnPeriods) {
    const key = JSON.stringify([value, options]);
    const group = periodGroups.get(key) ?? { hazards: [], value, options };
    group.hazards.push(HAZARDS_METADATA[hazard]?.label ?? hazard);
    periodGroups.set(key, group);
  }

  useEffect(() => {
    if (
      catalog &&
      requestedSource !== 'all' &&
      (requestedSource.length !== selectedHazards.length ||
        requestedSource.some((hazard) => !selectedHazards.includes(hazard)))
    )
      setDamageSource(selectedHazards);
  }, [catalog, requestedSource, selectedHazards, setDamageSource]);

  const allSelected = hazards.length > 0 && selectedHazards.length === hazards.length;
  const selectedSource =
    requestedSource === 'all'
      ? 'all'
      : selectedHazards.length === 1
        ? selectedHazards[0]
        : allSelected
          ? 'all'
          : '';

  const protectionLevels = [
    ...new Set(
      rows
        .filter((row) => result && parameterKey(row.parameters) === parameterKey(result.parameters))
        .map((row) => row.protection_standard),
    ),
  ];

  return (
    <>
      <StateEffectRoot state={damageScenarioSyncState} effect={damageSourceStateEffect} />
      <LayerStylePanel>
        <InputSection>
          <FormControl fullWidth>
            <FormLabel id={`${id}-damage-type`}>Damage type</FormLabel>
            <Select<string>
              labelId={`${id}-damage-type`}
              variant="standard"
              value={damageType}
              onChange={(e) => setDamageType(e.target.value)}
            >
              <MenuItem value="direct">Direct Damages</MenuItem>
              <MenuItem value="indirect">Economic Losses</MenuItem>
            </Select>
          </FormControl>
        </InputSection>
        <InputSection>
          <FormControl component="fieldset" fullWidth>
            <FormLabel component="legend" id={`${id}-hazard`}>
              Hazard
            </FormLabel>
            <RadioGroup
              aria-labelledby={`${id}-hazard`}
              name={`${id}-hazard`}
              value={selectedSource}
              onChange={(_event, value) => setDamageSource(value === 'all' ? 'all' : [value])}
            >
              <FormControlLabel
                label="All Hazards"
                value="all"
                disabled={!hazards.length}
                control={<Radio />}
              />
              {hazards.map((hazard) => (
                <FormControlLabel
                  key={hazard}
                  label={HAZARDS_METADATA[hazard]?.label ?? hazard}
                  value={hazard}
                  disabled={HAZARDS_METADATA[hazard]?.has_access === false}
                  control={<Radio />}
                />
              ))}
            </RadioGroup>
          </FormControl>
        </InputSection>
        <InputSection>
          <ModelParameterControls
            rows={catalog ? rows : undefined}
            parameters={result?.parameters ?? null}
            onChange={setParameters}
            numericControl={numericControl}
            error={catalog?.error}
            emptyMessage={
              hazards.length > 0
                ? selectedHazards.length === 0
                  ? 'Select at least one hazard.'
                  : 'No compatible combination is available for the selected hazards.'
                : undefined
            }
          />
          {protectionLevels.length > 1 && (
            <ModelParameterControl
              title="Protection standard"
              value={result.protection_standard}
              options={protectionLevels}
              onChange={setProtection}
              numericControl={numericControl}
            />
          )}
          {periodGroups.size > 0 && (
            <>
              {[...periodGroups].map(([key, { hazards: labels, value, options }]) => (
                <ModelParameterControl
                  key={key}
                  title={
                    periodGroups.size === 1
                      ? 'Return period (years)'
                      : `${labels.join(' + ')} return period (years)`
                  }
                  value={value}
                  options={options}
                  onChange={() => undefined}
                  numericControl={numericControl}
                  disabled
                />
              ))}
              <FormHelperText>
                Fixed to the maximum available for the matching hazard maps. Damage values are
                expected annual estimates.
              </FormHelperText>
            </>
          )}
        </InputSection>
      </LayerStylePanel>
    </>
  );
};
