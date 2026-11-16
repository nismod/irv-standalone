import { FC } from 'react';
import { useAtom } from 'jotai';
import { FormLabel } from '@mui/material';

import { ParamDropdown } from 'lib/controls/ParamDropdown';

import { InputSection } from 'lib/sidebar/ui/InputSection';
import { LayerStylePanel } from 'lib/sidebar/ui/LayerStylePanel';
import { ProtectedScenarioControls } from './ProtectedScenarioControls';

import { adaptationFieldState } from '../state/layer';

export const ProtectedFeaturesControl: FC = () => {
  const [adaptationField, setAdaptationField] = useAtom(adaptationFieldState);
  return (
    <LayerStylePanel>
      <InputSection>
        <FormLabel>Adaptation for</FormLabel>
        <ProtectedScenarioControls />
      </InputSection>
      <InputSection>
        <ParamDropdown<typeof adaptationField>
          title="Displayed variable"
          value={adaptationField}
          onChange={setAdaptationField}
          options={[
            { value: 'avoided_ead_mean', label: 'Avoided Expected Annual Damages' },
            { value: 'avoided_eael_mean', label: 'Avoided Expected Annual Economic Losses' },
            { value: 'adaptation_cost', label: 'Adaptation Cost' },
          ]}
        />
      </InputSection>
    </LayerStylePanel>
  );
};
