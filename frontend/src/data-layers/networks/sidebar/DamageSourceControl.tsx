import {
  FormControl,
  FormControlLabel,
  FormLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
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
import { ParamDropdown } from 'lib/controls/ParamDropdown';
import {
  damageScenarioSyncState,
  damageSourceStateEffect,
} from 'app/state/damage-mapping/damage-map';
import { LayerStylePanel } from 'lib/sidebar/ui/LayerStylePanel';

import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';

export const DamageSourceControl = () => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  const {
    catalog,
    hazards,
    hazard: damageSource,
    rows,
    result,
  } = useAtomValue(damageScenarioState);
  const [requestedSource, setDamageSource] = useAtom(damageSourceState);
  const setParameters = useSetAtom(modelParametersState('damages_expected'));
  const setProtection = useSetAtom(damageProtectionStandardState);
  const [damageType, setDamageType] = useAtom(damageTypeState);
  const id = useId();

  useEffect(() => {
    if (catalog && requestedSource != null && requestedSource !== damageSource)
      setDamageSource(damageSource);
  }, [catalog, requestedSource, damageSource, setDamageSource]);

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
            <FormLabel component="legend">Hazard</FormLabel>
            <RadioGroup value={damageSource} onChange={(e, value) => setDamageSource(value)}>
              <FormControlLabel label="All Hazards" control={<Radio value="all" />} />
              {hazards.map((hazard) => (
                <FormControlLabel
                  key={hazard}
                  label={HAZARDS_METADATA[hazard]?.label ?? hazard}
                  disabled={HAZARDS_METADATA[hazard]?.has_access === false}
                  control={<Radio value={hazard} />}
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
            error={catalog?.error}
            emptyMessage={
              damageSource === 'all' && hazards.length > 0
                ? 'No compatible combination is available across all hazards. Choose a hazard.'
                : undefined
            }
          />
          {protectionLevels.length > 1 && (
            <ParamDropdown<number>
              title="Protection standard"
              value={result.protection_standard}
              options={protectionLevels}
              onChange={setProtection}
            />
          )}
        </InputSection>
      </LayerStylePanel>
    </>
  );
};
