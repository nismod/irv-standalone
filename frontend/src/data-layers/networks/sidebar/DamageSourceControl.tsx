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
import { useAtom, useAtomValue } from 'jotai';

import { StateEffectRoot } from 'lib/recoil/state-effects/StateEffectRoot';
import { InputSection } from 'lib/sidebar/ui/InputSection';
import { InputRow } from 'lib/sidebar/ui/InputRow';
import { EpochControl } from 'lib/sidebar/ui/params/EpochControl';
import { RCPControl } from 'lib/sidebar/ui/params/RCPControl';
import { damageSourceState, damageTypeState } from 'lib/state/damage-map';
import { damageSourceStateEffect } from 'app/state/damage-mapping/damage-map';
import { LayerStylePanel } from 'lib/sidebar/ui/LayerStylePanel';

import { hazardsUIOrderState, hazardsMetadataState } from 'data-layers/hazards/state/metadata';

export const DamageSourceControl = () => {
  const HAZARDS_METADATA = useAtomValue(hazardsMetadataState);
  const hazardsUIOrder = useAtomValue(hazardsUIOrderState);
  const [damageSource, setDamageSource] = useAtom(damageSourceState);
  const [damageType, setDamageType] = useAtom(damageTypeState);
  const id = useId();

  useEffect(() => {
    if (
      damageSource !== 'all' &&
      Object.keys(HAZARDS_METADATA).length > 0 &&
      !HAZARDS_METADATA[damageSource]?.has_access
    ) {
      setDamageSource('all');
    }
  }, [damageSource, HAZARDS_METADATA, setDamageSource]);

  return (
    <>
      <StateEffectRoot state={damageSourceState} effect={damageSourceStateEffect} />
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
              {hazardsUIOrder
                .filter((h) => !!HAZARDS_METADATA[h] && h !== 'storm')
                .map((hazard) => (
                  <FormControlLabel
                    key={hazard}
                    label={HAZARDS_METADATA[hazard].label}
                    disabled={!HAZARDS_METADATA[hazard].has_access}
                    control={<Radio value={hazard} />}
                  />
                ))}
            </RadioGroup>
          </FormControl>
        </InputSection>
        <InputSection>
          <InputRow>
            <EpochControl group={damageSource} />
            <RCPControl group={damageSource} />
          </InputRow>
        </InputSection>
      </LayerStylePanel>
    </>
  );
};
