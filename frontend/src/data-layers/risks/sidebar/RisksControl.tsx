import {
  FormControl,
  FormControlLabel,
  FormLabel,
  MenuItem,
  Radio,
  RadioGroup,
  Select,
} from '@mui/material';
import { useEffect, useMemo } from 'react';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';

import { sectionStyleOptionsState, sectionStyleValueState } from 'lib/state/sections';

import { InputSection } from 'lib/sidebar/ui/InputSection';
import { DataParam } from 'lib/sidebar/ui/params/DataParam';

import { sectorRiskTypes } from 'app/config/sidebar/RISK_DOMAINS';
import { dataParamState } from 'lib/state/data-params';
import { riskIdsState, risksMetadataState } from '../state/metadata';

function capitalise(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

export const RisksControl = () => {
  const [riskType, setRiskType] = useAtom(sectionStyleValueState('risks'));
  const setRiskTypes = useSetAtom(sectionStyleOptionsState('risks'));
  const riskIds = useAtomValue(riskIdsState);
  const risksMetadata = useAtomValue(risksMetadataState);
  const sector = useAtomValue(dataParamState({ group: 'risks', param: 'sector' }));
  const riskTypes = useMemo(
    () => riskIds.map((id) => ({ id, label: risksMetadata[id].label })),
    [riskIds, risksMetadata],
  );

  useEffect(() => {
    setRiskTypes(riskTypes);
  }, [riskTypes, setRiskTypes]);

  // Reset risk type if the selected sector does not support the current risk type.
  const allowedRiskTypes = sectorRiskTypes[sector] || [];
  if (allowedRiskTypes.length > 0 && !allowedRiskTypes.includes(riskType)) {
    setRiskType(allowedRiskTypes[0]);
  }

  function onSelectRiskType(event, value) {
    setRiskType(value);
  }

  return (
    <>
      <InputSection>
        <FormControl fullWidth sx={{ my: 2 }}>
          <FormLabel id="risks-sector">Sector</FormLabel>
          <DataParam group="risks" id="sector">
            {({ value, onChange, options }) => (
              <Select
                labelId="risks-sector"
                value={value}
                onChange={(e) => onChange(e.target.value)}
              >
                {options.map((option) => (
                  <MenuItem key={option} value={option}>
                    {capitalise(option)}
                  </MenuItem>
                ))}
              </Select>
            )}
          </DataParam>
        </FormControl>
      </InputSection>
      <InputSection>
        <FormControl component="fieldset">
          <FormLabel component="legend">Variable</FormLabel>
          <RadioGroup value={riskType} onChange={onSelectRiskType}>
            {riskTypes
              .filter((option) => sectorRiskTypes[sector]?.includes(option.id))
              .map((option) => (
                <FormControlLabel
                  key={option.id}
                  label={option.label}
                  control={<Radio value={option.id} />}
                />
              ))}
          </RadioGroup>
        </FormControl>
      </InputSection>
    </>
  );
};
