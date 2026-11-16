import { FC } from 'react';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import startCase from 'lodash/startCase';
import lowerCase from 'lodash/lowerCase';
import { FormLabel, Slider, Typography } from '@mui/material';
import { Box } from '@mui/system';

import { CustomNumberSlider } from 'lib/controls/CustomSlider';
import { ParamDropdown } from 'lib/controls/ParamDropdown';
import { StateEffectRoot } from 'lib/recoil/state-effects/StateEffectRoot';

import { InputRow } from 'lib/sidebar/ui/InputRow';
import { InputSection } from 'lib/sidebar/ui/InputSection';
import { LayerStylePanel } from 'lib/sidebar/ui/LayerStylePanel';
import { DataParam } from 'lib/sidebar/ui/params/DataParam';
import { dataParamState } from 'lib/state/data-params';
import { modelParametersState } from 'lib/model-scenarios/state';
import { ModelParameterControls } from 'lib/model-scenarios/ModelParameterControls';

import {
  adaptationCostBenefitRatioEaelDaysState,
  adaptationDataParamsStateEffect,
  adaptationFieldState,
  adaptationLayerSpecState,
  adaptationScenarioState,
} from '../state/layer';

function hazardLabel(val) {
  switch (val) {
    case 'flooding':
      return 'Flooding';
    case 'TC':
      return 'Cyclones';
    default:
      return autoLabel(val);
  }
}

function autoLabel(x) {
  return startCase(lowerCase(x));
}

function makeOptions(values, labelFn = (x) => x) {
  return values.map((val) => ({
    value: val,
    label: labelFn(val),
  }));
}
const EAEL_DAYS_MARKS = [1, 5, 10, 15, 20, 25, 30].map((x) => ({ value: x, label: x }));
const CostBenefitRatioInputs: FC = () => {
  const [eaelDays, setEaelDays] = useAtom(adaptationCostBenefitRatioEaelDaysState);

  return (
    <Box mt={1}>
      <Typography>The cost-benefit ratio is calculated using the following formula:</Typography>
      <Typography>
        (Avoided Direct Damages + Avoided Economic Losses * No. of Days) / Adaptation Cost
      </Typography>
      <FormLabel htmlFor="adaptation-cost-benefit-eael-days">No. of Days</FormLabel>
      <Slider
        id="adaptation-cost-benefit-eael-days"
        value={eaelDays}
        onChange={(e, value: number) => setEaelDays(value)}
        min={1}
        max={30}
        step={1}
        marks={EAEL_DAYS_MARKS}
        valueLabelDisplay="auto"
      />
    </Box>
  );
};

export const AdaptationControl: FC = () => {
  const [adaptationField, setAdaptationField] = useAtom(adaptationFieldState);
  const { catalog, hazards, hazard, rows, names, optionRows, result } =
    useAtomValue(adaptationScenarioState);
  const setParameters = useSetAtom(modelParametersState('adaptation'));
  const setHazard = useSetAtom(dataParamState({ group: 'adaptation', param: 'hazard' }));
  const setName = useSetAtom(dataParamState({ group: 'adaptation', param: 'adaptation_name' }));
  const setLevel = useSetAtom(
    dataParamState({ group: 'adaptation', param: 'adaptation_protection_level' }),
  );
  const levels = optionRows.map((row) => row.adaptation_protection_level);
  return (
    <LayerStylePanel>
      <StateEffectRoot state={adaptationLayerSpecState} effect={adaptationDataParamsStateEffect} />
      <InputSection>
        <InputRow>
          <DataParam group="adaptation" id="sector">
            {({ value, onChange, options }) => (
              <ParamDropdown
                title="Sector"
                value={value}
                onChange={onChange}
                options={makeOptions(options, autoLabel)}
              />
            )}
          </DataParam>
          <DataParam group="adaptation" id="subsector">
            {({ value, onChange, options }) => (
              <ParamDropdown
                title="Sub-sector"
                value={value}
                onChange={onChange}
                options={makeOptions(options, autoLabel)}
              />
            )}
          </DataParam>
        </InputRow>
      </InputSection>
      <InputSection>
        <DataParam group="adaptation" id="asset_type">
          {({ value, onChange, options }) => (
            <ParamDropdown
              title="Asset type"
              value={value}
              onChange={onChange}
              options={makeOptions(options, autoLabel)}
            />
          )}
        </DataParam>
      </InputSection>
      <InputSection>
        <FormLabel>Adaptation for</FormLabel>
        <InputRow>
          <ParamDropdown
            title="Hazard"
            value={hazard ?? ''}
            onChange={setHazard}
            options={makeOptions(hazards, hazardLabel)}
          />
        </InputRow>
        <ModelParameterControls
          rows={catalog ? rows : undefined}
          parameters={result?.parameters ?? null}
          onChange={setParameters}
          error={catalog?.error}
        />
      </InputSection>
      <InputSection>
        <ParamDropdown
          title="Adaptation type"
          value={result?.adaptation_name ?? ''}
          onChange={setName}
          options={names}
        />
      </InputSection>
      <InputSection>
        {levels.length > 2 ? (
          <>
            <FormLabel>Protection level</FormLabel>
            <CustomNumberSlider
              title="Protection level"
              value={result?.adaptation_protection_level}
              onChange={setLevel}
              marks={levels}
            />
          </>
        ) : (
          <ParamDropdown
            title="Protection level"
            value={result?.adaptation_protection_level ?? ''}
            onChange={setLevel}
            options={levels}
          />
        )}
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
            { value: 'cost_benefit_ratio', label: 'Cost-Benefit Ratio' },
          ]}
        />
        {adaptationField === 'cost_benefit_ratio' ? <CostBenefitRatioInputs /> : null}
      </InputSection>
    </LayerStylePanel>
  );
};
