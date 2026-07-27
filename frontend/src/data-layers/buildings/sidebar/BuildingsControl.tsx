import { useAtom, useAtomValue } from 'jotai';

import { networksMetadataState } from 'data-layers/networks/state/metadata';
import { ParamChecklist } from 'lib/controls/params/ParamChecklist';
import { LayerLabel } from 'lib/sidebar/ui/LayerLabel';

import { buildingSelectionState } from '../state/data-selection';

export const BuildingsControl = () => {
  const networksMetadata = useAtomValue(networksMetadataState);
  const [checkboxState, setCheckboxState] = useAtom(buildingSelectionState);

  return (
    <ParamChecklist
      title="Building types"
      options={Object.keys(checkboxState)}
      checklistState={checkboxState}
      onChecklistState={setCheckboxState}
      renderLabel={(key) => {
        const layerMetadata = networksMetadata[key];
        return layerMetadata ? (
          <LayerLabel {...layerMetadata} visible={checkboxState[key]} />
        ) : (
          <>{key}</>
        );
      }}
    />
  );
};
