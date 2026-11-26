import { useAtom, useAtomValue } from 'jotai';

import { networksMetadataState } from 'data-layers/networks/state/metadata';
import { ParamChecklist } from 'lib/controls/params/ParamChecklist';
import { LayerLabel } from 'lib/sidebar/ui/LayerLabel';

import { buildingLayerIdsState, buildingSelectionState } from '../state/data-selection';

export const BuildingsControl = () => {
  const layerIds = useAtomValue(buildingLayerIdsState);
  const networksMetadata = useAtomValue(networksMetadataState);
  const [checkboxState, setCheckboxState] = useAtom(buildingSelectionState);

  return (
    <ParamChecklist
      title="Building types"
      options={layerIds}
      checklistState={Object.fromEntries(layerIds.map((id) => [id, checkboxState[id] ?? true]))}
      onChecklistState={(state) => setCheckboxState({ ...checkboxState, ...state })}
      renderLabel={(key) => {
        const metadata = networksMetadata[key];
        return metadata ? (
          <LayerLabel {...metadata} visible={checkboxState[key] ?? true} />
        ) : (
          <>{key}</>
        );
      }}
    />
  );
};
