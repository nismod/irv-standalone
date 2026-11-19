import {
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  MenuItem,
  Checkbox,
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
import { ModelParameterControl, type NumericControl } from 'lib/model-scenarios/ModelParameterControl';
import {
  damageScenarioSyncState,
  damageSourceStateEffect,
} from 'app/state/damage-mapping/damage-map';
import { LayerStylePanel } from 'lib/sidebar/ui/LayerStylePanel';

import { hazardsMetadataState } from 'data-layers/hazards/state/metadata';

export const DamageSourceControl = ({ numericControl = 'select' }: { numericControl?: NumericControl }) => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  const { catalog, hazards, selectedHazards, rows, result } = useAtomValue(damageScenarioState);
  const [requestedSource, setDamageSource] = useAtom(damageSourceState);
  const setParameters = useSetAtom(modelParametersState('damages_expected'));
  const setProtection = useSetAtom(damageProtectionStandardState);
  const [damageType, setDamageType] = useAtom(damageTypeState);
  const id = useId();

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
  const partiallySelected = selectedHazards.length > 0 && !allSelected;

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
            <FormLabel component="legend">Hazards</FormLabel>
            <FormGroup>
              <FormControlLabel
                label="All Hazards"
                control={
                  <Checkbox
                    checked={allSelected}
                    indeterminate={partiallySelected}
                    disabled={!hazards.length}
                    slotProps={{
                      input: { 'aria-checked': partiallySelected ? 'mixed' : allSelected },
                    }}
                    onChange={(_event, checked) => setDamageSource(checked ? 'all' : [])}
                  />
                }
              />
              {hazards.map((hazard) => (
                <FormControlLabel
                  key={hazard}
                  label={HAZARDS_METADATA[hazard]?.label ?? hazard}
                  disabled={HAZARDS_METADATA[hazard]?.has_access === false}
                  control={
                    <Checkbox
                      checked={selectedHazards.includes(hazard)}
                      onChange={(_event, checked) => {
                        const next = hazards.filter((candidate) =>
                          candidate === hazard ? checked : selectedHazards.includes(candidate),
                        );
                        setDamageSource(next.length === hazards.length ? 'all' : next);
                      }}
                    />
                  }
                />
              ))}
            </FormGroup>
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
        </InputSection>
      </LayerStylePanel>
    </>
  );
};
