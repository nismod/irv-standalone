import { atom } from 'jotai';
import { atomFamily } from 'jotai-family';

import { StyleParams } from 'lib/data-map/view-layers';
import { damagesFieldState } from 'data-layers/networks/state/damage-scenarios';

import { damages, damagesCoastalDefence } from 'data-layers/networks/color-maps';

export const damageMapStyleParamsState = atomFamily((layerId: string) =>
  atom<StyleParams>((get) => {
    const eadFieldSpec = get(damagesFieldState);
    if (eadFieldSpec == null) return {};

    const colorSpec = layerId === 'coast_nodes_cpf' ? damagesCoastalDefence : damages;

    return {
      colorMap: {
        colorSpec: colorSpec,
        fieldSpec: eadFieldSpec,
      },
    };
  }),
);
