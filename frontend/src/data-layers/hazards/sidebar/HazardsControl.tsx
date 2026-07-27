import { ToggleSection, ToggleSectionGroup } from 'lib/controls/accordion-toggle/ToggleSection';

import { InputRow } from 'lib/sidebar/ui/InputRow';
import { InputSection } from 'lib/sidebar/ui/InputSection';
import { ReturnPeriodControl } from 'lib/sidebar/ui/params/ReturnPeriodControl';
import { EpochControl } from 'lib/sidebar/ui/params/EpochControl';
import { RCPControl } from 'lib/sidebar/ui/params/RCPControl';
import { useAtomValue } from 'jotai';
import { showDamagesState } from 'app/state/damage-mapping/damage-map';
import { Alert, Box, FormControl, FormLabel, MenuItem, Select } from '@mui/material';

import { hazardSelectionState } from '../state/data-selection';
import { hazardsUIOrderState, hazardsMetadataState } from '../state/metadata';
import { CustomNumberSlider } from 'lib/controls/CustomSlider';
import { DataParam } from 'lib/sidebar/ui/params/DataParam';
import { dataParamConfigState } from 'lib/state/data-params';
import { titleCase } from 'lib/helpers';

/* Lower bound of NOAA storm categories, in m/s.
  https://www.nhc.noaa.gov/aboutsshws.php
*/
const STORM_CATEGORIES = {
  1: 33,
  2: 43,
  3: 50,
  4: 58,
  5: 70,
};

function SpeedSlider({ value, onChange, options }) {
  const [category] = Object.entries(STORM_CATEGORIES).findLast(([, speed]) => value >= speed) || [];
  const categoryLabel = category ? `Category ${category}` : '';
  return (
    <CustomNumberSlider
      marks={options}
      value={value}
      onChange={onChange}
      scale={(x) => options[x]}
      showMarkLabelsFor={[20, 30, 40, 50, 60, 70]}
      valueLabelDisplay="auto"
      valueLabelFormat={(v) => `${v} ${categoryLabel}`}
    />
  );
}

const PARAM_LABELS: Record<string, string> = {
  rcp: 'RCP',
  GWL: 'Global Warming Level',
  SLR: 'Sea Level Rise',
  RP: 'Return Period',
  returnPeriod: 'Return Period',
};

const PARAM_ORDER = ['speed', 'returnPeriod', 'RP', 'GWL', 'epoch', 'rcp', 'confidence'];

function getParamLabel(param: string) {
  return PARAM_LABELS[param] ?? titleCase(param.replace(/_/g, ' '));
}

function getSortedParams(paramNames: string[]) {
  return [...paramNames].sort((a, b) => {
    const aIndex = PARAM_ORDER.indexOf(a);
    const bIndex = PARAM_ORDER.indexOf(b);
    if (aIndex === -1 && bIndex === -1) {
      return a.localeCompare(b);
    }
    if (aIndex === -1) {
      return 1;
    }
    if (bIndex === -1) {
      return -1;
    }
    return aIndex - bIndex;
  });
}

function chunkParams<T>(params: T[], size: number) {
  const chunks: T[][] = [];
  for (let i = 0; i < params.length; i += size) {
    chunks.push(params.slice(i, i + size));
  }
  return chunks;
}

function isNumericParam(param: string, groupConfig) {
  const options = groupConfig?.paramDomains?.[param];
  return Array.isArray(options) && options.every((option) => typeof option === 'number');
}

function GenericSelectControl({ labelId, param, value, onChange, options, disabled = false }) {
  return (
    <FormControl fullWidth disabled={disabled}>
      <FormLabel id={labelId}>{getParamLabel(param)}</FormLabel>
      <Select
        labelId={labelId}
        variant="standard"
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        fullWidth
      >
        {options.map((option) => (
          <MenuItem key={String(option)} value={option}>
            {String(option) === 'baseline' ? 'Baseline' : String(option)}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

function GenericNumberControl({ labelId, param, value, onChange, options, disabled = false }) {
  return (
    <FormControl fullWidth disabled={disabled}>
      <FormLabel id={labelId}>{getParamLabel(param)}</FormLabel>
      <CustomNumberSlider
        marks={options}
        value={value}
        onChange={onChange}
        valueLabelDisplay="auto"
        disabled={disabled}
      />
    </FormControl>
  );
}

function HazardParamControl({ group, param, disabled = false, hazard }) {
  if (param === 'speed') {
    return (
      <FormControl fullWidth disabled={disabled}>
        <FormLabel id="storm-speed">Storm speed (m/s)</FormLabel>
        <DataParam group={group} id="speed">
          {({ value, onChange, options }) => (
            <SpeedSlider value={value} onChange={onChange} options={options} />
          )}
        </DataParam>
      </FormControl>
    );
  }

  if (param === 'returnPeriod') {
    const otherProps =
      hazard === 'cyclone'
        ? {
            showMarkLabelsFor: [10, 50, 100, 500, 1000, 5000, 10000],
            valueLabelDisplay: 'auto',
          }
        : {};

    return <ReturnPeriodControl group={group} param="returnPeriod" disabled={disabled} {...otherProps} />;
  }

  if (param === 'epoch') {
    return <EpochControl group={group} disabled={disabled} />;
  }

  if (param === 'rcp') {
    return <RCPControl group={group} disabled={disabled} />;
  }

  return (
    <DataParam group={group} id={param}>
      {({ value, onChange, options }) => {
        const labelId = `${group}-${param}`;
        return options.every((option) => typeof option === 'number') ? (
          <GenericNumberControl
            labelId={labelId}
            param={param}
            value={value}
            onChange={onChange}
            options={options}
            disabled={disabled}
          />
        ) : (
          <GenericSelectControl
            labelId={labelId}
            param={param}
            value={value}
            onChange={onChange}
            options={options}
            disabled={disabled}
          />
        );
      }}
    </DataParam>
  );
}

function HazardToggleSection({ hazard, disabled }) {
  const hazardsMetadata = useAtomValue(hazardsMetadataState);
  const dataParamConfig = useAtomValue(dataParamConfigState);
  const catalogueEntry = hazardsMetadata[hazard];
  if (!catalogueEntry) {
    return null;
  }
  const groupConfig = dataParamConfig[hazard];
  const paramNames = groupConfig ? getSortedParams(Object.keys(groupConfig.paramDefaults)) : [];
  const sliderParams = paramNames.filter((param) => isNumericParam(param, groupConfig));
  const selectParams = paramNames.filter((param) => !isNumericParam(param, groupConfig));
  const permissionDenied = !catalogueEntry.has_access;

  return (
    <ToggleSection
      id={hazard}
      label={catalogueEntry.label}
      disabled={disabled || permissionDenied}
    >
      {sliderParams.map((param) => (
        <InputSection key={param}>
          <HazardParamControl
            group={hazard}
            hazard={hazard}
            param={param}
            disabled={disabled || permissionDenied}
          />
        </InputSection>
      ))}
      {chunkParams(selectParams, 2).map((paramGroup) => (
        <InputSection key={paramGroup.join('-')}>
          <InputRow>
            {paramGroup.map((param) => (
              <HazardParamControl
                key={param}
                group={hazard}
                hazard={hazard}
                param={param}
                disabled={disabled || permissionDenied}
              />
            ))}
          </InputRow>
        </InputSection>
      ))}
    </ToggleSection>
  );
}

export const HazardsControl = () => {
  const showDirectDamages = useAtomValue(showDamagesState);
  const hazardsUIOrder = useAtomValue(hazardsUIOrderState);
  const disabled = showDirectDamages;

  return (
    <>
      {showDirectDamages ? (
        <Box my={1}>
          <Alert severity="info">
            Hazards are currently following the Infrastructure &gt; Damages selection
          </Alert>
        </Box>
      ) : null}
      <ToggleSectionGroup toggleState={hazardSelectionState}>
        {hazardsUIOrder.map((hazard) => (
          <HazardToggleSection key={hazard} hazard={hazard} disabled={disabled} />
        ))}
      </ToggleSectionGroup>
    </>
  );
};
